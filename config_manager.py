#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self):
        # 設定ファイルのパス
        self.config_dir = Path.home() / ".web_dakoku"
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / "key.bin"
        
        # 設定ディレクトリの作成
        self.config_dir.mkdir(exist_ok=True)
        
        # 暗号化キーの取得または生成
        self.encryption_key = self._get_or_create_key()
        
        # Fernetインスタンスの作成
        self.fernet = Fernet(self.encryption_key)
        
        # デフォルトのセレクタ設定
        self.default_selectors = {
            "user_id_input": "user_id",
            "password_input": "password",
            "login_button": "login_button",
            "dakoku_panel": "dakoku_panel",
            "clock_in_button": "clock_in_button",
            "clock_out_button": "clock_out_button",
            "confirm_button": "confirm_button",
            "success_message": "success_message"
        }
    
    def _get_or_create_key(self):
        """暗号化キーの取得または生成"""
        if self.key_file.exists():
            # 既存のキーを読み込む
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            # 新しいキーを生成
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key
    
    def is_configured(self):
        """設定が完了しているかどうかを確認"""
        if not self.config_file.exists():
            return False
        
        config = self.get_config()
        return all(key in config for key in ["url", "user_id", "password"])
    
    def get_config(self):
        """設定の取得"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # パスワードの復号化
            if "password" in config and config["password"]:
                encrypted_password = config["password"].encode("utf-8")
                decrypted_password = self.fernet.decrypt(base64.b64decode(encrypted_password)).decode("utf-8")
                config["password"] = decrypted_password
            
            # セレクタ設定がない場合はデフォルト値を使用
            if "selectors" not in config:
                config["selectors"] = self.default_selectors
            
            return config
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            return {}
    
    def save_config(self, url, user_id, password, selectors=None):
        """設定の保存"""
        # パスワードの暗号化
        encrypted_password = base64.b64encode(
            self.fernet.encrypt(password.encode("utf-8"))
        ).decode("utf-8")
        
        # 現在の設定を取得
        current_config = self.get_config()
        
        # 新しい設定
        config = {
            "url": url,
            "user_id": user_id,
            "password": encrypted_password,
            "selectors": selectors if selectors else current_config.get("selectors", self.default_selectors)
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定ファイルの保存エラー: {e}")
            return False
    
    def save_selectors(self, selectors):
        """セレクタ設定のみを保存"""
        current_config = self.get_config()
        
        # 現在のURL、ユーザーID、パスワードを取得
        url = current_config.get("url", "")
        user_id = current_config.get("user_id", "")
        password = current_config.get("password", "")
        
        # パスワードが復号化されている場合は再暗号化
        if password and not password.startswith("gAAAAA"):
            encrypted_password = base64.b64encode(
                self.fernet.encrypt(password.encode("utf-8"))
            ).decode("utf-8")
        else:
            encrypted_password = password
        
        # 設定を更新
        config = {
            "url": url,
            "user_id": user_id,
            "password": encrypted_password,
            "selectors": selectors
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定ファイルの保存エラー: {e}")
            return False 