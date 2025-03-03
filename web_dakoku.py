#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='web_dakoku.log'
)
logger = logging.getLogger('web_dakoku')

class WebDakoku:
    """Web打刻ハンドラクラス"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.driver = None
        self.selectors = {}
        self._load_selectors()
    
    def _load_selectors(self):
        """セレクタ設定の読み込み"""
        config = self.config_manager.get_config()
        self.selectors = config.get("selectors", {})
    
    def _setup_driver(self):
        """WebDriverのセットアップ"""
        try:
            # Chromeオプションの設定
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # ヘッドレスモード
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # WebDriverのセットアップ
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)
            
            return driver
        except Exception as e:
            logger.error(f"WebDriverのセットアップエラー: {e}")
            return None
    
    def _login(self, driver):
        """ログイン処理"""
        try:
            # 設定の取得
            config = self.config_manager.get_config()
            url = config.get("url", "")
            user_id = config.get("user_id", "")
            password = config.get("password", "")
            
            if not url or not user_id or not password:
                logger.error("設定が不完全です")
                return False
            
            # ログインページにアクセス
            logger.info(f"ログインページにアクセス: {url}")
            driver.get(url)
            
            # ログインフォームの入力
            try:
                # ユーザーIDの入力
                user_id_selector = self.selectors.get("user_id_input", "user_id")
                logger.info(f"ユーザーID入力フィールドを検索: セレクタ={user_id_selector}")
                id_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, user_id_selector))
                )
                id_input.clear()
                id_input.send_keys(user_id)
                logger.info("ユーザーIDを入力しました")
                
                # パスワードの入力
                password_selector = self.selectors.get("password_input", "password")
                logger.info(f"パスワード入力フィールドを検索: セレクタ={password_selector}")
                try:
                    password_input = driver.find_element(By.ID, password_selector)
                    password_input.clear()
                    password_input.send_keys(password)
                    logger.info("パスワードを入力しました")
                except Exception as e:
                    logger.error(f"パスワード入力フィールドの検索に失敗しました: {e}")
                    return False
                
                # ログインボタンのクリック
                login_button_selector = self.selectors.get("login_button", "login_button")
                logger.info(f"ログインボタンを検索: セレクタ={login_button_selector}")
                try:
                    login_button = driver.find_element(By.ID, login_button_selector)
                    login_button.click()
                    logger.info("ログインボタンをクリックしました")
                except Exception as e:
                    logger.error(f"ログインボタンの検索に失敗しました: {e}")
                    return False
                
                # ログイン成功の確認
                dakoku_panel_selector = self.selectors.get("dakoku_panel", "dakoku_panel")
                logger.info(f"打刻パネルを検索: セレクタ={dakoku_panel_selector}")
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, dakoku_panel_selector))
                    )
                    logger.info("ログインに成功しました")
                    return True
                except TimeoutException:
                    logger.error(f"打刻パネルが見つかりませんでした。ログインに失敗した可能性があります。")
                    # ページのHTMLソースを記録（デバッグ用）
                    logger.debug(f"ページのHTML: {driver.page_source[:1000]}...")
                    return False
                except Exception as e:
                    logger.error(f"打刻パネルの検索中にエラーが発生しました: {e}")
                    return False
            except TimeoutException:
                logger.error("ログイン処理がタイムアウトしました")
                return False
            except Exception as e:
                logger.error(f"ログイン処理中にエラーが発生しました: {e}")
                return False
        except Exception as e:
            logger.error(f"ログイン処理中にエラーが発生しました: {e}")
            return False
    
    def clock_in(self):
        """出勤打刻"""
        try:
            driver = self._setup_driver()
            if not driver:
                return False
            
            try:
                # ログイン
                if not self._login(driver):
                    driver.quit()
                    return False
                
                # 出勤打刻ボタンのクリック
                clock_in_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, self.selectors.get("clock_in_button", "clock_in_button")))
                )
                clock_in_button.click()
                
                # 打刻確認ダイアログの処理
                try:
                    confirm_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, self.selectors.get("confirm_button", "confirm_button")))
                    )
                    confirm_button.click()
                except TimeoutException:
                    # 確認ダイアログがない場合は無視
                    pass
                
                # 打刻成功の確認
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, self.selectors.get("success_message", "success_message")))
                )
                
                logger.info("出勤打刻が完了しました")
                return True
            finally:
                driver.quit()
        except Exception as e:
            logger.error(f"出勤打刻中にエラーが発生しました: {e}")
            return False
    
    def clock_out(self):
        """退勤打刻"""
        try:
            driver = self._setup_driver()
            if not driver:
                return False
            
            try:
                # ログイン
                if not self._login(driver):
                    driver.quit()
                    return False
                
                # 退勤打刻ボタンのクリック
                clock_out_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, self.selectors.get("clock_out_button", "clock_out_button")))
                )
                clock_out_button.click()
                
                # 打刻確認ダイアログの処理
                try:
                    confirm_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, self.selectors.get("confirm_button", "confirm_button")))
                    )
                    confirm_button.click()
                except TimeoutException:
                    # 確認ダイアログがない場合は無視
                    pass
                
                # 打刻成功の確認
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, self.selectors.get("success_message", "success_message")))
                )
                
                logger.info("退勤打刻が完了しました")
                return True
            finally:
                driver.quit()
        except Exception as e:
            logger.error(f"退勤打刻中にエラーが発生しました: {e}")
            return False 