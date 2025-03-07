# Web打刻ツール

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)

会社のWeb打刻システムを自動化するデスクトップツールです。タスクトレイに常駐し、定期的に打刻確認を行います。

<img src="docs/screenshot.png" alt="スクリーンショット" width="500"/>

## 特徴

- タスクトレイに常駐するデスクトップアプリケーション
- 15分ごとに打刻確認のポップアップ表示
- 1日1回の出勤打刻と退勤打刻
- 朝12時までは出勤打刻の確認
- タスクトレイクリックで退勤打刻
- 出勤打刻済みで退勤打刻がない場合、夜10時に自動退勤打刻
- Web打刻システムへの自動アクセス
- ID・パスワードの暗号化保存
- Web要素のセレクタをGUIから設定可能
- 依存ライブラリのセキュリティチェック機能

## 必要条件

- Python 3.8以上
- 必要なライブラリ（requirements.txtに記載）

## インストール方法

1. リポジトリをクローンまたはダウンロードします：

```bash
git clone https://github.com/xtc1988/web-dakoku-tool.git
cd web-dakoku-tool
```

または、GitHubの[リポジトリページ](https://github.com/xtc1988/web-dakoku-tool)から「Code」→「Download ZIP」でダウンロードし、解凍してください。

2. 必要なライブラリをインストールします：

**方法1: バッチファイルを使用する場合（推奨）**
- `install_dependencies.bat` をダブルクリックするだけで必要なライブラリがインストールされます。
  - 注意: 文字化けが発生する場合は、英語表示の `install_dependencies.bat` を使用するか、以下の手順で日本語表示のバッチファイルを作成してください：
    1. `install_dependencies_ja.txt` の内容をコピー
    2. メモ帳を開き、コピーした内容を貼り付け
    3. 「ファイル」→「名前を付けて保存」を選択
    4. ファイル名を `install_dependencies_ja.bat` とし、文字コードを「ANSI」に設定して保存
    5. 作成したバッチファイルをダブルクリックして実行

**方法2: コマンドラインを使用する場合**
```bash
pip install -r requirements.txt
```

## セットアップ手順

### 初心者向け簡単セットアップ（最も簡単）

Seleniumを全く使ったことがない方向けの簡単セットアップ方法です。

#### Windowsの場合
1. `setup_beginner.bat` をダブルクリックして実行します。
2. 画面の指示に従って操作してください。
3. セットアップが完了すると、自動的に必要な設定が行われ、起動用のバッチファイルが作成されます。
4. `start_web_dakoku.bat` をダブルクリックしてアプリケーションを起動できます。

#### macOS/Linuxの場合
1. ターミナルを開きます。
2. スクリプトのあるディレクトリに移動します。
3. 以下のコマンドを実行します：
   ```
   chmod +x setup_beginner.sh
   ./setup_beginner.sh
   ```
4. 画面の指示に従って操作してください。
5. セットアップが完了すると、自動的に必要な設定が行われ、起動用のシェルスクリプトが作成されます。
6. `./start_web_dakoku.sh` コマンドでアプリケーションを起動できます。

### 簡単セットアップ（推奨）

#### Windowsの場合
1. `setup_all.bat` をダブルクリックして実行します。
2. セットアップが完了するまで待ちます。
3. セットアップ中に「セキュリティチェックを実行しますか？」と表示されたら、「y」を入力するとライブラリの安全性チェックが実行されます。
4. セットアップが完了したら、`python main.py` でアプリケーションを起動できます。

#### macOS/Linuxの場合
1. ターミナルを開きます。
2. スクリプトのあるディレクトリに移動します。
3. 以下のコマンドを実行します：
   ```
   chmod +x setup_all.sh
   ./setup_all.sh
   ```
4. セットアップ中に「セキュリティチェックを実行しますか？」と表示されたら、「y」を入力するとライブラリの安全性チェックが実行されます。
5. セットアップが完了したら、`python3 main.py` でアプリケーションを起動できます。

### 手動セットアップ

#### 1. 依存パッケージのインストール
```
pip install -r requirements.txt
```

#### 2. Seleniumのセットアップ
```
python setup_selenium.py
```

#### 3. セキュリティチェック（オプション）
```
python check_dependencies.py
```

#### 4. アプリケーションの起動
```
python main.py
```

## セキュリティチェックについて

このアプリケーションには、使用している依存ライブラリの安全性をチェックする機能が含まれています。セキュリティチェックでは以下の項目を確認します：

1. **既知の脆弱性**: 各ライブラリに既知のセキュリティ脆弱性がないかチェックします。
2. **怪しいパッケージ**: タイポスクワッティング（人気のあるパッケージ名に似た名前を使用する悪意のあるパッケージ）などの可能性をチェックします。
3. **人気度**: ダウンロード数の少ないパッケージを特定し、潜在的なリスクを評価します。
4. **パッケージ情報**: 作者、最終更新日などの基本情報を収集します。

セキュリティチェックを実行するには：

1. セットアップ時に「セキュリティチェックを実行しますか？」の問いに「y」と答える
2. または、手動で以下のコマンドを実行する：
   ```
   python check_dependencies.py
   ```

チェック結果は以下のファイルに保存されます：
- `security_report.json`: 詳細な結果（JSON形式）
- `security_report.html`: 見やすいHTML形式のレポート

セキュリティ上の問題が検出された場合は、レポートの推奨事項に従って対応してください。

## Seleniumについて

このアプリケーションはSeleniumを使用してWeb打刻システムを自動化しています。Seleniumは初めて使用する場合、以下の点に注意してください：

1. **Google Chromeが必要です**：最新バージョンのGoogle Chromeがインストールされていることを確認してください。
2. **ChromeDriverが自動的にダウンロードされます**：初回実行時に、お使いのChromeバージョンに合ったChromeDriverが自動的にダウンロードされます。
3. **ヘッドレスモード**：デフォルトでは、ブラウザは表示されずにバックグラウンドで動作します（ヘッドレスモード）。設定画面でこの動作を変更できます。

Seleniumのセットアップに問題がある場合は、`SELENIUM_SETUP.md` を参照してください。

## 使い方

1. アプリケーションを起動します：

```bash
python main.py
```

または、Windowsの場合は`start_dakoku.bat`をダブルクリックします。

2. 初回起動時に設定画面が表示されるので、Web打刻システムのURL、ユーザーID、パスワードを入力します。
3. 「詳細設定」タブでWeb要素のセレクタを設定します（実際のWeb打刻システムに合わせて調整）。
4. 設定完了後、アプリケーションはタスクトレイに常駐します。
5. 朝12時までは15分ごとに出勤打刻の確認ポップアップが表示されます。
6. タスクトレイアイコンをクリックすると退勤打刻が行われます。
7. 出勤打刻済みで退勤打刻がない場合、夜10時に自動的に退勤打刻が行われます。

## 他のPCでの使用方法

他のPCでWeb打刻ツールを使用するには、以下の手順に従ってください：

1. 新しいPCにPython（3.8以上）をインストールします。
   - [Python公式サイト](https://www.python.org/downloads/)からダウンロードしてインストール
   - インストール時に「Add Python to PATH」にチェックを入れることを忘れないでください

2. リポジトリをクローンまたはダウンロードします。
   - GitHubの[リポジトリページ](https://github.com/xtc1988/web-dakoku-tool)から「Code」→「Download ZIP」でダウンロードし、解凍

3. 必要なライブラリをインストールします：
   - `install_dependencies.bat` をダブルクリックするだけでOK
   - 文字化けが発生する場合は、上記の「インストール方法」セクションの注意事項を参照してください

4. アプリケーションを起動します：
   - `start_dakoku.bat` をダブルクリック

### 設定の移行

既存のPCから設定を移行する場合は、以下のファイルを新しいPCにコピーします：

1. `%USERPROFILE%\.web_dakoku\config.json`
2. `%USERPROFILE%\.web_dakoku\key.bin`

これらのファイルは、ユーザーのホームディレクトリ内の`.web_dakoku`フォルダにあります。

## Web要素セレクタの設定

Web打刻システムの要素IDは、「詳細設定」タブで設定できます。以下の要素IDを設定する必要があります：

1. ユーザーID入力: ユーザーID入力フィールドのID
2. パスワード入力: パスワード入力フィールドのID
3. ログインボタン: ログインボタンのID
4. 打刻パネル: ログイン成功後に表示される打刻パネルのID
5. 出勤打刻ボタン: 出勤打刻ボタンのID
6. 退勤打刻ボタン: 退勤打刻ボタンのID
7. 確認ボタン: 打刻確認ダイアログのOKボタンのID
8. 成功メッセージ: 打刻成功時に表示されるメッセージ要素のID

設定後、「テスト接続」ボタンをクリックして、設定が正しいか確認できます。

## 注意事項

- このツールは、特定のWeb打刻システムに対応するように設計されています。実際のWeb打刻システムに合わせて、Web要素のセレクタを設定する必要があります。
- ID・パスワードは暗号化されてローカルに保存されますが、完全なセキュリティを保証するものではありません。
- 会社のポリシーに従って使用してください。

## 貢献方法

1. このリポジトリをフォークします
2. 新しいブランチを作成します (`git checkout -b feature/amazing-feature`)
3. 変更をコミットします (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュします (`git push origin feature/amazing-feature`)
5. プルリクエストを作成します

## ライセンス

MITライセンスの下で配布されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
