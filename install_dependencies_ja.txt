@echo off
echo ===================================================
echo Web打刻ツール - 必要なライブラリのインストール
echo ===================================================
echo.

REM Pythonがインストールされているか確認
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo エラー: Pythonが見つかりません。
    echo Pythonをインストールしてから再度実行してください。
    echo https://www.python.org/downloads/ からダウンロードできます。
    echo インストール時に「Add Python to PATH」にチェックを入れてください。
    echo.
    pause
    exit /b 1
)

REM Pythonのバージョンを確認
python --version
echo.

echo 必要なライブラリをインストールしています...
echo これには数分かかる場合があります。
echo.

REM pipを最新バージョンに更新
python -m pip install --upgrade pip

REM requirements.txtからライブラリをインストール
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo エラー: ライブラリのインストールに失敗しました。
    echo 管理者権限で実行するか、個別にインストールしてみてください。
    echo.
    echo 個別インストールコマンド:
    echo python -m pip install pillow pystray selenium cryptography
    echo.
) else (
    echo.
    echo ===================================================
    echo インストールが完了しました！
    echo Web打刻ツールを使用するには start_dakoku.bat をダブルクリックしてください。
    echo ===================================================
    echo.
)

pause 