@echo off
echo Web打刻ツール - セットアップ
echo ==============================
echo.

echo 1. 依存パッケージのインストール
echo ------------------------------
call install_dependencies.bat
if %ERRORLEVEL% NEQ 0 (
    echo 依存パッケージのインストールに失敗しました。
    pause
    exit /b 1
)

echo.
echo 2. Seleniumのセットアップ
echo ------------------------
python setup_selenium.py
if %ERRORLEVEL% NEQ 0 (
    echo Seleniumのセットアップに失敗しました。
    echo ログファイル(setup_selenium.log)を確認してください。
    pause
    exit /b 1
)

echo.
echo 3. Seleniumのテスト
echo ------------------
python test_selenium.py
if %ERRORLEVEL% NEQ 0 (
    echo Seleniumのテストに失敗しました。
    pause
    exit /b 1
)

echo.
echo 4. セキュリティチェック（オプション）
echo ------------------------------
set /p security_check=セキュリティチェックを実行しますか？(y/n): 
if /i "%security_check%"=="y" (
    echo セキュリティチェックを実行しています...
    pip install requests
    python check_dependencies.py
    echo セキュリティチェックが完了しました。
    echo レポートは security_report.html を確認してください。
)

echo.
echo セットアップが完了しました！
echo Web打刻ツールを起動するには main.py を実行してください。
echo.
echo 例: python main.py
echo.
pause 