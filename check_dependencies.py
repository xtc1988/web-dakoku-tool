#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
依存ライブラリの安全性チェックスクリプト
Web打刻ツールで使用しているライブラリの安全性を確認します。
"""

import os
import sys
import json
import subprocess
import platform
import logging
import requests
import time
from pathlib import Path
from datetime import datetime

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("security_check.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 安全性チェックに使用するAPIのURL
PYPI_URL = "https://pypi.org/pypi/{package}/json"
SAFETY_DB_URL = "https://raw.githubusercontent.com/pyupio/safety-db/master/data/insecure_full.json"
SNYK_API_URL = "https://snyk.io/api/v1/vuln/pip/{package}"

def get_installed_packages():
    """インストール済みのパッケージとそのバージョンを取得"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==', 1)
                packages[name.lower()] = version
        
        logger.info(f"{len(packages)}個のパッケージがインストールされています")
        return packages
    except subprocess.SubprocessError as e:
        logger.error(f"パッケージ情報の取得に失敗しました: {e}")
        return {}

def get_project_dependencies():
    """プロジェクトの依存関係を取得"""
    try:
        requirements_path = "requirements.txt"
        if not os.path.exists(requirements_path):
            logger.warning(f"{requirements_path}が見つかりません")
            return {}
            
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        dependencies = {}
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # バージョン指定がある場合
            if '==' in line:
                name, version = line.split('==', 1)
                dependencies[name.lower()] = version
            else:
                # バージョン指定がない場合は空文字列を設定
                dependencies[line.lower()] = ""
                
        logger.info(f"{len(dependencies)}個の依存パッケージが定義されています")
        return dependencies
    except Exception as e:
        logger.error(f"依存関係の取得に失敗しました: {e}")
        return {}

def check_package_info(package_name, version):
    """PyPIからパッケージ情報を取得"""
    try:
        url = PYPI_URL.format(package=package_name)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # パッケージ情報
            info = data.get('info', {})
            author = info.get('author', 'Unknown')
            author_email = info.get('author_email', 'Unknown')
            home_page = info.get('home_page', 'Unknown')
            project_url = info.get('project_url', 'Unknown')
            
            # ダウンロード数
            if 'releases' in data and version in data['releases']:
                release_info = data['releases'][version]
                download_count = sum(item.get('downloads', 0) for item in release_info)
            else:
                download_count = "Unknown"
                
            # 最終更新日
            last_updated = "Unknown"
            if 'releases' in data and version in data['releases']:
                release_info = data['releases'][version]
                if release_info and 'upload_time' in release_info[0]:
                    last_updated = release_info[0]['upload_time']
                    
            return {
                "name": package_name,
                "version": version,
                "author": author,
                "author_email": author_email,
                "home_page": home_page,
                "project_url": project_url,
                "download_count": download_count,
                "last_updated": last_updated
            }
        else:
            logger.warning(f"{package_name}の情報取得に失敗しました: ステータスコード {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"{package_name}の情報取得中にエラーが発生しました: {e}")
        return None

def get_safety_db():
    """Safety DBから脆弱性情報を取得"""
    try:
        response = requests.get(SAFETY_DB_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Safety DBの取得に失敗しました: ステータスコード {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Safety DBの取得中にエラーが発生しました: {e}")
        return {}

def check_package_vulnerabilities(package_name, version, safety_db):
    """パッケージの脆弱性をチェック"""
    vulnerabilities = []
    
    # Safety DBでのチェック
    if package_name in safety_db:
        for vuln in safety_db[package_name]:
            affected_versions = vuln.get('specs', [])
            # バージョンチェック（簡易的な実装）
            is_vulnerable = False
            for spec in affected_versions:
                if spec[0] == '==' and spec[1] == version:
                    is_vulnerable = True
                    break
                elif spec[0] == '>=' and version >= spec[1]:
                    is_vulnerable = True
                    break
                elif spec[0] == '<=' and version <= spec[1]:
                    is_vulnerable = True
                    break
                    
            if is_vulnerable:
                vulnerabilities.append({
                    "source": "Safety DB",
                    "id": vuln.get('id', 'Unknown'),
                    "description": vuln.get('advisory', 'No description available')
                })
    
    # PyPI Advisoryでのチェック（簡易的な実装）
    try:
        url = f"https://pypi.org/project/{package_name}/{version}/"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text.lower()
            if 'security' in content and ('vulnerability' in content or 'advisory' in content):
                vulnerabilities.append({
                    "source": "PyPI Advisory",
                    "id": "N/A",
                    "description": "Potential security advisory found on PyPI page. Please check manually."
                })
    except Exception:
        pass
        
    return vulnerabilities

def check_package_popularity(package_name):
    """パッケージの人気度をチェック"""
    try:
        url = f"https://pypistats.org/api/packages/{package_name}/recent"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            downloads = data.get('data', {}).get('last_month', 0)
            return downloads
        else:
            return None
    except Exception:
        return None

def check_suspicious_packages(packages):
    """怪しいパッケージをチェック"""
    suspicious = []
    
    # 既知の悪意のあるパッケージのリスト（例）
    known_malicious = [
        "colourama",  # typosquatting (colorama)
        "jeIlyfish",  # typosquatting (jellyfish)
        "python-dateutil-2",  # typosquatting (python-dateutil)
        "crypt",  # typosquatting (cryptography)
        "request",  # typosquatting (requests)
        "urlib3",  # typosquatting (urllib3)
        "bs4-requests",  # suspicious combination
        "telnet-client",  # suspicious name
        "crypto-utils",  # suspicious name
        "setup-tools",  # typosquatting (setuptools)
        "pip-tools-1",  # typosquatting (pip-tools)
        "django-server",  # suspicious name
        "flask-login-1",  # typosquatting (flask-login)
        "tensorflow-gpu-1",  # typosquatting (tensorflow-gpu)
        "torch-utils",  # suspicious name
        "numpy-1",  # typosquatting (numpy)
        "pandas-1",  # typosquatting (pandas)
        "scikit-learn-1",  # typosquatting (scikit-learn)
        "matplotlib-1",  # typosquatting (matplotlib)
        "selenium-driver",  # suspicious name
        "webdriver-manager-1",  # typosquatting (webdriver-manager)
        "pyside-6",  # typosquatting (pyside6)
        "cryptography-1",  # typosquatting (cryptography)
        "pillow-1",  # typosquatting (pillow)
    ]
    
    for package in packages:
        # 既知の悪意のあるパッケージかチェック
        if package.lower() in known_malicious:
            suspicious.append({
                "name": package,
                "reason": "既知の悪意のあるパッケージ名と一致します"
            })
            continue
            
        # typosquattingの可能性をチェック
        common_packages = [
            "requests", "urllib3", "numpy", "pandas", "matplotlib", 
            "django", "flask", "tensorflow", "torch", "scikit-learn",
            "selenium", "beautifulsoup4", "cryptography", "pillow", "pyside6"
        ]
        
        for common in common_packages:
            # 編集距離が1または2の場合（簡易的な実装）
            if package.lower() != common.lower() and (
                package.lower().replace('-', '') == common.lower().replace('-', '') or
                package.lower().replace('_', '') == common.lower().replace('_', '') or
                package.lower() + '1' == common.lower() or
                package.lower() + '-1' == common.lower() or
                package.lower() + '_1' == common.lower()
            ):
                suspicious.append({
                    "name": package,
                    "reason": f"人気のパッケージ '{common}' に似た名前です (typosquatting)"
                })
                break
    
    return suspicious

def generate_report(packages, project_deps, safety_db):
    """セキュリティレポートを生成"""
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": platform.python_version(),
        "os": platform.system(),
        "packages": [],
        "suspicious_packages": [],
        "vulnerable_packages": [],
        "summary": {
            "total_packages": len(packages),
            "suspicious_count": 0,
            "vulnerable_count": 0,
            "low_popularity_count": 0
        }
    }
    
    # 怪しいパッケージのチェック
    suspicious = check_suspicious_packages(packages.keys())
    report["suspicious_packages"] = suspicious
    report["summary"]["suspicious_count"] = len(suspicious)
    
    # 各パッケージの詳細情報を取得
    for i, (name, version) in enumerate(packages.items()):
        logger.info(f"パッケージをチェック中 ({i+1}/{len(packages)}): {name}=={version}")
        
        # パッケージ情報の取得
        info = check_package_info(name, version)
        if not info:
            info = {
                "name": name,
                "version": version,
                "author": "Unknown",
                "author_email": "Unknown",
                "home_page": "Unknown",
                "project_url": "Unknown",
                "download_count": "Unknown",
                "last_updated": "Unknown"
            }
            
        # 脆弱性のチェック
        vulnerabilities = check_package_vulnerabilities(name, version, safety_db)
        if vulnerabilities:
            report["vulnerable_packages"].append({
                "name": name,
                "version": version,
                "vulnerabilities": vulnerabilities
            })
            report["summary"]["vulnerable_count"] += 1
            
        # 人気度のチェック
        popularity = check_package_popularity(name)
        if popularity is not None and popularity < 1000:
            info["low_popularity"] = True
            report["summary"]["low_popularity_count"] += 1
        else:
            info["low_popularity"] = False
            
        # プロジェクトの依存関係かどうか
        info["is_project_dependency"] = name in project_deps
        
        report["packages"].append(info)
        
        # APIレート制限を避けるための遅延
        time.sleep(0.5)
        
    return report

def save_report(report, filename="security_report.json"):
    """レポートをJSONファイルとして保存"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"レポートを保存しました: {filename}")
        return True
    except Exception as e:
        logger.error(f"レポートの保存に失敗しました: {e}")
        return False

def generate_html_report(report, filename="security_report.html"):
    """HTMLレポートを生成"""
    try:
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web打刻ツール - セキュリティレポート</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .summary {{
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .warning {{
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        .danger {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        .info {{
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 7px;
            font-size: 12px;
            font-weight: 700;
            line-height: 1;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 10px;
            margin-right: 5px;
        }}
        .badge-warning {{
            background-color: #ffc107;
            color: #212529;
        }}
        .badge-danger {{
            background-color: #dc3545;
            color: white;
        }}
        .badge-info {{
            background-color: #17a2b8;
            color: white;
        }}
        .badge-success {{
            background-color: #28a745;
            color: white;
        }}
    </style>
</head>
<body>
    <h1>Web打刻ツール - セキュリティレポート</h1>
    <p>生成日時: {report['timestamp']}</p>
    <p>Python バージョン: {report['python_version']}</p>
    <p>OS: {report['os']}</p>
    
    <div class="summary">
        <h2>サマリー</h2>
        <p>合計パッケージ数: {report['summary']['total_packages']}</p>
        <p>怪しいパッケージ: {report['summary']['suspicious_count']}</p>
        <p>脆弱性のあるパッケージ: {report['summary']['vulnerable_count']}</p>
        <p>人気度の低いパッケージ: {report['summary']['low_popularity_count']}</p>
    </div>
"""

        # 怪しいパッケージがある場合
        if report['suspicious_packages']:
            html += """
    <h2>怪しいパッケージ</h2>
    <div class="danger">
        <p>以下のパッケージは悪意のあるパッケージである可能性があります。慎重に確認してください。</p>
    </div>
    <table>
        <tr>
            <th>パッケージ名</th>
            <th>理由</th>
        </tr>
"""
            for package in report['suspicious_packages']:
                html += f"""
        <tr>
            <td>{package['name']}</td>
            <td>{package['reason']}</td>
        </tr>
"""
            html += """
    </table>
"""

        # 脆弱性のあるパッケージがある場合
        if report['vulnerable_packages']:
            html += """
    <h2>脆弱性のあるパッケージ</h2>
    <div class="warning">
        <p>以下のパッケージには既知の脆弱性があります。アップデートを検討してください。</p>
    </div>
    <table>
        <tr>
            <th>パッケージ名</th>
            <th>バージョン</th>
            <th>脆弱性</th>
        </tr>
"""
            for package in report['vulnerable_packages']:
                vulns = "<br>".join([f"{v['source']}: {v['description']}" for v in package['vulnerabilities']])
                html += f"""
        <tr>
            <td>{package['name']}</td>
            <td>{package['version']}</td>
            <td>{vulns}</td>
        </tr>
"""
            html += """
    </table>
"""

        # すべてのパッケージ
        html += """
    <h2>すべてのパッケージ</h2>
    <table>
        <tr>
            <th>パッケージ名</th>
            <th>バージョン</th>
            <th>作者</th>
            <th>最終更新日</th>
            <th>ステータス</th>
        </tr>
"""
        for package in report['packages']:
            badges = ""
            if package.get('is_project_dependency', False):
                badges += '<span class="badge badge-info">プロジェクト依存</span>'
            if package.get('low_popularity', False):
                badges += '<span class="badge badge-warning">低人気度</span>'
                
            # 脆弱性があるかチェック
            has_vulnerability = False
            for vuln_package in report['vulnerable_packages']:
                if vuln_package['name'] == package['name']:
                    has_vulnerability = True
                    badges += '<span class="badge badge-danger">脆弱性あり</span>'
                    break
                    
            # 怪しいパッケージかチェック
            is_suspicious = False
            for susp_package in report['suspicious_packages']:
                if susp_package['name'] == package['name']:
                    is_suspicious = True
                    badges += '<span class="badge badge-danger">怪しい</span>'
                    break
                    
            if not has_vulnerability and not is_suspicious and not package.get('low_popularity', False):
                badges += '<span class="badge badge-success">問題なし</span>'
                
            html += f"""
        <tr>
            <td>{package['name']}</td>
            <td>{package['version']}</td>
            <td>{package['author']}</td>
            <td>{package['last_updated']}</td>
            <td>{badges}</td>
        </tr>
"""
        html += """
    </table>
    
    <h2>推奨事項</h2>
"""

        # 推奨事項
        if report['suspicious_packages']:
            html += """
    <div class="danger">
        <h3>怪しいパッケージの対応</h3>
        <p>怪しいパッケージが検出されました。以下の対応を検討してください：</p>
        <ul>
            <li>パッケージの公式サイトやGitHubリポジトリを確認し、正規のパッケージであることを確認する</li>
            <li>正規のパッケージに置き換える</li>
            <li>必要ない場合はアンインストールする</li>
        </ul>
    </div>
"""

        if report['vulnerable_packages']:
            html += """
    <div class="warning">
        <h3>脆弱性のあるパッケージの対応</h3>
        <p>脆弱性のあるパッケージが検出されました。以下の対応を検討してください：</p>
        <ul>
            <li>最新バージョンにアップデートする</li>
            <li>脆弱性が修正されたバージョンに指定する</li>
            <li>代替パッケージを使用する</li>
        </ul>
    </div>
"""

        if report['summary']['low_popularity_count'] > 0:
            html += """
    <div class="info">
        <h3>人気度の低いパッケージの対応</h3>
        <p>人気度の低いパッケージが検出されました。以下の対応を検討してください：</p>
        <ul>
            <li>パッケージの信頼性を確認する</li>
            <li>より人気のある代替パッケージを検討する</li>
            <li>必要性を再検討する</li>
        </ul>
    </div>
"""

        html += """
    <div class="info">
        <h3>一般的な推奨事項</h3>
        <ul>
            <li>定期的にパッケージをアップデートする</li>
            <li>requirements.txtでバージョンを固定する</li>
            <li>仮想環境を使用して依存関係を分離する</li>
            <li>信頼できるソースからのみパッケージをインストールする</li>
        </ul>
    </div>
    
    <footer>
        <p>このレポートは自動生成されたものです。詳細な分析には専門家の判断が必要です。</p>
    </footer>
</body>
</html>
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"HTMLレポートを保存しました: {filename}")
        return True
    except Exception as e:
        logger.error(f"HTMLレポートの生成に失敗しました: {e}")
        return False

def main():
    """メイン処理"""
    logger.info("依存ライブラリの安全性チェックを開始します")
    
    # インストール済みのパッケージを取得
    packages = get_installed_packages()
    if not packages:
        logger.error("インストール済みのパッケージを取得できませんでした")
        return False
        
    # プロジェクトの依存関係を取得
    project_deps = get_project_dependencies()
    
    # Safety DBを取得
    logger.info("脆弱性データベースを取得しています...")
    safety_db = get_safety_db()
    
    # レポートを生成
    logger.info("セキュリティレポートを生成しています...")
    report = generate_report(packages, project_deps, safety_db)
    
    # レポートを保存
    save_report(report)
    
    # HTMLレポートを生成
    generate_html_report(report)
    
    # 結果を表示
    print("\nセキュリティチェックが完了しました！")
    print(f"合計パッケージ数: {report['summary']['total_packages']}")
    print(f"怪しいパッケージ: {report['summary']['suspicious_count']}")
    print(f"脆弱性のあるパッケージ: {report['summary']['vulnerable_count']}")
    print(f"人気度の低いパッケージ: {report['summary']['low_popularity_count']}")
    print("\nレポートは以下のファイルに保存されました:")
    print("- security_report.json")
    print("- security_report.html")
    
    # 怪しいパッケージがある場合
    if report['suspicious_packages']:
        print("\n警告: 怪しいパッケージが検出されました！")
        for package in report['suspicious_packages']:
            print(f"- {package['name']}: {package['reason']}")
            
    # 脆弱性のあるパッケージがある場合
    if report['vulnerable_packages']:
        print("\n警告: 脆弱性のあるパッケージが検出されました！")
        for package in report['vulnerable_packages']:
            print(f"- {package['name']} {package['version']}")
            for vuln in package['vulnerabilities']:
                print(f"  - {vuln['source']}: {vuln['description']}")
                
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.exception(f"予期せぬエラーが発生しました: {e}")
        print(f"エラーが発生しました: {e}")
        print("詳細はsecurity_check.logを確認してください。")
        sys.exit(1) 