#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Seleniumの初期セットアップスクリプト
Web打刻ツールを使用するために必要なSeleniumとChromeDriverの設定を自動化します。
"""

import os
import sys
import time
import subprocess
import platform
import logging
import zipfile
import shutil
import urllib.request
from pathlib import Path

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("setup_selenium.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_python_version():
    """Pythonのバージョンを確認"""
    logger.info(f"Pythonバージョン: {platform.python_version()}")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 6):
        logger.error("Python 3.6以上が必要です")
        return False
    return True

def check_pip():
    """pipがインストールされているか確認"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("pipが正常にインストールされています")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("pipがインストールされていないか、正常に動作していません")
        return False

def install_dependencies():
    """必要なパッケージをインストール"""
    packages = [
        "selenium",
        "webdriver-manager",
        "PySide6",
        "cryptography",
        "pillow"
    ]
    
    logger.info("必要なパッケージをインストールします...")
    
    for package in packages:
        try:
            logger.info(f"{package}をインストールしています...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"{package}のインストールが完了しました")
        except subprocess.SubprocessError as e:
            logger.error(f"{package}のインストールに失敗しました: {e}")
            return False
    
    logger.info("すべてのパッケージのインストールが完了しました")
    return True

def detect_chrome():
    """Chromeがインストールされているか確認"""
    system = platform.system()
    
    if system == "Windows":
        chrome_paths = [
            os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google\\Chrome\\Application\\chrome.exe")
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                logger.info(f"Chromeが見つかりました: {path}")
                return True, path
    
    elif system == "Darwin":  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            logger.info(f"Chromeが見つかりました: {chrome_path}")
            return True, chrome_path
    
    elif system == "Linux":
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                logger.info(f"Chromeが見つかりました: {path}")
                return True, path
    
    logger.warning("Chromeが見つかりませんでした")
    return False, None

def get_chrome_version(chrome_path):
    """Chromeのバージョンを取得"""
    if not chrome_path:
        return None
    
    try:
        if platform.system() == "Windows":
            # Windowsの場合はレジストリからバージョンを取得
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            logger.info(f"Chromeバージョン: {version}")
            return version
        else:
            # macOSとLinuxの場合はコマンドラインからバージョンを取得
            result = subprocess.run(
                [chrome_path, "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            version = result.stdout.strip().split()[-1]
            logger.info(f"Chromeバージョン: {version}")
            return version
    except Exception as e:
        logger.error(f"Chromeバージョンの取得に失敗しました: {e}")
        return None

def download_chromedriver(version=None):
    """ChromeDriverをダウンロード"""
    try:
        # webdriver-managerを使用してChromeDriverをダウンロード
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        
        logger.info("ChromeDriverをダウンロードしています...")
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriverのダウンロードが完了しました: {driver_path}")
        
        # ChromeDriverが正常に動作するか確認
        try:
            from selenium.webdriver.chrome.options import Options
            options = Options()
            options.add_argument("--headless=new")
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            driver.quit()
            logger.info("ChromeDriverが正常に動作することを確認しました")
        except Exception as e:
            logger.warning(f"ChromeDriverのテストに失敗しました: {e}")
        
        return True, driver_path
    except Exception as e:
        logger.error(f"ChromeDriverのダウンロードに失敗しました: {e}")
        return False, None

def create_test_script():
    """テスト用のスクリプトを作成"""
    test_script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Seleniumの動作確認用スクリプト
\"\"\"

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def test_selenium():
    print("Seleniumの動作確認を開始します...")
    
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
        driver.save_screenshot("selenium_test.png")
        print("スクリーンショットを保存しました: selenium_test.png")
        
        # ブラウザを閉じる
        driver.quit()
        
        print("テストが正常に完了しました！")
        return True
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    test_selenium()
"""
    
    try:
        with open("test_selenium.py", "w", encoding="utf-8") as f:
            f.write(test_script)
        logger.info("テスト用スクリプトを作成しました: test_selenium.py")
        return True
    except Exception as e:
        logger.error(f"テスト用スクリプトの作成に失敗しました: {e}")
        return False

def create_setup_bat():
    """Windowsユーザー向けのセットアップバッチファイルを作成"""
    bat_content = """@echo off
echo Web打刻ツール - Seleniumセットアップ
echo ======================================
echo.

python setup_selenium.py
if %ERRORLEVEL% NEQ 0 (
    echo セットアップに失敗しました。
    echo ログファイル(setup_selenium.log)を確認してください。
    pause
    exit /b 1
)

echo.
echo セットアップが完了しました！
echo テストスクリプトを実行します...
echo.

python test_selenium.py
if %ERRORLEVEL% NEQ 0 (
    echo テストに失敗しました。
    pause
    exit /b 1
)

echo.
echo すべての設定が完了しました！
echo Web打刻ツールを起動するには main.py を実行してください。
pause
"""
    
    try:
        with open("setup_selenium.bat", "w", encoding="utf-8") as f:
            f.write(bat_content)
        logger.info("セットアップバッチファイルを作成しました: setup_selenium.bat")
        return True
    except Exception as e:
        logger.error(f"セットアップバッチファイルの作成に失敗しました: {e}")
        return False

def create_setup_sh():
    """Linux/macOSユーザー向けのセットアップシェルスクリプトを作成"""
    sh_content = """#!/bin/bash
echo "Web打刻ツール - Seleniumセットアップ"
echo "======================================"
echo

python3 setup_selenium.py
if [ $? -ne 0 ]; then
    echo "セットアップに失敗しました。"
    echo "ログファイル(setup_selenium.log)を確認してください。"
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo
echo "セットアップが完了しました！"
echo "テストスクリプトを実行します..."
echo

python3 test_selenium.py
if [ $? -ne 0 ]; then
    echo "テストに失敗しました。"
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo
echo "すべての設定が完了しました！"
echo "Web打刻ツールを起動するには python3 main.py を実行してください。"
read -p "Enterキーを押して終了..."
"""
    
    try:
        with open("setup_selenium.sh", "w", encoding="utf-8") as f:
            f.write(sh_content)
        
        # 実行権限を付与
        if platform.system() != "Windows":
            os.chmod("setup_selenium.sh", 0o755)
            
        logger.info("セットアップシェルスクリプトを作成しました: setup_selenium.sh")
        return True
    except Exception as e:
        logger.error(f"セットアップシェルスクリプトの作成に失敗しました: {e}")
        return False

def create_readme():
    """セットアップ手順のREADMEを作成"""
    readme_content = """# Web打刻ツール - Seleniumセットアップ手順

このスクリプトは、Web打刻ツールを使用するために必要なSeleniumとChromeDriverの設定を自動化します。

## 前提条件

- Python 3.6以上がインストールされていること
- Google Chromeがインストールされていること
- インターネット接続があること

## セットアップ手順

### Windowsの場合

1. `setup_selenium.bat` をダブルクリックして実行します。
2. セットアップが完了するまで待ちます。
3. テストが成功したら、Web打刻ツールを使用できます。

### macOS/Linuxの場合

1. ターミナルを開きます。
2. スクリプトのあるディレクトリに移動します。
3. 以下のコマンドを実行します：
   ```
   ./setup_selenium.sh
   ```
4. セットアップが完了するまで待ちます。
5. テストが成功したら、Web打刻ツールを使用できます。

## 手動セットアップ

自動セットアップが失敗した場合は、以下の手順で手動セットアップを行ってください：

1. 必要なパッケージをインストールします：
   ```
   pip install selenium webdriver-manager PySide6 cryptography pillow
   ```

2. ChromeDriverをダウンロードします：
   - [ChromeDriverのダウンロードページ](https://chromedriver.chromium.org/downloads)からお使いのChromeバージョンに合ったドライバーをダウンロードします。
   - ダウンロードしたファイルを解凍し、`chromedriver.exe`（Windowsの場合）または`chromedriver`（macOS/Linuxの場合）をWeb打刻ツールのディレクトリに配置します。

3. テストスクリプトを実行して動作確認を行います：
   ```
   python test_selenium.py
   ```

## トラブルシューティング

セットアップに失敗した場合は、以下を確認してください：

1. Pythonが正しくインストールされているか
2. Google Chromeが最新バージョンか
3. インターネット接続が安定しているか
4. ファイアウォールやセキュリティソフトがダウンロードをブロックしていないか

詳細なエラー情報は `setup_selenium.log` ファイルを確認してください。
"""
    
    try:
        with open("SELENIUM_SETUP.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        logger.info("セットアップ手順のREADMEを作成しました: SELENIUM_SETUP.md")
        return True
    except Exception as e:
        logger.error(f"セットアップ手順のREADMEの作成に失敗しました: {e}")
        return False

def main():
    """メイン処理"""
    logger.info("Seleniumセットアップスクリプトを開始します")
    
    # Pythonバージョンの確認
    if not check_python_version():
        logger.error("Pythonバージョンが要件を満たしていません。Python 3.6以上が必要です。")
        return False
    
    # pipの確認
    if not check_pip():
        logger.error("pipが正常に動作していません。Pythonのインストールを確認してください。")
        return False
    
    # 依存パッケージのインストール
    if not install_dependencies():
        logger.error("依存パッケージのインストールに失敗しました。")
        return False
    
    # Chromeの検出
    chrome_installed, chrome_path = detect_chrome()
    if not chrome_installed:
        logger.warning("Google Chromeが見つかりませんでした。インストールしてください。")
    else:
        # Chromeバージョンの取得
        chrome_version = get_chrome_version(chrome_path)
    
    # ChromeDriverのダウンロード
    driver_downloaded, driver_path = download_chromedriver()
    if not driver_downloaded:
        logger.error("ChromeDriverのダウンロードに失敗しました。")
        return False
    
    # テストスクリプトの作成
    if not create_test_script():
        logger.error("テストスクリプトの作成に失敗しました。")
        return False
    
    # セットアップスクリプトの作成
    if platform.system() == "Windows":
        if not create_setup_bat():
            logger.error("セットアップバッチファイルの作成に失敗しました。")
    else:
        if not create_setup_sh():
            logger.error("セットアップシェルスクリプトの作成に失敗しました。")
    
    # READMEの作成
    if not create_readme():
        logger.error("セットアップ手順のREADMEの作成に失敗しました。")
    
    logger.info("セットアップスクリプトが完了しました")
    print("\nセットアップが完了しました！")
    print(f"ChromeDriverのパス: {driver_path}")
    print("\nテストスクリプトを実行するには:")
    print("  python test_selenium.py")
    print("\nWeb打刻ツールを起動するには:")
    print("  python main.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.exception(f"予期せぬエラーが発生しました: {e}")
        print(f"エラーが発生しました: {e}")
        print("詳細はsetup_selenium.logを確認してください。")
        sys.exit(1) 