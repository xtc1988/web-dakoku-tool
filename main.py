#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime
import schedule
import threading
import json
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, 
                              QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QLineEdit, QPushButton, 
                              QMessageBox, QDialog, QTabWidget,
                              QGridLayout, QGroupBox, QScrollArea)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject

from config_manager import ConfigManager
from web_dakoku import WebDakoku
from create_icon import create_clock_icon

class DakokuApp(QApplication):
    """打刻アプリケーションのメインクラス"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # 設定マネージャーの初期化
        self.config_manager = ConfigManager()
        
        # Web打刻ハンドラの初期化
        self.web_dakoku = WebDakoku(self.config_manager)
        
        # アイコンの準備
        self.prepare_icon()
        
        # システムトレイアイコンの設定
        self.setup_tray_icon()
        
        # 状態変数の初期化
        self.today_clock_in = False
        self.today_clock_out = False
        self.last_check_date = None
        
        # 定期チェックタイマーの設定
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_dakoku)
        self.check_timer.start(15 * 60 * 1000)  # 15分ごとにチェック
        
        # 日付変更チェックタイマーの設定
        self.date_check_timer = QTimer(self)
        self.date_check_timer.timeout.connect(self.check_date_change)
        self.date_check_timer.start(60 * 60 * 1000)  # 1時間ごとにチェック
        
        # 自動退勤タイマーの設定
        self.setup_auto_clock_out()
        
        # 初回起動時のチェック
        self.check_dakoku()
    
    def prepare_icon(self):
        """アイコンの準備"""
        icon_dir = Path(__file__).parent / "icons"
        icon_dir.mkdir(exist_ok=True)
        
        self.icon_path = icon_dir / "clock_icon.png"
        
        # アイコンが存在しない場合は作成
        if not self.icon_path.exists():
            create_clock_icon(self.icon_path)
    
    def setup_tray_icon(self):
        """システムトレイアイコンの設定"""
        # アイコンの作成
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(str(self.icon_path)))
        self.tray_icon.setToolTip("Web打刻ツール")
        
        # メニューの作成
        tray_menu = QMenu()
        
        # 出勤打刻アクション
        clock_in_action = QAction("出勤打刻", self)
        clock_in_action.triggered.connect(self.manual_clock_in)
        tray_menu.addAction(clock_in_action)
        
        # 退勤打刻アクション
        clock_out_action = QAction("退勤打刻", self)
        clock_out_action.triggered.connect(self.manual_clock_out)
        tray_menu.addAction(clock_out_action)
        
        tray_menu.addSeparator()
        
        # 設定アクション
        settings_action = QAction("設定", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        # 終了アクション
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self.quit)
        tray_menu.addAction(quit_action)
        
        # メニューをトレイアイコンに設定
        self.tray_icon.setContextMenu(tray_menu)
        
        # トレイアイコンのクリックイベント
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # トレイアイコンを表示
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """トレイアイコンがクリックされたときの処理"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # シングルクリックで退勤打刻
            self.manual_clock_out()
    
    def check_dakoku(self):
        """打刻状態のチェック"""
        now = datetime.datetime.now()
        
        # 設定が完了しているか確認
        if not self.config_manager.is_configured():
            self.show_notification("設定が必要です", "Web打刻ツールの設定を行ってください")
            self.show_settings()
            return
        
        # 日付が変わっていたら状態をリセット
        if self.last_check_date is not None and self.last_check_date.date() != now.date():
            self.today_clock_in = False
            self.today_clock_out = False
        
        self.last_check_date = now
        
        # 出勤打刻のチェック（12時前かつ未打刻の場合）
        if not self.today_clock_in and now.hour < 12:
            self.show_clock_in_dialog()
        
        # 退勤打刻のチェック（出勤済みかつ未退勤の場合）
        if self.today_clock_in and not self.today_clock_out and now.hour >= 17:
            self.show_notification("退勤打刻", "タスクトレイアイコンをクリックして退勤打刻ができます")
    
    def check_date_change(self):
        """日付変更のチェック"""
        now = datetime.datetime.now()
        
        # 日付が変わっていたら状態をリセット
        if self.last_check_date is not None and self.last_check_date.date() != now.date():
            self.today_clock_in = False
            self.today_clock_out = False
            self.last_check_date = now
    
    def setup_auto_clock_out(self):
        """自動退勤処理のスケジュール設定"""
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        # 毎日22時に自動退勤
        schedule.every().day.at("22:00").do(self.auto_clock_out)
        
        # スケジューラを別スレッドで実行
        scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        scheduler_thread.start()
    
    def auto_clock_out(self):
        """自動退勤処理"""
        if self.today_clock_in and not self.today_clock_out:
            success = self.web_dakoku.clock_out()
            if success:
                self.today_clock_out = True
                self.show_notification("自動退勤打刻", "退勤打刻が完了しました")
            else:
                self.show_notification("自動退勤打刻エラー", "退勤打刻に失敗しました")
    
    def manual_clock_in(self):
        """手動出勤打刻"""
        if self.today_clock_in:
            self.show_notification("既に出勤打刻済みです", "本日は既に出勤打刻が完了しています")
            return
        
        success = self.web_dakoku.clock_in()
        if success:
            self.today_clock_in = True
            self.show_notification("出勤打刻完了", "出勤打刻が完了しました")
        else:
            self.show_notification("出勤打刻エラー", "出勤打刻に失敗しました")
    
    def manual_clock_out(self):
        """手動退勤打刻"""
        if not self.today_clock_in:
            self.show_notification("出勤打刻が必要です", "先に出勤打刻を行ってください")
            return
        
        if self.today_clock_out:
            self.show_notification("既に退勤打刻済みです", "本日は既に退勤打刻が完了しています")
            return
        
        success = self.web_dakoku.clock_out()
        if success:
            self.today_clock_out = True
            self.show_notification("退勤打刻完了", "退勤打刻が完了しました")
        else:
            self.show_notification("退勤打刻エラー", "退勤打刻に失敗しました")
    
    def show_clock_in_dialog(self):
        """出勤打刻確認ダイアログの表示"""
        dialog = QMessageBox()
        dialog.setWindowTitle("出勤打刻確認")
        dialog.setText("出勤打刻を行いますか？")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        # ダイアログを最前面に表示
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        result = dialog.exec()
        if result == QMessageBox.StandardButton.Yes:
            self.manual_clock_in()
    
    def show_notification(self, title, message):
        """通知の表示"""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)
    
    def show_settings(self):
        """設定画面の表示"""
        settings_dialog = SettingsDialog(self.config_manager, self.web_dakoku)
        settings_dialog.exec()
    
    def quit(self):
        """アプリケーションの終了"""
        # 確認ダイアログ
        dialog = QMessageBox()
        dialog.setWindowTitle("終了確認")
        dialog.setText("Web打刻ツールを終了しますか？")
        dialog.setInformativeText("終了すると自動打刻機能が動作しなくなります。")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        
        result = dialog.exec()
        if result == QMessageBox.StandardButton.Yes:
            super().quit()


class SettingsDialog(QDialog):
    """設定ダイアログ"""
    
    def __init__(self, config_manager, web_dakoku=None):
        super().__init__()
        self.config_manager = config_manager
        self.web_dakoku = web_dakoku
        
        self.setWindowTitle("Web打刻ツール設定")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI要素の設定"""
        layout = QVBoxLayout()
        
        # スクロールエリアの作成
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 基本設定グループ
        basic_group = QGroupBox("基本設定")
        basic_layout = QVBoxLayout()
        
        # Web打刻URL
        url_layout = QHBoxLayout()
        url_label = QLabel("Web打刻URL:")
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        basic_layout.addLayout(url_layout)
        
        # ユーザーID
        user_id_layout = QHBoxLayout()
        user_id_label = QLabel("ユーザーID:")
        self.user_id_input = QLineEdit()
        user_id_layout.addWidget(user_id_label)
        user_id_layout.addWidget(self.user_id_input)
        basic_layout.addLayout(user_id_layout)
        
        # パスワード
        password_layout = QHBoxLayout()
        password_label = QLabel("パスワード:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        basic_layout.addLayout(password_layout)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # セレクタ設定グループ
        selectors_group = QGroupBox("Web要素セレクタ設定")
        selectors_layout = QGridLayout()
        
        # セレクタ入力フィールドの作成
        self.selector_inputs = {}
        
        # ユーザーID入力フィールド
        selectors_layout.addWidget(QLabel("ユーザーID入力:"), 0, 0)
        self.selector_inputs["user_id_input"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["user_id_input"], 0, 1)
        
        # パスワード入力フィールド
        selectors_layout.addWidget(QLabel("パスワード入力:"), 1, 0)
        self.selector_inputs["password_input"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["password_input"], 1, 1)
        
        # ログインボタン
        selectors_layout.addWidget(QLabel("ログインボタン:"), 2, 0)
        self.selector_inputs["login_button"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["login_button"], 2, 1)
        
        # 打刻パネル
        selectors_layout.addWidget(QLabel("打刻パネル:"), 3, 0)
        self.selector_inputs["dakoku_panel"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["dakoku_panel"], 3, 1)
        
        # 出勤打刻ボタン
        selectors_layout.addWidget(QLabel("出勤打刻ボタン:"), 4, 0)
        self.selector_inputs["clock_in_button"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["clock_in_button"], 4, 1)
        
        # 退勤打刻ボタン
        selectors_layout.addWidget(QLabel("退勤打刻ボタン:"), 5, 0)
        self.selector_inputs["clock_out_button"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["clock_out_button"], 5, 1)
        
        # 確認ボタン
        selectors_layout.addWidget(QLabel("確認ボタン:"), 6, 0)
        self.selector_inputs["confirm_button"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["confirm_button"], 6, 1)
        
        # 成功メッセージ
        selectors_layout.addWidget(QLabel("成功メッセージ:"), 7, 0)
        self.selector_inputs["success_message"] = QLineEdit()
        selectors_layout.addWidget(self.selector_inputs["success_message"], 7, 1)
        
        selectors_group.setLayout(selectors_layout)
        scroll_layout.addWidget(selectors_group)
        
        # 説明テキスト
        help_text = QLabel("※ 各要素のIDを入力してください。実際のWeb打刻システムに合わせて設定してください。")
        help_text.setWordWrap(True)
        scroll_layout.addWidget(help_text)
        
        # テスト接続ボタン
        test_button = QPushButton("テスト接続")
        test_button.clicked.connect(self.test_connection)
        scroll_layout.addWidget(test_button)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # ボタン
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """設定の読み込み"""
        config = self.config_manager.get_config()
        
        # 基本設定
        self.url_input.setText(config.get("url", ""))
        self.user_id_input.setText(config.get("user_id", ""))
        
        # パスワードを読み込む（保持する）
        if "password" in config and config["password"]:
            self.password_input.setText(config.get("password", ""))
        
        # セレクタ設定
        selectors = config.get("selectors", {})
        for key, input_field in self.selector_inputs.items():
            input_field.setText(selectors.get(key, ""))
    
    def save_settings(self):
        """設定の保存"""
        # 基本設定の取得
        url = self.url_input.text().strip()
        user_id = self.user_id_input.text().strip()
        password = self.password_input.text()
        
        # 基本設定のバリデーション
        if not url:
            QMessageBox.warning(self, "入力エラー", "URLは必須項目です")
            return
        
        if not user_id:
            QMessageBox.warning(self, "入力エラー", "ユーザーIDは必須項目です")
            return
        
        # パスワードが入力されていない場合は既存のパスワードを使用
        if not password:
            config = self.config_manager.get_config()
            password = config.get("password", "")
            if not password:
                QMessageBox.warning(self, "入力エラー", "パスワードを入力してください")
                return
        
        # セレクタ設定の取得
        selectors = {}
        for key, input_field in self.selector_inputs.items():
            value = input_field.text().strip()
            if value:
                selectors[key] = value
        
        # 設定の保存
        self.config_manager.save_config(url, user_id, password, selectors)
        
        # Web打刻ハンドラのセレクタを更新
        if self.web_dakoku:
            self.web_dakoku._load_selectors()
        
        QMessageBox.information(self, "設定保存", "設定を保存しました")
        self.accept()
    
    def test_connection(self):
        """テスト接続"""
        # 現在の設定を一時的に保存
        url = self.url_input.text().strip()
        user_id = self.user_id_input.text().strip()
        password = self.password_input.text()
        
        if not url:
            QMessageBox.warning(self, "入力エラー", "URLを入力してください")
            return
        
        if not user_id:
            QMessageBox.warning(self, "入力エラー", "ユーザーIDを入力してください")
            return
        
        if not password:
            QMessageBox.warning(self, "入力エラー", "パスワードを入力してください")
            return
        
        # セレクタ設定の取得
        selectors = {}
        for key, input_field in self.selector_inputs.items():
            value = input_field.text().strip()
            if value:
                selectors[key] = value
        
        # 一時的に設定を保存
        self.config_manager.save_config(url, user_id, password, selectors)
        
        # Web打刻ハンドラのセレクタを更新
        if self.web_dakoku:
            self.web_dakoku._load_selectors()
            
            # テスト接続
            QMessageBox.information(self, "テスト接続", "テスト接続を開始します。\nこの処理には時間がかかる場合があります。")
            
            # 別スレッドでテスト接続を実行
            def run_test():
                error_message = None
                driver = None
                
                try:
                    driver = self.web_dakoku._setup_driver()
                    if not driver:
                        error_message = "WebDriverの初期化に失敗しました"
                        return
                    
                    success = self.web_dakoku._login(driver)
                    if success:
                        QMessageBox.information(self, "テスト接続成功", "Web打刻システムへの接続に成功しました")
                    else:
                        # ログからエラーメッセージを取得
                        with open('web_dakoku.log', 'r', encoding='utf-8') as f:
                            log_lines = f.readlines()
                            # 最新の10行を取得
                            recent_logs = ''.join(log_lines[-10:])
                        
                        error_message = f"Web打刻システムへの接続に失敗しました\n設定を確認してください\n\nエラーログ:\n{recent_logs}"
                finally:
                    if driver:
                        driver.quit()
                    
                    if error_message:
                        QMessageBox.warning(self, "テスト接続失敗", error_message)
            
            threading.Thread(target=run_test).start()


def main():
    app = DakokuApp(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 