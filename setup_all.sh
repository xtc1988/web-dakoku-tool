#!/bin/bash
echo "Web打刻ツール - セットアップ"
echo "=============================="
echo

echo "1. 依存パッケージのインストール"
echo "------------------------------"
bash install_dependencies.sh
if [ $? -ne 0 ]; then
    echo "依存パッケージのインストールに失敗しました。"
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo
echo "2. Seleniumのセットアップ"
echo "------------------------"
python3 setup_selenium.py
if [ $? -ne 0 ]; then
    echo "Seleniumのセットアップに失敗しました。"
    echo "ログファイル(setup_selenium.log)を確認してください。"
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo
echo "3. Seleniumのテスト"
echo "------------------"
python3 test_selenium.py
if [ $? -ne 0 ]; then
    echo "Seleniumのテストに失敗しました。"
    read -p "Enterキーを押して終了..."
    exit 1
fi

echo
echo "4. セキュリティチェック（オプション）"
echo "------------------------------"
read -p "セキュリティチェックを実行しますか？(y/n): " security_check
if [ "$security_check" = "y" ] || [ "$security_check" = "Y" ]; then
    echo "セキュリティチェックを実行しています..."
    pip3 install requests
    python3 check_dependencies.py
    echo "セキュリティチェックが完了しました。"
    echo "レポートは security_report.html を確認してください。"
fi

echo
echo "セットアップが完了しました！"
echo "Web打刻ツールを起動するには main.py を実行してください。"
echo
echo "例: python3 main.py"
echo
read -p "Enterキーを押して終了..." 