#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web打刻ツール - 初心者向けセットアップスクリプト
Seleniumを全く使ったことがない方でも簡単にセットアップできるようにするためのスクリプトです。
"""

import os
import sys
import time
import subprocess
import platform
import logging
import shutil
import webbrowser
from pathlib import Path

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("beginner_setup.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def print_header(title):
    """ヘッダーを表示"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

def print_step(step_num, description):
    """ステップを表示"""
    print(f"\n[ステップ {step_num}] {description}")
    print("-" * 60)

def check_python_version():
    """Pythonのバージョンを確認"""
    print_step(1, "Pythonのバージョンを確認しています...")
    
    major, minor = sys.version_info[:2]
    version = f"{major}.{minor}.{sys.version_info[2]}"
    
    print(f"Pythonバージョン: {version}")
    
    if major < 3 or (major == 3 and minor < 8):
        print("❌ Python 3.8以上が必要です。")
        print("   Python公式サイトから最新バージョンをインストールしてください:")
        print("   https://www.python.org/downloads/")
        return False
    
    print("✅ Pythonのバージョンは要件を満たしています。")
    return True

def check_pip():
    """pipがインストールされているか確認"""
    print_step(2, "pipの状態を確認しています...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("✅ pipが正常にインストールされています。")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ pipがインストールされていないか、正常に動作していません。")
        print("   Pythonを再インストールするか、以下のコマンドでpipをインストールしてください:")
        print("   python -m ensurepip --upgrade")
        return False

def check_chrome():
    """Google Chromeがインストールされているか確認"""
    print_step(3, "Google Chromeを確認しています...")
    
    system = platform.system()
    chrome_found = False
    chrome_path = None
    
    if system == "Windows":
        chrome_paths = [
            os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google\\Chrome\\Application\\chrome.exe")
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_found = True
                chrome_path = path
                break
    
    elif system == "Darwin":  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            chrome_found = True
    
    elif system == "Linux":
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_found = True
                chrome_path = path
                break
    
    if chrome_found:
        print(f"✅ Google Chromeが見つかりました: {chrome_path}")
        return True
    else:
        print("❌ Google Chromeが見つかりませんでした。")
        print("   Web打刻ツールを使用するには、Google Chromeが必要です。")
        print("   以下のリンクからダウンロードしてインストールしてください:")
        print("   https://www.google.com/chrome/")
        
        # Chromeのダウンロードページを開く
        try:
            webbrowser.open("https://www.google.com/chrome/")
            print("   Chromeのダウンロードページを開きました。")
        except:
            pass
            
        return False

def install_dependencies():
    """必要なパッケージをインストール"""
    print_step(4, "必要なパッケージをインストールしています...")
    
    # requirements.txtが存在するか確認
    requirements_path = os.path.join(os.getcwd(), "requirements.txt")
    if not os.path.exists(requirements_path):
        print("❌ requirements.txtが見つかりません。")
        print("   正しいディレクトリにいることを確認してください。")
        return False
    
    # パッケージのインストール
    try:
        print("パッケージのインストールを開始します...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("✅ 必要なパッケージのインストールが完了しました。")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ パッケージのインストールに失敗しました: {e}")
        print("   以下のコマンドを手動で実行してみてください:")
        print("   pip install -r requirements.txt")
        return False

def setup_selenium():
    """Seleniumの初期設定"""
    print_step(5, "Seleniumの初期設定を行っています...")
    
    try:
        # Seleniumのインポートテスト
        print("Seleniumのインポートをテストしています...")
        import_cmd = (
            "try:\n"
            "    from selenium import webdriver\n"
            "    from selenium.webdriver.chrome.service import Service\n"
            "    from selenium.webdriver.chrome.options import Options\n"
            "    from webdriver_manager.chrome import ChromeDriverManager\n"
            "    print('Seleniumのインポートに成功しました')\n"
            "except ImportError as e:\n"
            "    print(f'Seleniumのインポートに失敗しました: {e}')\n"
            "    exit(1)\n"
        )
        
        result = subprocess.run(
            [sys.executable, "-c", import_cmd],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Seleniumのインポートに失敗しました。")
            print("   以下のコマンドを手動で実行してみてください:")
            print("   pip install selenium webdriver-manager")
            return False
        
        print(result.stdout.strip())
        
        # ChromeDriverのダウンロードテスト
        print("\nChromeDriverのダウンロードをテストしています...")
        driver_cmd = (
            "try:\n"
            "    from selenium import webdriver\n"
            "    from selenium.webdriver.chrome.service import Service\n"
            "    from selenium.webdriver.chrome.options import Options\n"
            "    from webdriver_manager.chrome import ChromeDriverManager\n"
            "    \n"
            "    options = Options()\n"
            "    options.add_argument('--headless=new')\n"
            "    options.add_argument('--no-sandbox')\n"
            "    options.add_argument('--disable-dev-shm-usage')\n"
            "    \n"
            "    service = Service(ChromeDriverManager().install())\n"
            "    driver = webdriver.Chrome(service=service, options=options)\n"
            "    print('ChromeDriverのセットアップに成功しました')\n"
            "    driver.quit()\n"
            "except Exception as e:\n"
            "    print(f'ChromeDriverのセットアップに失敗しました: {e}')\n"
            "    exit(1)\n"
        )
        
        result = subprocess.run(
            [sys.executable, "-c", driver_cmd],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print("❌ ChromeDriverのセットアップに失敗しました。")
            print("   詳細なエラーメッセージ:")
            print(result.stdout.strip())
            print(result.stderr.strip())
            print("\n   以下の点を確認してください:")
            print("   - インターネット接続が正常か")
            print("   - Google Chromeが最新バージョンか")
            print("   - ファイアウォールがダウンロードをブロックしていないか")
            return False
        
        print(result.stdout.strip())
        print("✅ Seleniumの初期設定が完了しました。")
        return True
    except Exception as e:
        print(f"❌ Seleniumの初期設定中にエラーが発生しました: {e}")
        return False

def create_test_script():
    """Seleniumのテスト用スクリプトを作成"""
    print_step(6, "テスト用スクリプトを作成しています...")
    
    test_script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Seleniumの動作確認用スクリプト
\"\"\"

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def test_selenium():
    print("Seleniumの動作確認を開始します...")
    
    # スクリーンショット保存用のディレクトリを作成
    os.makedirs("screenshots", exist_ok=True)
    
    # ChromeDriverのセットアップ
    print("ChromeDriverをセットアップしています...")
    options = Options()
    options.add_argument("--headless=new")  # ヘッドレスモード
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Googleにアクセス
        print("Googleにアクセスしています...")
        driver.get("https://www.google.com")
        
        # タイトルを取得
        title = driver.title
        print(f"ページタイトル: {title}")
        
        # スクリーンショットを保存
        screenshot_path = os.path.join("screenshots", "selenium_test.png")
        driver.save_screenshot(screenshot_path)
        print(f"スクリーンショットを保存しました: {screenshot_path}")
        
        # ブラウザを閉じる
        driver.quit()
        
        print("テストが正常に完了しました！")
        return True
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = test_selenium()
    if not success:
        print("テストに失敗しました。")
        exit(1)
    else:
        print("テストに成功しました！Web打刻ツールを使用する準備が整いました。")
"""
    
    try:
        with open("test_selenium.py", "w", encoding="utf-8") as f:
            f.write(test_script)
        print("✅ テスト用スクリプトを作成しました: test_selenium.py")
        return True
    except Exception as e:
        print(f"❌ テスト用スクリプトの作成に失敗しました: {e}")
        return False

def run_test_script():
    """テスト用スクリプトを実行"""
    print_step(7, "テスト用スクリプトを実行しています...")
    
    try:
        result = subprocess.run(
            [sys.executable, "test_selenium.py"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print("❌ テストに失敗しました。")
            print("   エラーメッセージ:")
            print(result.stderr)
            return False
        
        # スクリーンショットが生成されたか確認
        screenshot_path = os.path.join("screenshots", "selenium_test.png")
        if os.path.exists(screenshot_path):
            print(f"✅ スクリーンショットが正常に生成されました: {screenshot_path}")
        else:
            print("❌ スクリーンショットが生成されませんでした。")
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return False

def create_startup_script():
    """起動用スクリプトを作成"""
    print_step(8, "起動用スクリプトを作成しています...")
    
    system = platform.system()
    
    if system == "Windows":
        # Windowsの場合はバッチファイルを作成
        batch_content = """@echo off
echo Web打刻ツールを起動しています...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo エラーが発生しました。
    echo ログファイルを確認してください。
    pause
    exit /b 1
)
"""
        try:
            with open("start_web_dakoku.bat", "w", encoding="utf-8") as f:
                f.write(batch_content)
            print("✅ 起動用バッチファイルを作成しました: start_web_dakoku.bat")
            return True
        except Exception as e:
            print(f"❌ 起動用バッチファイルの作成に失敗しました: {e}")
            return False
    else:
        # macOS/Linuxの場合はシェルスクリプトを作成
        shell_content = """#!/bin/bash
echo "Web打刻ツールを起動しています..."
python3 main.py
if [ $? -ne 0 ]; then
    echo "エラーが発生しました。"
    echo "ログファイルを確認してください。"
    read -p "Enterキーを押して終了..."
    exit 1
fi
"""
        try:
            with open("start_web_dakoku.sh", "w", encoding="utf-8") as f:
                f.write(shell_content)
            # 実行権限を付与
            os.chmod("start_web_dakoku.sh", 0o755)
            print("✅ 起動用シェルスクリプトを作成しました: start_web_dakoku.sh")
            return True
        except Exception as e:
            print(f"❌ 起動用シェルスクリプトの作成に失敗しました: {e}")
            return False

def create_beginner_guide():
    """初心者向けガイドを作成"""
    print_step(9, "初心者向けガイドを作成しています...")
    
    guide_content = """# Web打刻ツール - 初心者向けガイド

## はじめに

このガイドは、Web打刻ツールを初めて使用する方向けに、基本的な使い方を説明します。

## 起動方法

### Windowsの場合
`start_web_dakoku.bat` をダブルクリックするだけで起動できます。

### macOS/Linuxの場合
ターミナルを開き、以下のコマンドを実行します：
```
./start_web_dakoku.sh
```

## 初期設定

初回起動時には、以下の設定が必要です：

1. **Web打刻システムのURL**: 会社のWeb打刻システムのURLを入力します。
2. **ユーザーID**: Web打刻システムのログインIDを入力します。
3. **パスワード**: Web打刻システムのパスワードを入力します。
4. **Web要素のセレクタ**: Web打刻システムの各要素のIDを設定します。

### Web要素のセレクタの設定方法

1. Web打刻システムにブラウザでアクセスします。
2. ログイン画面で右クリック→「検証」をクリックします。
3. 開発者ツールが開きます。
4. ユーザーID入力欄をクリックし、HTMLコードでその要素のID属性を確認します。
5. 同様に、パスワード入力欄、ログインボタンなどのID属性を確認します。
6. 確認したID属性を、Web打刻ツールの設定画面の対応する項目に入力します。

## トラブルシューティング

### ツールが起動しない場合
- Pythonが正しくインストールされているか確認してください。
- 必要なライブラリがインストールされているか確認してください。
- ログファイル（web_dakoku.log）を確認してください。

### ログインできない場合
- URL、ユーザーID、パスワードが正しいか確認してください。
- Web要素のセレクタが正しく設定されているか確認してください。
- 「テスト接続」ボタンをクリックして、接続テストを行ってください。

### ChromeDriverのエラーが発生する場合
- Google Chromeを最新バージョンにアップデートしてください。
- `setup_beginner.py` を再実行して、ChromeDriverを再インストールしてください。

## サポート

問題が解決しない場合は、以下の情報を添えて開発者に連絡してください：
- エラーメッセージ
- ログファイル（web_dakoku.log）
- 実行環境（OS、Pythonバージョンなど）

"""
    
    try:
        with open("BEGINNER_GUIDE.md", "w", encoding="utf-8") as f:
            f.write(guide_content)
        print("✅ 初心者向けガイドを作成しました: BEGINNER_GUIDE.md")
        return True
    except Exception as e:
        print(f"❌ 初心者向けガイドの作成に失敗しました: {e}")
        return False

def run_security_check():
    """セキュリティチェックを実行"""
    print_step(10, "セキュリティチェックを実行しています...")
    
    # requestsパッケージがインストールされているか確認
    try:
        import requests
    except ImportError:
        print("requestsパッケージをインストールしています...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "requests"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    # check_dependencies.pyが存在するか確認
    if not os.path.exists("check_dependencies.py"):
        print("❌ check_dependencies.pyが見つかりません。セキュリティチェックをスキップします。")
        return False
    
    try:
        print("依存ライブラリのセキュリティチェックを実行しています...")
        result = subprocess.run(
            [sys.executable, "check_dependencies.py"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print("❌ セキュリティチェックに失敗しました。")
            print("   エラーメッセージ:")
            print(result.stderr)
            return False
        
        print("✅ セキュリティチェックが完了しました。")
        print("   詳細なレポートは security_report.html を確認してください。")
        return True
    except Exception as e:
        print(f"❌ セキュリティチェック実行中にエラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print_header("Web打刻ツール - 初心者向けセットアップ")
    
    print("このスクリプトは、Seleniumを全く使ったことがない方でも")
    print("簡単にWeb打刻ツールをセットアップできるようにするためのものです。")
    print("\n各ステップを順番に実行していきます。")
    
    # 環境チェック
    if not check_python_version():
        print("\n❌ Pythonのバージョンが要件を満たしていないため、セットアップを中止します。")
        return False
    
    if not check_pip():
        print("\n❌ pipが正常に動作していないため、セットアップを中止します。")
        return False
    
    if not check_chrome():
        print("\n❌ Google Chromeが見つからないため、セットアップを中止します。")
        print("   Google Chromeをインストールした後、このスクリプトを再実行してください。")
        return False
    
    # 依存パッケージのインストール
    if not install_dependencies():
        print("\n❌ 依存パッケージのインストールに失敗したため、セットアップを中止します。")
        return False
    
    # Seleniumの初期設定
    if not setup_selenium():
        print("\n❌ Seleniumの初期設定に失敗したため、セットアップを中止します。")
        return False
    
    # テスト用スクリプトの作成と実行
    if not create_test_script():
        print("\n❌ テスト用スクリプトの作成に失敗したため、セットアップを中止します。")
        return False
    
    if not run_test_script():
        print("\n❌ テストに失敗したため、セットアップを中止します。")
        return False
    
    # 起動用スクリプトの作成
    create_startup_script()
    
    # 初心者向けガイドの作成
    create_beginner_guide()
    
    # セキュリティチェック
    print("\nセキュリティチェックを実行しますか？ (y/n): ", end="")
    choice = input().strip().lower()
    if choice == 'y':
        run_security_check()
    
    # セットアップ完了
    print_header("セットアップ完了")
    print("Web打刻ツールのセットアップが完了しました！")
    print("\n以下のファイルが作成されました:")
    
    system = platform.system()
    if system == "Windows":
        print("- start_web_dakoku.bat: Web打刻ツールを起動するためのバッチファイル")
    else:
        print("- start_web_dakoku.sh: Web打刻ツールを起動するためのシェルスクリプト")
        
    print("- BEGINNER_GUIDE.md: 初心者向けガイド")
    print("- test_selenium.py: Seleniumのテスト用スクリプト")
    
    print("\n使い方については、BEGINNER_GUIDE.mdを参照してください。")
    
    if system == "Windows":
        print("\nWeb打刻ツールを起動するには、start_web_dakoku.batをダブルクリックしてください。")
    else:
        print("\nWeb打刻ツールを起動するには、以下のコマンドを実行してください:")
        print("./start_web_dakoku.sh")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\nセットアップに失敗しました。")
            print("上記のエラーメッセージを確認し、問題を解決してから再度実行してください。")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nセットアップが中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n予期せぬエラーが発生しました: {e}")
        print("詳細はbeginner_setup.logを確認してください。")
        logger.exception("予期せぬエラーが発生しました")
        sys.exit(1) 