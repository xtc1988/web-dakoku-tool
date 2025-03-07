#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime
import schedule
import threading
import json
import logging
from datetime import datetime, time as dt_time
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, 
                              QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QLineEdit, QPushButton, 
                              QMessageBox, QDialog, QTabWidget,
                              QGridLayout, QGroupBox, QScrollArea,
                              QFormLayout, QTimeEdit, QCheckBox,
                              QMainWindow)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject, QTime

from config_manager import ConfigManager
from web_dakoku import WebDakoku
from create_icon import create_clock_icon

# ロガーの設定
logging.basicConfig(
    filename='web_dakoku.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DakokuApp(QApplication):
    """打刻アプリケーションのメインクラス"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # 設定マネージャーの初期化
        self.config_manager = ConfigManager("config.json")
        
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
        
        # 自動退勤タイマー
        self.auto_end_timer = QTimer(self)
        self.auto_end_timer.timeout.connect(self.check_auto_end)
        self.auto_end_timer.start(60000)  # 1分ごとにチェック
        
        # UIのセットアップ
        self.setup_ui()
    
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

    def check_auto_end(self):
        """自動退勤のチェック"""
        try:
            # 設定を読み込む
            config = self.config_manager.load_config()
            advanced = config.get("advanced", {})
            auto_end = advanced.get("auto_end", {})
            
            # 自動退勤が有効かチェック
            if not auto_end.get("enabled", False):
                return
                
            # 現在時刻の取得
            now = datetime.now()
            current_time = now.time()
            
            # 設定された退勤時刻の取得
            auto_end_time_str = auto_end.get("time", "18:00")
            hours, minutes = map(int, auto_end_time_str.split(":"))
            auto_end_time = dt_time(hours, minutes)
            
            # 現在時刻が設定時刻を過ぎているかチェック
            if current_time >= auto_end_time:
                # 既に退勤済みかチェック（実装が必要）
                # ここでは簡易的に実装
                self.end_work(auto=True)
        except Exception as e:
            logging.error(f"自動退勤チェック中にエラーが発生しました: {e}")
            
    def start_work(self):
        """出勤処理"""
        self.status_label.setText("ステータス: 出勤処理中...")
        
        # 別スレッドで実行
        def run_start():
            try:
                # WebDriverのセットアップ
                driver = self.web_dakoku._setup_driver()
                if not driver:
                    self.status_label.setText("ステータス: WebDriverの初期化に失敗しました")
                    QMessageBox.warning(self, "エラー", "WebDriverの初期化に失敗しました")
                    return
                    
                # ログイン
                if not self.web_dakoku._login(driver):
                    self.status_label.setText("ステータス: ログインに失敗しました")
                    QMessageBox.warning(self, "エラー", "ログインに失敗しました")
                    driver.quit()
                    return
                    
                # 出勤打刻
                success = self.web_dakoku.clock_in(driver)
                
                # 結果の表示
                if success:
                    self.status_label.setText("ステータス: 出勤打刻完了")
                    QMessageBox.information(self, "成功", "出勤打刻が完了しました")
                else:
                    self.status_label.setText("ステータス: 出勤打刻に失敗しました")
                    QMessageBox.warning(self, "エラー", "出勤打刻に失敗しました")
                    
                # WebDriverの終了
                driver.quit()
            except Exception as e:
                self.status_label.setText(f"ステータス: エラー - {str(e)}")
                QMessageBox.warning(self, "エラー", f"出勤処理中にエラーが発生しました: {str(e)}")
                
        threading.Thread(target=run_start).start()
        
    def end_work(self, auto=False):
        """退勤処理"""
        if auto:
            self.status_label.setText("ステータス: 自動退勤処理中...")
        else:
            self.status_label.setText("ステータス: 退勤処理中...")
            
        # 別スレッドで実行
        def run_end():
            try:
                # WebDriverのセットアップ
                driver = self.web_dakoku._setup_driver()
                if not driver:
                    self.status_label.setText("ステータス: WebDriverの初期化に失敗しました")
                    if not auto:
                        QMessageBox.warning(self, "エラー", "WebDriverの初期化に失敗しました")
                    return
                    
                # ログイン
                if not self.web_dakoku._login(driver):
                    self.status_label.setText("ステータス: ログインに失敗しました")
                    if not auto:
                        QMessageBox.warning(self, "エラー", "ログインに失敗しました")
                    driver.quit()
                    return
                    
                # 退勤打刻
                success = self.web_dakoku.clock_out(driver)
                
                # 結果の表示
                if success:
                    if auto:
                        self.status_label.setText("ステータス: 自動退勤打刻完了")
                        # 自動退勤の場合は通知のみ
                        self.tray_icon.showMessage("Web打刻ツール", "自動退勤打刻が完了しました", QIcon("icon.png"), 5000)
                    else:
                        self.status_label.setText("ステータス: 退勤打刻完了")
                        QMessageBox.information(self, "成功", "退勤打刻が完了しました")
                else:
                    if auto:
                        self.status_label.setText("ステータス: 自動退勤打刻に失敗しました")
                        self.tray_icon.showMessage("Web打刻ツール", "自動退勤打刻に失敗しました", QIcon("icon.png"), 5000)
                    else:
                        self.status_label.setText("ステータス: 退勤打刻に失敗しました")
                        QMessageBox.warning(self, "エラー", "退勤打刻に失敗しました")
                    
                # WebDriverの終了
                driver.quit()
            except Exception as e:
                error_msg = f"退勤処理中にエラーが発生しました: {str(e)}"
                self.status_label.setText(f"ステータス: エラー - {str(e)}")
                if auto:
                    self.tray_icon.showMessage("Web打刻ツール", error_msg, QIcon("icon.png"), 5000)
                else:
                    QMessageBox.warning(self, "エラー", error_msg)
                
        threading.Thread(target=run_end).start()


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
        """UIのセットアップ"""
        self.setWindowTitle("Web打刻ツール")
        self.setGeometry(100, 100, 600, 500)
        
        # メインレイアウト
        main_layout = QVBoxLayout()
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # メインタブ
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout()
        
        # 設定タブ
        settings_tab = QWidget()
        settings_tab_layout = QVBoxLayout()
        
        # メインタブのUI
        # URL入力
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_tab_layout.addLayout(url_layout)
        
        # ユーザーID入力
        user_id_layout = QHBoxLayout()
        user_id_label = QLabel("ユーザーID:")
        self.user_id_input = QLineEdit()
        user_id_layout.addWidget(user_id_label)
        user_id_layout.addWidget(self.user_id_input)
        main_tab_layout.addLayout(user_id_layout)
        
        # パスワード入力
        password_layout = QHBoxLayout()
        password_label = QLabel("パスワード:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        main_tab_layout.addLayout(password_layout)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # テスト接続ボタン
        self.test_button = QPushButton("テスト接続")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        # 保存ボタン
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        main_tab_layout.addLayout(button_layout)
        
        # 打刻ボタンレイアウト
        dakoku_button_layout = QHBoxLayout()
        
        # 出勤ボタン
        self.start_button = QPushButton("出勤")
        self.start_button.clicked.connect(self.start_work)
        dakoku_button_layout.addWidget(self.start_button)
        
        # 退勤ボタン
        self.end_button = QPushButton("退勤")
        self.end_button.clicked.connect(self.end_work)
        dakoku_button_layout.addWidget(self.end_button)
        
        main_tab_layout.addLayout(dakoku_button_layout)
        
        # ステータス表示
        self.status_label = QLabel("ステータス: 準備完了")
        main_tab_layout.addWidget(self.status_label)
        
        # 設定タブのUI
        # セレクタ設定のグループボックス
        selector_group = QGroupBox("Web要素セレクタ設定")
        selector_layout = QVBoxLayout()
        
        # セレクタの説明
        selector_info = QLabel("以下の項目は、Web打刻システムの各要素を特定するためのセレクタです。\n"
                              "要素のID属性を入力してください。\n"
                              "例: ユーザーID入力フィールドのHTMLが <input id=\"user_id\"> の場合、\n"
                              "「ユーザーIDセレクタ」に「user_id」と入力します。")
        selector_info.setWordWrap(True)
        selector_layout.addWidget(selector_info)
        
        # セレクタ入力フィールド
        self.selector_inputs = {}
        
        # セレクタ設定のフォームレイアウト
        form_layout = QFormLayout()
        
        # 各セレクタの入力フィールドを作成
        selector_fields = [
            ("user_id_selector", "ユーザーIDセレクタ", "ユーザーID入力フィールドのID"),
            ("password_selector", "パスワードセレクタ", "パスワード入力フィールドのID"),
            ("login_button_selector", "ログインボタンセレクタ", "ログインボタンのID"),
            ("success_element_selector", "ログイン成功要素セレクタ", "ログイン成功時に表示される要素のID"),
            ("start_button_selector", "出勤ボタンセレクタ", "出勤ボタンのID"),
            ("end_button_selector", "退勤ボタンセレクタ", "退勤ボタンのID")
        ]
        
        for key, label, placeholder in selector_fields:
            input_field = QLineEdit()
            input_field.setPlaceholderText(placeholder)
            
            # ツールチップを設定
            input_field.setToolTip(f"{placeholder}\n例: {key.replace('_selector', '')}")
            
            # 入力補助ボタン
            help_button = QPushButton("?")
            help_button.setFixedSize(20, 20)
            help_button.setToolTip(f"{placeholder}の詳細説明")
            
            # ヘルプボタンのクリックイベント
            help_button.clicked.connect(lambda checked, k=key: self.show_selector_help(k))
            
            # 水平レイアウトでフィールドとヘルプボタンを配置
            field_layout = QHBoxLayout()
            field_layout.addWidget(input_field)
            field_layout.addWidget(help_button)
            
            form_layout.addRow(label, field_layout)
            self.selector_inputs[key] = input_field
        
        selector_layout.addLayout(form_layout)
        selector_group.setLayout(selector_layout)
        settings_tab_layout.addWidget(selector_group)
        
        # 詳細設定のグループボックス
        advanced_group = QGroupBox("詳細設定")
        advanced_layout = QVBoxLayout()
        
        # 自動退勤設定
        auto_end_layout = QHBoxLayout()
        auto_end_label = QLabel("自動退勤時刻:")
        self.auto_end_time_edit = QTimeEdit()
        self.auto_end_time_edit.setDisplayFormat("HH:mm")
        self.auto_end_time_edit.setTime(QTime(18, 0))  # デフォルト18:00
        self.auto_end_checkbox = QCheckBox("有効")
        auto_end_layout.addWidget(auto_end_label)
        auto_end_layout.addWidget(self.auto_end_time_edit)
        auto_end_layout.addWidget(self.auto_end_checkbox)
        advanced_layout.addLayout(auto_end_layout)
        
        # ヘッドレスモード設定
        headless_layout = QHBoxLayout()
        headless_label = QLabel("ヘッドレスモード:")
        self.headless_checkbox = QCheckBox("有効")
        self.headless_checkbox.setChecked(True)  # デフォルトで有効
        headless_layout.addWidget(headless_label)
        headless_layout.addWidget(self.headless_checkbox)
        advanced_layout.addLayout(headless_layout)
        
        advanced_group.setLayout(advanced_layout)
        settings_tab_layout.addWidget(advanced_group)
        
        # 設定タブのボタン
        settings_button_layout = QHBoxLayout()
        
        # 設定保存ボタン
        settings_save_button = QPushButton("設定を保存")
        settings_save_button.clicked.connect(self.save_settings)
        settings_button_layout.addWidget(settings_save_button)
        
        # 設定リセットボタン
        settings_reset_button = QPushButton("設定をリセット")
        settings_reset_button.clicked.connect(self.reset_settings)
        settings_button_layout.addWidget(settings_reset_button)
        
        settings_tab_layout.addLayout(settings_button_layout)
        
        # タブにレイアウトを設定
        main_tab.setLayout(main_tab_layout)
        settings_tab.setLayout(settings_tab_layout)
        
        # タブをタブウィジェットに追加
        self.tab_widget.addTab(main_tab, "メイン")
        self.tab_widget.addTab(settings_tab, "設定")
        
        # メインレイアウトにタブウィジェットを追加
        main_layout.addWidget(self.tab_widget)
        
        # ウィジェットにメインレイアウトを設定
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # 設定を読み込む
        self.load_settings()
    
    def load_settings(self):
        """設定を読み込む"""
        config = self.config_manager.load_config()
        
        # 基本設定の読み込み
        self.url_input.setText(config.get("url", ""))
        self.user_id_input.setText(config.get("user_id", ""))
        self.password_input.setText(config.get("password", ""))
        
        # セレクタ設定の読み込み
        selectors = config.get("selectors", {})
        for key, input_field in self.selector_inputs.items():
            input_field.setText(selectors.get(key, ""))
            
        # 詳細設定の読み込み
        advanced = config.get("advanced", {})
        
        # 自動退勤設定
        auto_end = advanced.get("auto_end", {})
        auto_end_enabled = auto_end.get("enabled", False)
        auto_end_time = auto_end.get("time", "18:00")
        self.auto_end_checkbox.setChecked(auto_end_enabled)
        
        try:
            hours, minutes = map(int, auto_end_time.split(":"))
            self.auto_end_time_edit.setTime(QTime(hours, minutes))
        except (ValueError, AttributeError):
            # デフォルト値を設定
            self.auto_end_time_edit.setTime(QTime(18, 0))
            
        # ヘッドレスモード設定
        headless_mode = advanced.get("headless_mode", True)
        self.headless_checkbox.setChecked(headless_mode)
    
    def save_settings(self):
        """設定を保存する"""
        # 基本設定の取得
        url = self.url_input.text().strip()
        user_id = self.user_id_input.text().strip()
        password = self.password_input.text()
        
        # セレクタ設定の取得
        selectors = {}
        for key, input_field in self.selector_inputs.items():
            value = input_field.text().strip()
            if value:
                selectors[key] = value
                
        # 詳細設定の取得
        advanced = {}
        
        # 自動退勤設定
        auto_end = {
            "enabled": self.auto_end_checkbox.isChecked(),
            "time": self.auto_end_time_edit.time().toString("HH:mm")
        }
        advanced["auto_end"] = auto_end
        
        # ヘッドレスモード設定
        advanced["headless_mode"] = self.headless_checkbox.isChecked()
        
        # 設定を保存
        self.config_manager.save_config(url, user_id, password, selectors, advanced)
        
        # Web打刻ハンドラのセレクタを更新
        if self.web_dakoku:
            self.web_dakoku._load_selectors()
            
        QMessageBox.information(self, "設定保存", "設定を保存しました")
    
    def reset_settings(self):
        """設定をリセットする"""
        reply = QMessageBox.question(
            self, 
            "設定リセット", 
            "すべての設定をリセットしますか？\nこの操作は元に戻せません。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 設定ファイルをリセット
            self.config_manager.reset_config()
            
            # UI要素をクリア
            self.url_input.clear()
            self.user_id_input.clear()
            self.password_input.clear()
            
            for input_field in self.selector_inputs.values():
                input_field.clear()
                
            # 詳細設定をデフォルトに戻す
            self.auto_end_checkbox.setChecked(False)
            self.auto_end_time_edit.setTime(QTime(18, 0))
            self.headless_checkbox.setChecked(True)
            
            QMessageBox.information(self, "設定リセット", "設定をリセットしました")
    
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
            QMessageBox.information(self, "テスト接続成功", "テスト接続を開始します。\nこの処理には時間がかかる場合があります。")
            
            # 別スレッドでテスト接続を実行
            def run_test():
                error_message = None
                driver = None
                
                try:
                    # WebDriverのセットアップ
                    driver = self.web_dakoku._setup_driver()
                    if not driver:
                        # ログからエラーメッセージを取得
                        try:
                            with open('web_dakoku.log', 'r', encoding='utf-8') as f:
                                log_lines = f.readlines()
                                # 最新の10行を取得
                                recent_logs = ''.join(log_lines[-10:])
                        except Exception as e:
                            recent_logs = f"ログファイルの読み込みに失敗しました: {e}"
                        
                        error_message = f"WebDriverの初期化に失敗しました。\n\nエラーログ:\n{recent_logs}"
                        
                        # ChromeDriverのインストール方法を案内
                        error_message += "\n\n【解決方法】\n"
                        error_message += "1. ChromeDriverを手動でダウンロードしてください。\n"
                        error_message += "   https://chromedriver.chromium.org/downloads\n"
                        error_message += "2. ダウンロードしたchromedriver.exeをプログラムと同じフォルダに配置してください。\n"
                        error_message += "3. または、--headless=newオプションを無効化してみてください。"
                        return
                    
                    # ログイン処理
                    success = self.web_dakoku._login(driver)
                    if success:
                        QMessageBox.information(self, "テスト接続成功", "Web打刻システムへの接続に成功しました")
                    else:
                        # ログからエラーメッセージを取得
                        try:
                            with open('web_dakoku.log', 'r', encoding='utf-8') as f:
                                log_lines = f.readlines()
                                # 最新の15行を取得
                                recent_logs = ''.join(log_lines[-15:])
                        except Exception as e:
                            recent_logs = f"ログファイルの読み込みに失敗しました: {e}"
                        
                        error_message = f"Web打刻システムへの接続に失敗しました\n設定を確認してください\n\nエラーログ:\n{recent_logs}"
                        
                        # セレクタ設定の確認を促す
                        error_message += "\n\n【確認ポイント】\n"
                        error_message += "1. URLが正しいか確認してください\n"
                        error_message += "2. ユーザーIDとパスワードが正しいか確認してください\n"
                        error_message += "3. 各セレクタ設定が実際のWeb要素IDと一致しているか確認してください"
                except Exception as e:
                    error_message = f"テスト接続中に予期せぬエラーが発生しました: {e}"
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except Exception:
                            pass
                    
                    if error_message:
                        QMessageBox.warning(self, "テスト接続失敗", error_message)
            
            threading.Thread(target=run_test).start()
    
    def show_selector_help(self, selector_key):
        """セレクタのヘルプを表示する"""
        help_texts = {
            "user_id_selector": (
                "ユーザーIDセレクタの設定方法",
                "ユーザーID入力フィールドのID属性を指定します。\n\n"
                "例: <input id=\"user_id\" name=\"username\" type=\"text\">\n"
                "この場合、「user_id」と入力してください。\n\n"
                "ID属性がない場合は、開発者ツールを使用して要素を特定してください。\n"
                "1. ログインページで右クリック→「検証」をクリック\n"
                "2. ユーザーID入力フィールドを特定\n"
                "3. その要素のID属性を確認"
            ),
            "password_selector": (
                "パスワードセレクタの設定方法",
                "パスワード入力フィールドのID属性を指定します。\n\n"
                "例: <input id=\"password\" name=\"password\" type=\"password\">\n"
                "この場合、「password」と入力してください。\n\n"
                "ID属性がない場合は、開発者ツールを使用して要素を特定してください。"
            ),
            "login_button_selector": (
                "ログインボタンセレクタの設定方法",
                "ログインボタンのID属性を指定します。\n\n"
                "例: <button id=\"login_button\" type=\"submit\">ログイン</button>\n"
                "この場合、「login_button」と入力してください。\n\n"
                "ID属性がない場合は、開発者ツールを使用して要素を特定してください。"
            ),
            "success_element_selector": (
                "ログイン成功要素セレクタの設定方法",
                "ログイン成功時に表示される要素のID属性を指定します。\n"
                "これはログイン成功を判断するために使用されます。\n\n"
                "例: ログイン後のダッシュボードに <div id=\"dashboard\"> がある場合、\n"
                "「dashboard」と入力してください。\n\n"
                "この設定は省略可能です。省略した場合、URLの変化でログイン成功を判断します。"
            ),
            "start_button_selector": (
                "出勤ボタンセレクタの設定方法",
                "出勤ボタンのID属性を指定します。\n\n"
                "例: <button id=\"start_work\">出勤</button>\n"
                "この場合、「start_work」と入力してください。\n\n"
                "ID属性がない場合は、開発者ツールを使用して要素を特定してください。"
            ),
            "end_button_selector": (
                "退勤ボタンセレクタの設定方法",
                "退勤ボタンのID属性を指定します。\n\n"
                "例: <button id=\"end_work\">退勤</button>\n"
                "この場合、「end_work」と入力してください。\n\n"
                "ID属性がない場合は、開発者ツールを使用して要素を特定してください。"
            )
        }
        
        title, text = help_texts.get(selector_key, ("ヘルプ", "このセレクタに関する情報はありません。"))
        QMessageBox.information(self, title, text)


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""
    
    def __init__(self):
        """初期化"""
        super().__init__()
        
        # 設定マネージャーの初期化
        self.config_manager = ConfigManager("config.json")
        
        # Web打刻ハンドラの初期化
        self.web_dakoku = WebDakoku(self.config_manager)
        
        # 自動退勤タイマー
        self.auto_end_timer = QTimer(self)
        self.auto_end_timer.timeout.connect(self.check_auto_end)
        self.auto_end_timer.start(60000)  # 1分ごとにチェック
        
        # UIのセットアップ
        self.setup_ui()
        
    def setup_ui(self):
        """UIのセットアップ"""
        # ... 既存のコード ...


def main():
    app = DakokuApp(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 