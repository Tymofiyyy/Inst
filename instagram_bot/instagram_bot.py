#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram UI Automation Bot
Автоматизація дій в Instagram з обходом систем захисту
"""

# Фікс для ChromeDriver та рекурсії
import os
import sys
os.environ['WDM_ARCH'] = 'win64' if os.name == 'nt' else 'linux64'
os.environ['WDM_LOG_LEVEL'] = '0'
sys.setrecursionlimit(1000)  # Обмеження рекурсії

import random
import time
import json
import logging
import platform
import subprocess
import tempfile
import zipfile
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import threading


class AntiDetectionManager:
    """Менеджер для обходу систем детекції ботів"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ]
        
        self.screen_resolutions = [
            (360, 640), (375, 667), (414, 736), (412, 869), (360, 780)
        ]
        
        self.proxy_list = []
        self.current_proxy_index = 0
        
    def get_random_user_agent(self) -> str:
        """Отримання випадкового User-Agent"""
        return random.choice(self.user_agents)
    
    def get_random_resolution(self) -> tuple:
        """Отримання випадкової роздільної здатності"""
        return random.choice(self.screen_resolutions)
    
    def get_next_proxy(self) -> Optional[str]:
        """Отримання наступного проксі"""
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy
    
    def add_proxy(self, proxy: str):
        """Додавання проксі до списку"""
        self.proxy_list.append(proxy)
    
    def human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Затримка, що імітує людську поведінку"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def random_scroll(self, driver):
        """Випадкове прокручування для імітації людської поведінки"""
        try:
            actions = ActionChains(driver)
            for _ in range(random.randint(1, 3)):
                actions.scroll_by_amount(0, random.randint(-200, 200))
                actions.perform()
                time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logging.debug(f"Помилка прокручування: {e}")


class CaptchaSolver:
    """Розв'язувач капчі"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.solving_services = {
            '2captcha': 'http://2captcha.com',
            'anticaptcha': 'https://api.anti-captcha.com',
            'rucaptcha': 'https://rucaptcha.com'
        }
    
    def solve_recaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """Розв'язання reCAPTCHA"""
        if not self.api_key:
            logging.warning("API ключ капчі не встановлений")
            return None
        
        try:
            # Відправка капчі на розв'язання
            submit_url = f"{self.solving_services['2captcha']}/in.php"
            data = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url
            }
            
            response = requests.post(submit_url, data=data, timeout=30)
            if response.text.startswith('OK|'):
                captcha_id = response.text.split('|')[1]
                
                # Очікування розв'язання
                result_url = f"{self.solving_services['2captcha']}/res.php"
                for _ in range(60):  # Очікування до 5 хвилин
                    time.sleep(5)
                    result = requests.get(result_url, params={
                        'key': self.api_key,
                        'action': 'get',
                        'id': captcha_id
                    }, timeout=30)
                    
                    if result.text.startswith('OK|'):
                        return result.text.split('|')[1]
                    elif result.text == 'CAPCHA_NOT_READY':
                        continue
                    else:
                        break
        except Exception as e:
            logging.error(f"Помилка розв'язання капчі: {e}")
        
        return None


class AccountManager:
    """Менеджер акаунтів Instagram"""
    
    def __init__(self):
        self.accounts = {}
        self.active_sessions = {}
        self.account_status = {}
        self.session_data_file = 'account_sessions.json'
        self.load_accounts()
    
    def add_account(self, username: str, password: str, proxy: str = None):
        """Додавання нового акаунту"""
        self.accounts[username] = {
            'password': password,
            'proxy': proxy,
            'last_activity': None,
            'actions_count': 0,
            'daily_limit': 100,
            'status': 'active'
        }
        self.save_accounts()
        logging.info(f"Додано акаунт: {username}")
    
    def remove_account(self, username: str):
        """Видалення акаунту"""
        if username in self.accounts:
            del self.accounts[username]
            if username in self.active_sessions:
                del self.active_sessions[username]
            self.save_accounts()
            logging.info(f"Видалено акаунт: {username}")
    
    def get_account_info(self, username: str) -> Dict:
        """Отримання інформації про акаунт"""
        return self.accounts.get(username, {})
    
    def update_account_status(self, username: str, status: str):
        """Оновлення статусу акаунту"""
        if username in self.accounts:
            self.accounts[username]['status'] = status
            self.accounts[username]['last_activity'] = datetime.now().isoformat()
            self.save_accounts()
            logging.info(f"Оновлено статус {username}: {status}")
    
    def is_account_available(self, username: str) -> bool:
        """Перевірка доступності акаунту"""
        account = self.accounts.get(username)
        if not account:
            return False
        
        # Перевірка статусу
        if account['status'] in ['banned', 'shadowban', 'suspended']:
            return False
        
        # Перевірка лімітів
        if account['actions_count'] >= account['daily_limit']:
            return False
        
        return True
    
    def increment_actions(self, username: str):
        """Збільшення лічильника дій"""
        if username in self.accounts:
            self.accounts[username]['actions_count'] += 1
            self.accounts[username]['last_activity'] = datetime.now().isoformat()
            self.save_accounts()
    
    def reset_daily_limits(self):
        """Скидання денних лімітів"""
        for username in self.accounts:
            self.accounts[username]['actions_count'] = 0
        self.save_accounts()
        logging.info("Скинуто денні ліміти для всіх акаунтів")
    
    def save_accounts(self):
        """Збереження даних акаунтів"""
        try:
            with open(self.session_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Помилка збереження акаунтів: {e}")
    
    def load_accounts(self):
        """Завантаження даних акаунтів"""
        try:
            if os.path.exists(self.session_data_file):
                with open(self.session_data_file, 'r', encoding='utf-8') as f:
                    self.accounts = json.load(f)
                logging.info(f"Завантажено {len(self.accounts)} акаунтів")
        except FileNotFoundError:
            self.accounts = {}
        except Exception as e:
            logging.error(f"Помилка завантаження акаунтів: {e}")
            self.accounts = {}


class InstagramBot:
    """Основний клас бота Instagram"""
    
    def __init__(self, captcha_api_key: str = None):
        self.anti_detection = AntiDetectionManager()
        self.captcha_solver = CaptchaSolver(captcha_api_key)
        self.account_manager = AccountManager()
        self.drivers = {}
        self.setup_logging()
        
        # Налаштування для обходу детекції
        self.action_delays = {
            'like': (3, 8),
            'comment': (5, 12),
            'follow': (8, 15),
            'story_view': (2, 5),
            'story_reply': (4, 10),
            'page_load': (5, 10),
            'human_pause': (1, 3)
        }
        
        # Шаблони відповідей для сторіс
        self.story_replies = [
            "🔥🔥🔥", "❤️", "Круто!", "👍", "Супер!", 
            "💯", "🙌", "Класно!", "👏", "Wow!",
            "Дуже цікаво!", "Топ контент!", "Красиво!",
            "🤗", "😊", "👌", "🔝", "💪", "🌟", "✨", "🙏", "💝", "🎈",
            "Nice", "Cool", "Great", "Amazing", "Awesome", "Perfect",
            "Love it", "So good", "Fantastic", "Incredible", "Beautiful"
        ]
        
        # Налаштування для розпізнавання shadowban
        self.shadowban_indicators = [
            "your account has been restricted",
            "temporarily blocked",
            "unusual activity",
            "violating community guidelines",
            "action blocked",
            "action has been blocked",
            "we restrict certain activity",
            "help us keep instagram safe",
            "this feature isn't available right now"
        ]
    
    def setup_logging(self):
        """Налаштування логування"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('instagram_bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def get_chrome_version(self) -> str:
        """Отримання версії Chrome"""
        try:
            if platform.system() == "Windows":
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                       r"Software\Google\Chrome\BLBeacon")
                    version, _ = winreg.QueryValueEx(key, "version")
                    return version
                except Exception:
                    try:
                        result = subprocess.run(['reg', 'query', 
                                               'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', 
                                               '/v', 'version'], 
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            for line in result.stdout.split('\n'):
                                if 'version' in line:
                                    return line.split()[-1]
                    except Exception:
                        pass
                    
                    chrome_paths = [
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
                    ]
                    
                    for chrome_path in chrome_paths:
                        if os.path.exists(chrome_path):
                            try:
                                result = subprocess.run([chrome_path, '--version'], 
                                                      capture_output=True, text=True, timeout=10)
                                return result.stdout.strip().split()[-1]
                            except Exception:
                                continue
            else:
                try:
                    result = subprocess.run(['google-chrome', '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    return result.stdout.strip().split()[-1]
                except Exception:
                    try:
                        result = subprocess.run(['chromium-browser', '--version'], 
                                              capture_output=True, text=True, timeout=10)
                        return result.stdout.strip().split()[-1]
                    except Exception:
                        pass
        except Exception as e:
            logging.debug(f"Помилка отримання версії Chrome: {e}")
        
        return "137.0.7151"
    
    def download_correct_chromedriver(self) -> Optional[str]:
        """Ручне завантаження правильного ChromeDriver"""
        try:
            chrome_version = self.get_chrome_version()
            logging.info(f"Завантаження ChromeDriver для Chrome {chrome_version}")
            
            system = platform.system()
            machine = platform.machine()
            
            if system == "Windows":
                if machine.endswith('64'):
                    platform_name = "win64"
                    filename = "chromedriver-win64.zip"
                    executable_name = "chromedriver.exe"
                else:
                    platform_name = "win32"
                    filename = "chromedriver-win32.zip"
                    executable_name = "chromedriver.exe"
            elif system == "Linux":
                if machine.endswith('64'):
                    platform_name = "linux64"
                    filename = "chromedriver-linux64.zip"
                else:
                    platform_name = "linux32"
                    filename = "chromedriver-linux32.zip"
                executable_name = "chromedriver"
            elif system == "Darwin":
                if machine == "arm64":
                    platform_name = "mac-arm64"
                    filename = "chromedriver-mac-arm64.zip"
                else:
                    platform_name = "mac-x64"
                    filename = "chromedriver-mac-x64.zip"
                executable_name = "chromedriver"
            else:
                logging.error(f"Непідтримувана платформа: {system} {machine}")
                return None
            
            base_url = "https://storage.googleapis.com/chrome-for-testing-public"
            download_url = f"{base_url}/{chrome_version}/{platform_name}/{filename}"
            
            logging.info(f"Завантаження з: {download_url}")
            
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, filename)
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == executable_name or (file.startswith('chromedriver') and 
                                                 (file.endswith('.exe') or system != "Windows")):
                        driver_path = os.path.join(root, file)
                        
                        permanent_dir = os.path.join(os.path.expanduser('~'), '.chromedriver')
                        os.makedirs(permanent_dir, exist_ok=True)
                        permanent_path = os.path.join(permanent_dir, executable_name)
                        
                        shutil.copy2(driver_path, permanent_path)
                        
                        if system != "Windows":
                            os.chmod(permanent_path, 0o755)
                        
                        logging.info(f"ChromeDriver збережено: {permanent_path}")
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        
                        return permanent_path
            
            logging.error("Не знайдено виконуваний файл ChromeDriver в архіві")
            return None
            
        except Exception as e:
            logging.error(f"Помилка завантаження ChromeDriver: {e}")
            return None
    
    def create_driver(self, username: str) -> webdriver.Chrome:
        """Створення драйвера з покращеним обходом детекції"""
        options = Options()
        
        # Покращені налаштування для обходу детекції
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--no-first-run")
        options.add_argument("--no-service-autorun")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--password-store=basic")
        options.add_argument("--use-mock-keychain")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-domain-reliability")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-field-trial-config")
        options.add_argument("--disable-back-forward-cache")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-sync")
        
        # Реалістичний User-Agent
        user_agent = self.anti_detection.get_random_user_agent()
        options.add_argument(f"--user-agent={user_agent}")
        
        # Мобільна емуляція
        width, height = self.anti_detection.get_random_resolution()
        mobile_emulation = {
            "deviceMetrics": {
                "width": width,
                "height": height,
                "pixelRatio": random.uniform(2.0, 3.0)
            },
            "userAgent": user_agent
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        # Налаштування для обходу детекції
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.plugins": 1,
            "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
            "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
            "PluginsAllowedForUrls": ["https://www.instagram.com"],
            "PluginsBlockedForUrls": [],
        }
        options.add_experimental_option("prefs", prefs)
        
        # Проксі
        account_info = self.account_manager.get_account_info(username)
        if account_info.get('proxy'):
            options.add_argument(f"--proxy-server={account_info['proxy']}")
        
        driver = None
        last_error = None
        
        # Спроба 1: webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            
            wdm_cache = os.path.expanduser('~/.wdm')
            if os.path.exists(wdm_cache):
                shutil.rmtree(wdm_cache, ignore_errors=True)
            
            manager = ChromeDriverManager()
            driver_path = manager.install()
            
            if os.path.exists(driver_path):
                if platform.system() == "Windows" and not driver_path.endswith('.exe'):
                    driver_dir = os.path.dirname(driver_path)
                    for file in os.listdir(driver_dir):
                        if file.endswith('chromedriver.exe'):
                            driver_path = os.path.join(driver_dir, file)
                            break
                
                logging.info(f"Використовується ChromeDriver: {driver_path}")
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
                
        except Exception as e:
            last_error = e
            logging.warning(f"Помилка з webdriver-manager: {e}")
        
        # Спроба 2: ручне завантаження
        if not driver:
            try:
                logging.info("Спроба ручного завантаження ChromeDriver...")
                driver_path = self.download_correct_chromedriver()
                if driver_path and os.path.exists(driver_path):
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=options)
                else:
                    raise Exception("Не вдалося завантажити ChromeDriver")
                    
            except Exception as e:
                last_error = e
                logging.warning(f"Помилка ручного завантаження: {e}")
        
        # Спроба 3: системний ChromeDriver
        if not driver:
            try:
                logging.info("Спроба використання системного ChromeDriver...")
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                
            except Exception as e:
                last_error = e
                logging.warning(f"Системний ChromeDriver недоступний: {e}")
        
        if not driver:
            error_msg = f"Критична помилка: не вдалося створити WebDriver. Остання помилка: {last_error}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        # Налаштування для обходу детекції
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.execute_cdp_cmd('Runtime.evaluate', {
                "expression": f"""
                    Object.defineProperty(navigator, 'webdriver', {{
                      get: () => undefined,
                    }});
                    
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                    delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                    
                    Object.defineProperty(navigator, 'userAgent', {{
                      get: () => '{user_agent}',
                    }});
                    
                    Object.defineProperty(navigator, 'plugins', {{
                      get: () => [1, 2, 3, 4, 5],
                    }});
                    
                    Object.defineProperty(navigator, 'languages', {{
                      get: () => ['en-US', 'en'],
                    }});
                """
            })
            
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'mobile': True,
                'width': width,
                'height': height,
                'deviceScaleFactor': random.uniform(2.0, 3.0),
            })
            
            driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
                'latitude': random.uniform(40.0, 50.0),
                'longitude': random.uniform(-5.0, 5.0),
                'accuracy': 100
            })
            
        except Exception as e:
            logging.debug(f"Помилка налаштування анти-детекції: {e}")
        
        logging.info(f"WebDriver успішно створено для {username}")
        return driver
    
    def detect_captcha(self, driver) -> bool:
        """Спрощена детекція капчі"""
        try:
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            captcha_indicators = [
                "recaptcha" in page_source,
                "captcha" in page_source,
                "challenge" in current_url,
                "verify you're human" in page_source,
                "unusual activity" in page_source,
                "security check" in page_source,
                "suspicious activity" in page_source
            ]
            
            return any(captcha_indicators)
            
        except Exception:
            return False
    
    def solve_captcha(self, driver) -> bool:
        """Спрощений обхід капчі"""
        try:
            logging.warning("Виявлено капчу, спроба обходу...")
            
            # Метод 1: перезавантаження з очищенням cookies
            try:
                driver.delete_all_cookies()
                time.sleep(2)
                driver.refresh()
                time.sleep(5)
                
                if not self.detect_captcha(driver):
                    logging.info("Капча обійдена через перезавантаження")
                    return True
            except:
                pass
            
            # Метод 2: закриття попапів
            try:
                close_selectors = ["button[aria-label='Close']", "svg[aria-label='Close']"]
                for selector in close_selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            time.sleep(2)
                            if not self.detect_captcha(driver):
                                logging.info("Капча обійдена через закриття")
                                return True
            except:
                pass
            
            # Метод 3: повернення назад
            try:
                driver.back()
                time.sleep(3)
                if not self.detect_captcha(driver):
                    logging.info("Капча обійдена через повернення назад")
                    return True
            except:
                pass
            
            logging.error("Не вдалося обійти капчу автоматично")
            return False
                
        except Exception as e:
            logging.error(f"Помилка обходу капчі: {e}")
            return False
    
    def login_account(self, username: str) -> bool:
        """Вхід в акаунт без рекурсії"""
        try:
            # Перевірка, чи акаунт вже залогінений
            if username in self.drivers:
                try:
                    self.drivers[username].current_url
                    return True
                except:
                    del self.drivers[username]
            
            account_info = self.account_manager.get_account_info(username)
            if not account_info:
                logging.error(f"Акаунт {username} не знайдено")
                return False
            
            logging.info(f"Спроба входу для акаунту: {username}")
            
            # Створення нового драйвера
            try:
                driver = self.create_driver(username)
                self.drivers[username] = driver
            except Exception as e:
                logging.error(f"Помилка створення драйвера: {e}")
                return False
            
            driver = self.drivers[username]
            
            # Перехід на головну сторінку Instagram
            try:
                driver.get("https://www.instagram.com/")
                time.sleep(random.uniform(3, 5))
                
                # Перевірка на капчу на головній сторінці
                if self.detect_captcha(driver):
                    logging.warning("Капча на головній сторінці")
                    if not self.solve_captcha(driver):
                        logging.error("Не вдалося обійти капчу на головній сторінці")
                        return False
                        
            except Exception as e:
                logging.error(f"Помилка завантаження головної сторінки: {e}")
                return False
            
            # Перехід на сторінку входу
            try:
                driver.get("https://www.instagram.com/accounts/login/")
                time.sleep(random.uniform(5, 8))
                
                # Перевірка на капчу на сторінці входу
                if self.detect_captcha(driver):
                    logging.warning("Капча на сторінці входу")
                    if not self.solve_captcha(driver):
                        logging.error("Не вдалося обійти капчу на сторінці входу")
                        return False
                        
            except Exception as e:
                logging.error(f"Помилка завантаження сторінки входу: {e}")
                return False
            
            # Пошук поля username
            username_field = None
            username_selectors = [
                "input[name='username']",
                "input[aria-label*='username']",
                "input[aria-label*='Phone number']",
                "input[type='text']"
            ]
            
            for selector in username_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            username_field = element
                            break
                    if username_field:
                        break
                except:
                    continue
            
            if not username_field:
                logging.error("Не знайдено поле для введення логіна")
                return False
            
            # Введення username
            try:
                username_field.clear()
                time.sleep(0.5)
                for char in username:
                    username_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.2))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.error(f"Помилка введення логіна: {e}")
                return False
            
            # Пошук поля password
            password_field = None
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[aria-label*='Password']"
            ]
            
            for selector in password_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            password_field = element
                            break
                    if password_field:
                        break
                except:
                    continue
            
            if not password_field:
                logging.error("Не знайдено поле для введення пароля")
                return False
            
            # Введення password
            try:
                password_field.clear()
                time.sleep(0.5)
                for char in account_info['password']:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.2))
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.error(f"Помилка введення пароля: {e}")
                return False
            
            # Перевірка на капчу перед входом
            if self.detect_captcha(driver):
                logging.warning("Капча перед входом")
                if not self.solve_captcha(driver):
                    logging.error("Не вдалося обійти капчу перед входом")
                    return False
            
            # Натискання кнопки входу
            login_clicked = False
            login_selectors = [
                "button[type='submit']",
                "button:contains('Log in')",
                "button:contains('Увійти')"
            ]
            
            for selector in login_selectors:
                try:
                    if ":contains(" in selector:
                        text = selector.split(":contains('")[1].split("')")[0]
                        xpath_selector = f"//button[contains(text(), '{text}')]"
                        elements = driver.find_elements(By.XPATH, xpath_selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            try:
                                element.click()
                                login_clicked = True
                                break
                            except:
                                try:
                                    driver.execute_script("arguments[0].click();", element)
                                    login_clicked = True
                                    break
                                except:
                                    continue
                    if login_clicked:
                        break
                except:
                    continue
            
            if not login_clicked:
                try:
                    password_field.send_keys(Keys.RETURN)
                    login_clicked = True
                except:
                    pass
            
            if not login_clicked:
                logging.error("Не вдалося натиснути кнопку входу")
                return False
            
            # Очікування після входу
            time.sleep(random.uniform(8, 12))
            
            # Перевірка на капчу після входу
            if self.detect_captcha(driver):
                logging.warning("Капча після входу")
                if not self.solve_captcha(driver):
                    logging.error("Не вдалося обійти капчу після входу")
                    return False
            
            # Перевірка успішного входу
            success = self.check_login_success(driver)
            
            if success:
                self.account_manager.update_account_status(username, 'active')
                logging.info(f"Успішний вхід для {username}")
                return True
            else:
                self.account_manager.update_account_status(username, 'login_failed')
                logging.error(f"Помилка входу для {username}")
                return False
                
        except Exception as e:
            logging.error(f"Критична помилка входу для {username}: {e}")
            self.account_manager.update_account_status(username, 'error')
            return False
    
    def check_login_success(self, driver) -> bool:
        """Перевірка успішного входу"""
        try:
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            
            # Негативні індикатори
            negative_indicators = [
                "sorry, your password was incorrect",
                "incorrect password",
                "неправильний пароль",
                "/accounts/login/" in current_url,
                "challenge_required" in current_url
            ]
            
            for indicator in negative_indicators:
                if indicator in page_source or indicator in current_url:
                    return False
            
            # Позитивні індикатори
            positive_indicators = [
                current_url == "https://www.instagram.com/" or current_url == "https://www.instagram.com",
                "feed" in current_url,
                "home" in page_source,
                '"viewerId"' in page_source,
                'role="main"' in page_source
            ]
            
            if any(positive_indicators):
                self.close_popups_simple(driver)
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Помилка перевірки входу: {e}")
            return False
    
    def close_popups_simple(self, driver):
        """Закриття попапів"""
        try:
            close_selectors = [
                "button[aria-label='Close']",
                "svg[aria-label='Close']",
                "button:contains('Not Now')",
                "button:contains('Не зараз')"
            ]
            
            attempts = 0
            max_attempts = 3
            
            while attempts < max_attempts:
                popup_found = False
                
                for selector in close_selectors:
                    try:
                        if ":contains(" in selector:
                            text = selector.split(":contains('")[1].split("')")[0]
                            xpath_selector = f"//*[contains(text(), '{text}')]"
                            elements = driver.find_elements(By.XPATH, xpath_selector)
                        else:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in elements:
                            if element.is_displayed():
                                try:
                                    element.click()
                                    popup_found = True
                                    time.sleep(1)
                                    break
                                except:
                                    continue
                        
                        if popup_found:
                            break
                    except:
                        continue
                
                if not popup_found:
                    break
                
                attempts += 1
                time.sleep(1)
                
        except Exception as e:
            logging.debug(f"Помилка закриття попапів: {e}")
    
    def like_last_posts(self, username: str, target_username: str, count: int = 2) -> bool:
        """Лайк останніх постів"""
        try:
            if username not in self.drivers:
                logging.error(f"Акаунт {username} не залогінений")
                return False
            
            driver = self.drivers[username]
            
            try:
                driver.current_url
            except:
                logging.error(f"Драйвер для {username} неактивний")
                return False
            
            # Перехід на профіль
            logging.info(f"Перехід на профіль {target_username}")
            try:
                driver.get(f"https://www.instagram.com/{target_username}/")
                time.sleep(random.uniform(5, 8))
            except Exception as e:
                logging.error(f"Помилка переходу на профіль: {e}")
                return False
            
            # Перевірка на приватний профіль
            page_source = driver.page_source
            if "This account is private" in page_source:
                logging.warning(f"Профіль {target_username} приватний")
                return False
            
            # Пошук постів
            post_selectors = [
                "article a[href*='/p/']",
                "a[href*='/p/']"
            ]
            
            posts = []
            for selector in post_selectors:
                try:
                    found_posts = driver.find_elements(By.CSS_SELECTOR, selector)
                    if found_posts:
                        posts = found_posts[:count]
                        break
                except:
                    continue
            
            if not posts:
                logging.warning(f"Не знайдено постів у {target_username}")
                return False
            
            success_count = 0
            
            for i, post in enumerate(posts):
                try:
                    # Прокрутка до поста
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post)
                    time.sleep(random.uniform(1, 2))
                    
                    # Відкриття поста
                    post.click()
                    time.sleep(random.uniform(3, 5))
                    
                    # Пошук кнопки лайка
                    like_selectors = [
                        "svg[aria-label='Like']",
                        "button[aria-label='Like']",
                        "span[aria-label='Like']"
                    ]
                    
                    liked = False
                    for selector in like_selectors:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                parent = element.find_element(By.XPATH, "./parent::*")
                                if parent.is_displayed():
                                    parent.click()
                                    liked = True
                                    break
                            if liked:
                                break
                        except:
                            continue
                    
                    if liked:
                        logging.info(f"Лайк поста {i+1} від {username} для {target_username}")
                        self.account_manager.increment_actions(username)
                        success_count += 1
                        time.sleep(random.uniform(3, 8))
                    
                    # Закриття поста
                    try:
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(random.uniform(2, 3))
                    except:
                        pass
                    
                except Exception as e:
                    logging.error(f"Помилка лайка поста {i+1}: {e}")
                    try:
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    except:
                        pass
                    continue
            
            logging.info(f"Успішно лайкнуто {success_count}/{count} постів")
            return success_count > 0
            
        except Exception as e:
            logging.error(f"Критична помилка лайка постів: {e}")
            return False
    
    def like_stories(self, username: str, target_username: str) -> bool:
        """Лайк сторіс"""
        try:
            if username not in self.drivers:
                logging.error(f"Акаунт {username} не залогінений")
                return False
            
            driver = self.drivers[username]
            
            # Перехід на головну сторінку
            logging.info(f"Пошук сторіс {target_username}")
            try:
                driver.get("https://www.instagram.com/")
                time.sleep(random.uniform(5, 8))
            except Exception as e:
                logging.error(f"Помилка переходу на головну сторінку: {e}")
                return False
            
            # Пошук сторіс
            story_found = False
            story_selectors = [
                f"img[alt*='{target_username}']",
                f"canvas[aria-label*='{target_username}']"
            ]
            
            for selector in story_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if target_username.lower() in (element.get_attribute("alt") or "").lower():
                            element.click()
                            story_found = True
                            break
                    if story_found:
                        break
                except:
                    continue
            
            if not story_found:
                logging.warning(f"Не знайдено активних сторіс для {target_username}")
                return False
            
            time.sleep(random.uniform(3, 5))
            
            # Пошук кнопки лайка сторіс
            like_selectors = [
                "svg[aria-label='Like']",
                "button[aria-label='Like']"
            ]
            
            liked = False
            for selector in like_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        parent = element.find_element(By.XPATH, "./parent::*")
                        if parent.is_displayed():
                            parent.click()
                            liked = True
                            break
                    if liked:
                        break
                except:
                    continue
            
            if liked:
                logging.info(f"Лайк сторіс від {username} для {target_username}")
                self.account_manager.increment_actions(username)
                time.sleep(random.uniform(2, 5))
            
            # Закриття сторіс
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except:
                pass
            
            return liked
            
        except Exception as e:
            logging.error(f"Критична помилка лайка сторіс: {e}")
            return False
    
    def reply_to_story(self, username: str, target_username: str, messages: List[str]) -> bool:
        """Відповідь на сторіс"""
        try:
            if username not in self.drivers:
                logging.error(f"Акаунт {username} не залогінений")
                return False
            
            driver = self.drivers[username]
            
            # Перехід на головну сторінку
            logging.info(f"Пошук сторіс {target_username} для відповіді")
            try:
                driver.get("https://www.instagram.com/")
                time.sleep(random.uniform(5, 8))
            except Exception as e:
                logging.error(f"Помилка переходу на головну сторінку: {e}")
                return False
            
            # Пошук сторіс
            story_found = False
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, "img[alt]")
                for element in elements:
                    alt_text = element.get_attribute("alt") or ""
                    if target_username.lower() in alt_text.lower():
                        element.click()
                        story_found = True
                        break
            except:
                pass
            
            if not story_found:
                logging.warning(f"Не знайдено активних сторіс для відповіді {target_username}")
                return False
            
            time.sleep(random.uniform(3, 5))
            
            # Пошук поля для відповіді
            reply_field = None
            reply_selectors = [
                "textarea[placeholder*='message']",
                "input[placeholder*='message']",
                "div[contenteditable='true']"
            ]
            
            for selector in reply_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            reply_field = element
                            break
                    if reply_field:
                        break
                except:
                    continue
            
            if not reply_field:
                logging.warning("Не знайдено поле для відповіді на сторіс")
                return False
            
            # Вибір повідомлення
            message = random.choice(messages) if messages else random.choice(self.story_replies)
            
            # Введення повідомлення
            try:
                reply_field.click()
                time.sleep(0.5)
                reply_field.clear()
                for char in message:
                    reply_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
            except Exception as e:
                logging.error(f"Помилка введення повідомлення: {e}")
                return False
            
            # Відправка
            try:
                reply_field.send_keys(Keys.RETURN)
                time.sleep(random.uniform(2, 4))
                
                logging.info(f"Відповідь на сторіс від {username} для {target_username}: {message}")
                self.account_manager.increment_actions(username)
                
                # Закриття сторіс
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                
                return True
                
            except Exception as e:
                logging.error(f"Помилка відправки повідомлення: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Критична помилка відповіді на сторіс: {e}")
            return False
    
    def run_automation(self, config: Dict):
        """Запуск автоматизації"""
        try:
            accounts = config.get('accounts', [])
            targets = config.get('targets', [])
            actions = config.get('actions', {})
            messages = config.get('story_messages', [])
            
            logging.info(f"Запуск автоматизації: {len(accounts)} акаунтів, {len(targets)} цілей")
            
            total_actions = 0
            successful_actions = 0
            
            for account_info in accounts:
                username = account_info['username']
                
                if not self.account_manager.is_account_available(username):
                    logging.warning(f"Акаунт {username} недоступний")
                    continue
                
                logging.info(f"Обробка акаунту: {username}")
                
                for target in targets:
                    try:
                        # Перевірка лімітів
                        account_data = self.account_manager.get_account_info(username)
                        if account_data.get('actions_count', 0) >= account_data.get('daily_limit', 100):
                            logging.warning(f"Досягнуто денний ліміт для {username}")
                            break
                        
                        logging.info(f"Обробка цілі: {target}")
                        
                        # Лайк постів
                        if actions.get('like_posts', False):
                            total_actions += 1
                            if self.like_last_posts(username, target, 2):
                                successful_actions += 1
                            self.anti_detection.human_like_delay(5, 10)
                        
                        # Лайк сторіс
                        if actions.get('like_stories', False):
                            total_actions += 1
                            if self.like_stories(username, target):
                                successful_actions += 1
                            self.anti_detection.human_like_delay(3, 7)
                        
                        # Відповідь на сторіс
                        if actions.get('reply_stories', False):
                            total_actions += 1
                            if self.reply_to_story(username, target, messages):
                                successful_actions += 1
                            self.anti_detection.human_like_delay(5, 12)
                        
                        # Випадкове прокручування
                        if username in self.drivers:
                            self.anti_detection.random_scroll(self.drivers[username])
                        
                        # Затримка між цілями
                        time.sleep(random.uniform(10, 30))
                        
                        # Моніторинг здоров'я акаунту
                        self.monitor_account_health(username)
                        
                    except Exception as e:
                        logging.error(f"Помилка обробки цілі {target}: {e}")
                        continue
                
                # Затримка між акаунтами
                account_delay = random.uniform(60, 180)
                logging.info(f"Затримка між акаунтами: {account_delay:.1f} секунд")
                time.sleep(account_delay)
            
            # Підсумок
            success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
            logging.info(f"Автоматизація завершена: {successful_actions}/{total_actions} ({success_rate:.1f}%)")
            
        except Exception as e:
            logging.error(f"Помилка автоматизації: {e}")
    
    def monitor_account_health(self, username: str):
        """Моніторинг стану акаунту"""
        try:
            if username not in self.drivers:
                return
            
            driver = self.drivers[username]
            
            # Перевірка на обмеження
            page_source = driver.page_source.lower()
            if any(indicator in page_source for indicator in self.shadowban_indicators):
                self.account_manager.update_account_status(username, 'restricted')
                logging.warning(f"Акаунт {username} обмежений")
                return
            
            # Перевірка на shadowban
            try:
                driver.get(f"https://www.instagram.com/{username}/")
                self.anti_detection.human_like_delay(3, 5)
                
                if "Page Not Found" in driver.page_source or "User not found" in driver.page_source:
                    self.account_manager.update_account_status(username, 'shadowban')
                    logging.warning(f"Можливий shadowban для {username}")
                
            except Exception as e:
                logging.debug(f"Помилка перевірки shadowban для {username}: {e}")
            
        except Exception as e:
            logging.error(f"Помилка моніторингу акаунту {username}: {e}")
    
    def close_driver(self, username: str):
        """Закриття драйвера для акаунту"""
        if username in self.drivers:
            try:
                self.drivers[username].quit()
                del self.drivers[username]
                logging.info(f"Драйвер для {username} закрито")
            except Exception as e:
                logging.error(f"Помилка закриття драйвера {username}: {e}")
    
    def close_all_drivers(self):
        """Закриття всіх драйверів"""
        for username in list(self.drivers.keys()):
            self.close_driver(username)
        
        logging.info("Всі драйвери закрито")
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """Отримання статистики акаунтів"""
        stats = {
            'total_accounts': len(self.account_manager.accounts),
            'active_accounts': 0,
            'restricted_accounts': 0,
            'total_actions_today': 0
        }
        
        for username, account_info in self.account_manager.accounts.items():
            status = account_info.get('status', 'unknown')
            if status == 'active':
                stats['active_accounts'] += 1
            elif status in ['restricted', 'shadowban', 'banned']:
                stats['restricted_accounts'] += 1
            
            stats['total_actions_today'] += account_info.get('actions_count', 0)
        
        return stats
    
    def __del__(self):
        """Деструктор"""
        try:
            self.close_all_drivers()
        except Exception:
            pass