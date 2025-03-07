@echo off
echo Web打刻ツール - 初心者向けセットアップ
echo ======================================
echo.

echo このスクリプトは、Seleniumを全く使ったことがない方でも
echo 簡単にWeb打刻ツールをセットアップできるようにするためのものです。
echo.
echo 以下の項目を自動的に確認・セットアップします：
echo  - Pythonのバージョン
echo  - Google Chromeのインストール状況
echo  - 必要なライブラリのインストール
echo  - Seleniumの初期設定
echo  - ChromeDriverのダウンロードとテスト
echo.
echo 準備ができたら何かキーを押して続行してください...
pause > nul

echo.
echo セットアップを開始します...
echo.

python setup_beginner.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo セットアップに失敗しました。
    echo 上記のエラーメッセージを確認し、問題を解決してから再度実行してください。
    echo.
    echo 詳細はbeginner_setup.logを確認してください。
    pause
    exit /b 1
)

echo.
echo セットアップが完了しました！
echo Web打刻ツールを起動するには、start_web_dakoku.batをダブルクリックしてください。
echo.
echo 使い方については、BEGINNER_GUIDE.mdを参照してください。
echo.
pause 