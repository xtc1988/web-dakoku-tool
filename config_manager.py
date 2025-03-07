#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import base64
import logging
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ConfigManager:
    """設定ファイルの管理クラス"""
    
    def __init__(self, config_file="config.json"):
        """初期化"""
        self.config_file = config_file
        self.encryption_key = self._generate_key()
        
    def _generate_key(self):
        """暗号化キーの生成"""
        try:
            # マシン固有の情報を使用してキーを生成
            machine_id = self._get_machine_id()
            
            # PBKDF2を使用してキーを導出
            salt = b'web_dakoku_salt'  # 固定のソルト
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            return key
        except Exception as e:
            logging.error(f"暗号化キーの生成に失敗しました: {e}")
            # フォールバックキー（固定）
            return base64.urlsafe_b64encode(b'web_dakoku_fallback_key_12345678901234')
            
    def _get_machine_id(self):
        """マシン固有のIDを取得"""
        try:
            # Windowsの場合
            if os.name == 'nt':
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Cryptography")
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                return machine_guid
            # Linuxの場合
            elif os.name == 'posix':
                try:
                    with open('/etc/machine-id', 'r') as f:
                        return f.read().strip()
                except:
                    with open('/var/lib/dbus/machine-id', 'r') as f:
                        return f.read().strip()
            # macOSの場合
            elif os.name == 'darwin':
                import subprocess
                output = subprocess.check_output(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'])
                for line in output.splitlines():
                    if b'IOPlatformUUID' in line:
                        return line.split(b'"')[-2].decode()
        except Exception as e:
            logging.error(f"マシンIDの取得に失敗しました: {e}")
            
        # フォールバックID
        return "web_dakoku_fallback_id"
        
    def _encrypt(self, data):
        """データの暗号化"""
        try:
            f = Fernet(self.encryption_key)
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            logging.error(f"データの暗号化に失敗しました: {e}")
            return ""
            
    def _decrypt(self, encrypted_data):
        """データの復号化"""
        try:
            f = Fernet(self.encryption_key)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logging.error(f"データの復号化に失敗しました: {e}")
            return ""
            
    def load_config(self):
        """設定の読み込み"""
        try:
            if not os.path.exists(self.config_file):
                return {}
                
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # パスワードの復号化
            if "password" in config and config["password"]:
                try:
                    config["password"] = self._decrypt(config["password"])
                except Exception as e:
                    logging.error(f"パスワードの復号化に失敗しました: {e}")
                    config["password"] = ""
                    
            return config
        except Exception as e:
            logging.error(f"設定ファイルの読み込みに失敗しました: {e}")
            return {}
            
    def save_config(self, url, user_id, password, selectors, advanced=None):
        """設定の保存"""
        try:
            # パスワードの暗号化
            encrypted_password = self._encrypt(password) if password else ""
            
            # 設定の構築
            config = {
                "url": url,
                "user_id": user_id,
                "password": encrypted_password,
                "selectors": selectors
            }
            
            # 詳細設定の追加
            if advanced:
                config["advanced"] = advanced
                
            # 設定ファイルの保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            return True
        except Exception as e:
            logging.error(f"設定ファイルの保存に失敗しました: {e}")
            return False
            
    def reset_config(self):
        """設定のリセット"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            return True
        except Exception as e:
            logging.error(f"設定ファイルのリセットに失敗しました: {e}")
            return False

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
                try:
                    encrypted_password = config["password"].encode("utf-8")
                    decrypted_password = self._decrypt(encrypted_password)
                    config["password"] = decrypted_password
                except Exception as e:
                    print(f"パスワードの復号化エラー: {e}")
                    # 復号化に失敗した場合は空のパスワードを設定
                    config["password"] = ""
            
            # セレクタ設定がない場合はデフォルト値を使用
            if "selectors" not in config:
                config["selectors"] = self.default_selectors
            
            return config
        except Exception as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            return {}
    
    def save_selectors(self, selectors):
        """セレクタ設定のみを保存"""
        current_config = self.get_config()
        
        # 現在のURL、ユーザーID、パスワードを取得
        url = current_config.get("url", "")
        user_id = current_config.get("user_id", "")
        password = current_config.get("password", "")
        
        # パスワードが復号化されている場合は再暗号化
        if password and not password.startswith("gAAAAA"):
            encrypted_password = self._encrypt(password)
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