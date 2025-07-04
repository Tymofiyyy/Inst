"""
Допоміжні утиліти для Instagram Bot
"""

import random
import string
import hashlib
import base64
import time
from typing import List, Dict, Any
import json
import os
import sqlite3
import requests
from datetime import datetime, timedelta
import logging


class ProxyManager:
    """Менеджер проксі серверів"""
    
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = []
        self.current_index = 0
    
    def add_proxy(self, proxy: str):
        """Додавання проксі"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
    
    def add_proxies_from_file(self, file_path: str):
        """Додавання проксі з файлу"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and ':' in proxy:
                        self.add_proxy(proxy)
            logging.info(f"Завантажено {len(self.proxies)} проксі з файлу")
        except Exception as e:
            logging.error(f"Помилка завантаження проксі: {e}")
    
    def test_proxy(self, proxy: str) -> bool:
        """Тестування проксі"""
        try:
            # Парсинг проксі
            if proxy.count(':') >= 3:
                # Формат: ip:port:user:pass
                parts = proxy.split(':')
                proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            else:
                # Формат: ip:port
                proxy_url = f"http://{proxy}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logging.debug(f"Проксі {proxy} не працює: {e}")
            return False
    
    def test_all_proxies(self):
        """Тестування всіх проксі"""
        self.working_proxies = []
        self.failed_proxies = []
        
        logging.info("Початок тестування проксі...")
        
        for i, proxy in enumerate(self.proxies):
            logging.info(f"Тестування проксі {i+1}/{len(self.proxies)}: {proxy}")
            
            if self.test_proxy(proxy):
                self.working_proxies.append(proxy)
                logging.info(f"✅ Проксі {proxy} працює")
            else:
                self.failed_proxies.append(proxy)
                logging.warning(f"❌ Проксі {proxy} не працює")
        
        logging.info(f"Результат: {len(self.working_proxies)} робочих, {len(self.failed_proxies)} неробочих")
        return len(self.working_proxies)
    
    def get_random_proxy(self) -> str:
        """Отримання випадкового проксі"""
        if not self.working_proxies:
            return None
        return random.choice(self.working_proxies)
    
    def get_next_proxy(self) -> str:
        """Отримання наступного проксі по черзі"""
        if not self.working_proxies:
            return None
        
        proxy = self.working_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.working_proxies)
        return proxy
    
    def remove_proxy(self, proxy: str):
        """Видалення проксі зі списків"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
        if proxy in self.failed_proxies:
            self.failed_proxies.remove(proxy)
    
    def get_stats(self) -> Dict[str, int]:
        """Отримання статистики проксі"""
        return {
            'total': len(self.proxies),
            'working': len(self.working_proxies),
            'failed': len(self.failed_proxies),
            'success_rate': (len(self.working_proxies) / len(self.proxies) * 100) if self.proxies else 0
        }


class SessionManager:
    """Менеджер сесій для збереження стану"""
    
    def __init__(self, session_file: str = "sessions.json"):
        self.session_file = session_file
        self.sessions = self.load_sessions()
    
    def load_sessions(self) -> Dict:
        """Завантаження сесій"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Помилка завантаження сесій: {e}")
        return {}
    
    def save_sessions(self):
        """Збереження сесій"""
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Помилка збереження сесій: {e}")
    
    def save_session(self, username: str, session_data: Dict):
        """Збереження сесії акаунту"""
        self.sessions[username] = {
            **session_data,
            'last_updated': datetime.now().isoformat(),
            'session_id': self.generate_session_id()
        }
        self.save_sessions()
    
    def get_session(self, username: str) -> Dict:
        """Отримання сесії акаунту"""
        return self.sessions.get(username, {})
    
    def delete_session(self, username: str):
        """Видалення сесії акаунту"""
        if username in self.sessions:
            del self.sessions[username]
            self.save_sessions()
    
    def is_session_valid(self, username: str, max_age_hours: int = 24) -> bool:
        """Перевірка валідності сесії"""
        session = self.get_session(username)
        if not session or 'last_updated' not in session:
            return False
        
        try:
            last_updated = datetime.fromisoformat(session['last_updated'])
            age = datetime.now() - last_updated
            return age.total_seconds() < max_age_hours * 3600
        except Exception:
            return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 48):
        """Очищення старих сесій"""
        to_remove = []
        for username in self.sessions:
            if not self.is_session_valid(username, max_age_hours):
                to_remove.append(username)
        
        for username in to_remove:
            del self.sessions[username]
        
        if to_remove:
            self.save_sessions()
            logging.info(f"Видалено {len(to_remove)} застарілих сесій")
    
    @staticmethod
    def generate_session_id() -> str:
        """Генерація ID сесії"""
        timestamp = str(int(time.time()))
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return base64.b64encode(f"{timestamp}:{random_part}".encode()).decode()


class SecurityManager:
    """Менеджер безпеки та обходу детекції"""
    
    @staticmethod
    def generate_device_id() -> str:
        """Генерація унікального ID пристрою"""
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        return hashlib.md5(random_string.encode()).hexdigest()
    
    @staticmethod
    def generate_fingerprint() -> Dict[str, Any]:
        """Генерація цифрового відбитку пристрою"""
        return {
            'device_id': SecurityManager.generate_device_id(),
            'user_agent': SecurityManager.random_user_agent(),
            'viewport': SecurityManager.get_random_viewport(),
            'timezone': random.choice(['Europe/Kiev', 'Europe/Moscow', 'Europe/Warsaw']),
            'language': random.choice(['uk-UA', 'en-US', 'ru-RU']),
            'platform': random.choice(['Linux', 'Android']),
            'screen_resolution': SecurityManager.get_random_screen_resolution()
        }
    
    @staticmethod
    def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> float:
        """Генерація людської затримки"""
        # Використання нормального розподілу для більш реалістичних затримок
        mean = (min_seconds + max_seconds) / 2
        std = (max_seconds - min_seconds) / 6  # 99.7% значень будуть в межах min-max
        delay = random.normalvariate(mean, std)
        return max(min_seconds, min(max_seconds, delay))
    
    @staticmethod
    def random_user_agent() -> str:
        """Генерація випадкового User-Agent"""
        agents = [
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ]
        return random.choice(agents)
    
    @staticmethod
    def get_random_viewport() -> Dict[str, int]:
        """Генерація випадкового розміру вікна"""
        viewports = [
            {'width': 360, 'height': 640},
            {'width': 375, 'height': 667},
            {'width': 414, 'height': 736},
            {'width': 412, 'height': 869},
            {'width': 360, 'height': 780},
            {'width': 393, 'height': 851},
            {'width': 390, 'height': 844}
        ]
        return random.choice(viewports)
    
    @staticmethod
    def get_random_screen_resolution() -> Dict[str, int]:
        """Генерація випадкової роздільної здатності екрану"""
        resolutions = [
            {'width': 1080, 'height': 1920},
            {'width': 1080, 'height': 2340},
            {'width': 1125, 'height': 2436},
            {'width': 1242, 'height': 2208},
            {'width': 1080, 'height': 2400},
            {'width': 1170, 'height': 2532}
        ]
        return random.choice(resolutions)
    
    @staticmethod
    def generate_realistic_typing_delays(text: str) -> List[float]:
        """Генерація реалістичних затримок при введенні тексту"""
        delays = []
        for i, char in enumerate(text):
            if char == ' ':
                # Більша затримка для пробілів
                delay = random.uniform(0.1, 0.3)
            elif char.isupper() and i > 0:
                # Затримка для великих літер (Shift)
                delay = random.uniform(0.08, 0.15)
            elif char in '.,!?;:':
                # Затримка для розділових знаків
                delay = random.uniform(0.05, 0.12)
            else:
                # Звичайна затримка
                delay = random.uniform(0.03, 0.08)
            
            delays.append(delay)
        
        return delays
    
    @staticmethod
    def random_mouse_movement() -> List[Dict[str, int]]:
        """Генерація випадкових рухів миші"""
        movements = []
        current_x, current_y = 200, 200  # Початкова позиція
        
        for _ in range(random.randint(3, 8)):
            # Невеликі випадкові рухи
            current_x += random.randint(-50, 50)
            current_y += random.randint(-50, 50)
            
            # Обмеження координат
            current_x = max(50, min(800, current_x))
            current_y = max(50, min(600, current_y))
            
            movements.append({'x': current_x, 'y': current_y})
        
        return movements


class StatisticsManager:
    """Менеджер статистики та аналітики"""
    
    def __init__(self, stats_file: str = "statistics.json"):
        self.stats_file = stats_file
        self.stats = self.load_stats()
    
    def load_stats(self) -> Dict:
        """Завантаження статистики"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Помилка завантаження статистики: {e}")
        
        return {
            'accounts': {},
            'daily_stats': {},
            'hourly_stats': {},
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'start_time': datetime.now().isoformat()
        }
    
    def save_stats(self):
        """Збереження статистики"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Помилка збереження статистики: {e}")
    
    def record_action(self, username: str, action: str, success: bool = True, target: str = None):
        """Запис дії"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        hour = now.strftime("%Y-%m-%d %H:00")
        
        # Статистика акаунту
        if username not in self.stats['accounts']:
            self.stats['accounts'][username] = {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'actions_by_type': {},
                'last_action': None,
                'targets': []
            }
        
        account_stats = self.stats['accounts'][username]
        account_stats['total_actions'] += 1
        account_stats['last_action'] = now.isoformat()
        
        if target:
            if target not in account_stats['targets']:
                account_stats['targets'].append(target)
        
        if success:
            account_stats['successful_actions'] += 1
            self.stats['successful_actions'] += 1
        else:
            account_stats['failed_actions'] += 1
            self.stats['failed_actions'] += 1
        
        # Статистика по типу дії
        if action not in account_stats['actions_by_type']:
            account_stats['actions_by_type'][action] = {'total': 0, 'successful': 0, 'failed': 0}
        
        account_stats['actions_by_type'][action]['total'] += 1
        if success:
            account_stats['actions_by_type'][action]['successful'] += 1
        else:
            account_stats['actions_by_type'][action]['failed'] += 1
        
        # Денна статистика
        if today not in self.stats['daily_stats']:
            self.stats['daily_stats'][today] = {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'actions_by_type': {}
            }
        
        daily_stats = self.stats['daily_stats'][today]
        daily_stats['total_actions'] += 1
        
        if success:
            daily_stats['successful_actions'] += 1
        else:
            daily_stats['failed_actions'] += 1
        
        # Статистика по типу дії за день
        if action not in daily_stats['actions_by_type']:
            daily_stats['actions_by_type'][action] = 0
        daily_stats['actions_by_type'][action] += 1
        
        # Погодинна статистика
        if hour not in self.stats['hourly_stats']:
            self.stats['hourly_stats'][hour] = {
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0
            }
        
        hourly_stats = self.stats['hourly_stats'][hour]
        hourly_stats['total_actions'] += 1
        
        if success:
            hourly_stats['successful_actions'] += 1
        else:
            hourly_stats['failed_actions'] += 1
        
        self.stats['total_actions'] += 1
        self.save_stats()
    
    def get_account_stats(self, username: str) -> Dict:
        """Отримання статистики акаунту"""
        return self.stats['accounts'].get(username, {})
    
    def get_daily_stats(self, date: str = None) -> Dict:
        """Отримання денної статистики"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.stats['daily_stats'].get(date, {})
    
    def get_hourly_stats(self, hour: str = None) -> Dict:
        """Отримання погодинної статистики"""
        if hour is None:
            hour = datetime.now().strftime("%Y-%m-%d %H:00")
        return self.stats['hourly_stats'].get(hour, {})
    
    def get_success_rate(self, username: str = None) -> float:
        """Розрахунок успішності"""
        if username:
            stats = self.get_account_stats(username)
        else:
            stats = self.stats
        
        total = stats.get('total_actions', 0)
        successful = stats.get('successful_actions', 0)
        
        return (successful / total * 100) if total > 0 else 0
    
    def get_actions_per_hour(self, username: str = None) -> float:
        """Розрахунок дій за годину"""
        if username:
            account_stats = self.get_account_stats(username)
            total_actions = account_stats.get('total_actions', 0)
        else:
            total_actions = self.stats.get('total_actions', 0)
        
        try:
            start_time = datetime.fromisoformat(self.stats['start_time'])
            hours_elapsed = (datetime.now() - start_time).total_seconds() / 3600
            return total_actions / hours_elapsed if hours_elapsed > 0 else 0
        except:
            return 0
    
    def get_top_targets(self, username: str = None, limit: int = 10) -> List[str]:
        """Отримання топ цілей"""
        if username:
            account_stats = self.get_account_stats(username)
            return list(account_stats.get('targets', []))[:limit]
        else:
            all_targets = set()
            for account_data in self.stats['accounts'].values():
                all_targets.update(account_data.get('targets', []))
            return list(all_targets)[:limit]
    
    def export_report(self, file_path: str, format: str = 'json'):
        """Експорт звіту"""
        try:
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'summary': {
                    'total_actions': self.stats['total_actions'],
                    'successful_actions': self.stats['successful_actions'],
                    'failed_actions': self.stats['failed_actions'],
                    'success_rate': self.get_success_rate(),
                    'actions_per_hour': self.get_actions_per_hour(),
                    'active_accounts': len(self.stats['accounts'])
                },
                'accounts': self.stats['accounts'],
                'daily_stats': self.stats['daily_stats']
            }
            
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Заголовки
                    writer.writerow(['Акаунт', 'Всього дій', 'Успішних', 'Неуспішних', 'Успішність %', 'Остання дія'])
                    
                    # Дані по акаунтах
                    for username, stats in self.stats['accounts'].items():
                        success_rate = (stats['successful_actions'] / stats['total_actions'] * 100) if stats['total_actions'] > 0 else 0
                        writer.writerow([
                            username,
                            stats['total_actions'],
                            stats['successful_actions'],
                            stats['failed_actions'],
                            f"{success_rate:.1f}%",
                            stats.get('last_action', 'Ніколи')
                        ])
            
            elif format.lower() == 'html':
                html_content = self._generate_html_report(report_data)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            return True
            
        except Exception as e:
            logging.error(f"Помилка експорту звіту: {e}")
            return False
    
    def _generate_html_report(self, data: Dict) -> str:
        """Генерація HTML звіту"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Instagram Bot Report</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Instagram Bot - Звіт про роботу</h1>
            <p>Згенеровано: {data['generated_at']}</p>
            
            <div class="summary">
                <h2>Загальна статистика</h2>
                <p>Всього дій: <strong>{data['summary']['total_actions']}</strong></p>
                <p>Успішних дій: <strong class="success">{data['summary']['successful_actions']}</strong></p>
                <p>Неуспішних дій: <strong class="error">{data['summary']['failed_actions']}</strong></p>
                <p>Успішність: <strong>{data['summary']['success_rate']:.1f}%</strong></p>
                <p>Дій за годину: <strong>{data['summary']['actions_per_hour']:.1f}</strong></p>
                <p>Активних акаунтів: <strong>{data['summary']['active_accounts']}</strong></p>
            </div>
            
            <h2>Статистика по акаунтах</h2>
            <table>
                <tr>
                    <th>Акаунт</th>
                    <th>Всього дій</th>
                    <th>Успішних</th>
                    <th>Неуспішних</th>
                    <th>Успішність</th>
                    <th>Остання дія</th>
                </tr>
        """
        
        for username, stats in data['accounts'].items():
            success_rate = (stats['successful_actions'] / stats['total_actions'] * 100) if stats['total_actions'] > 0 else 0
            html += f"""
                <tr>
                    <td>{username}</td>
                    <td>{stats['total_actions']}</td>
                    <td class="success">{stats['successful_actions']}</td>
                    <td class="error">{stats['failed_actions']}</td>
                    <td>{success_rate:.1f}%</td>
                    <td>{stats.get('last_action', 'Ніколи')}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html
    
    def clear_old_data(self, days_to_keep: int = 30):
        """Очищення старих даних"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        # Очищення денної статистики
        to_remove = []
        for date in self.stats['daily_stats']:
            if date < cutoff_str:
                to_remove.append(date)
        
        for date in to_remove:
            del self.stats['daily_stats'][date]
        
        # Очищення погодинної статистики
        cutoff_hour = cutoff_date.strftime("%Y-%m-%d %H:00")
        to_remove = []
        for hour in self.stats['hourly_stats']:
            if hour < cutoff_hour:
                to_remove.append(hour)
        
        for hour in to_remove:
            del self.stats['hourly_stats'][hour]
        
        if to_remove:
            self.save_stats()
            logging.info(f"Очищено статистику старше {days_to_keep} днів")


class DatabaseManager:
    """Менеджер бази даних (SQLite)"""
    
    def __init__(self, db_file: str = "instagram_bot.db"):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Ініціалізація бази даних"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Таблиця акаунтів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                proxy TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                actions_count INTEGER DEFAULT 0,
                daily_limit INTEGER DEFAULT 100,
                success_rate REAL DEFAULT 0.0
            )
        ''')
        
        # Таблиця дій
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_user TEXT,
                status TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                execution_time REAL,
                FOREIGN KEY (username) REFERENCES accounts (username)
            )
        ''')
        
        # Таблиця цілей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 1,
                last_interaction TIMESTAMP
            )
        ''')
        
        # Таблиця логів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                username TEXT,
                action_id INTEGER,
                FOREIGN KEY (action_id) REFERENCES actions (id)
            )
        ''')
        
        # Таблиця налаштувань
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Індекси для оптимізації
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_username ON actions (username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp)')
        
        conn.commit()
        conn.close()
    
    def add_account(self, username: str, password: str, proxy: str = None) -> bool:
        """Додавання акаунту до БД"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO accounts (username, password, proxy)
                VALUES (?, ?, ?)
            ''', (username, password, proxy))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_accounts(self) -> List[Dict]:
        """Отримання всіх акаунтів"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM accounts')
        columns = [description[0] for description in cursor.description]
        accounts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return accounts
    
    def update_account_status(self, username: str, status: str):
        """Оновлення статусу акаунту"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE accounts 
            SET status = ?, last_activity = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (status, username))
        
        conn.commit()
        conn.close()
    
    def log_action(self, username: str, action_type: str, target_user: str, 
                   status: str, details: str = None, execution_time: float = None) -> int:
        """Логування дії"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO actions (username, action_type, target_user, status, details, execution_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, action_type, target_user, status, details, execution_time))
        
        action_id = cursor.lastrowid
        
        # Оновлення лічильника дій акаунту
        cursor.execute('''
            UPDATE accounts 
            SET actions_count = actions_count + 1, last_activity = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
        
        return action_id
    
    def get_actions_by_date(self, date: str, username: str = None) -> List[Dict]:
        """Отримання дій за датою"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        if username:
            cursor.execute('''
                SELECT * FROM actions 
                WHERE DATE(timestamp) = ? AND username = ?
                ORDER BY timestamp DESC
            ''', (date, username))
        else:
            cursor.execute('''
                SELECT * FROM actions 
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            ''', (date,))
        
        columns = [description[0] for description in cursor.description]
        actions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return actions
    
    def get_statistics(self, days: int = 7) -> Dict:
        """Отримання статистики за період"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Загальна статистика
        cursor.execute('''
            SELECT 
                COUNT(*) as total_actions,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_actions,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_actions,
                AVG(execution_time) as avg_execution_time
            FROM actions 
            WHERE timestamp >= DATE('now', '-{} days')
        '''.format(days))
        
        general_stats = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
        
        # Статистика по типах дій
        cursor.execute('''
            SELECT action_type, COUNT(*) as count
            FROM actions 
            WHERE timestamp >= DATE('now', '-{} days')
            GROUP BY action_type
        '''.format(days))
        
        action_types = dict(cursor.fetchall())
        
        # Статистика по акаунтах
        cursor.execute('''
            SELECT username, COUNT(*) as actions_count,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_actions
            FROM actions 
            WHERE timestamp >= DATE('now', '-{} days')
            GROUP BY username
        '''.format(days))
        
        account_stats = {}
        for row in cursor.fetchall():
            username, total, successful = row
            success_rate = (successful / total * 100) if total > 0 else 0
            account_stats[username] = {
                'total_actions': total,
                'successful_actions': successful,
                'success_rate': success_rate
            }
        
        conn.close()
        
        return {
            'general': general_stats,
            'action_types': action_types,
            'accounts': account_stats
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Очищення старих даних"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Видалення старих дій
        cursor.execute('''
            DELETE FROM actions 
            WHERE timestamp < DATE('now', '-{} days')
        '''.format(days_to_keep))
        
        actions_deleted = cursor.rowcount
        
        # Видалення старих логів
        cursor.execute('''
            DELETE FROM logs 
            WHERE timestamp < DATE('now', '-{} days')
        '''.format(days_to_keep))
        
        logs_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logging.info(f"Видалено {actions_deleted} старих дій та {logs_deleted} старих логів")
        return actions_deleted + logs_deleted


class FileManager:
    """Менеджер файлів та резервного копіювання"""
    
    @staticmethod
    def create_backup(source_files: List[str], backup_dir: str = "backups") -> str:
        """Створення резервної копії"""
        try:
            import shutil
            from datetime import datetime
            
            # Створення директорії для бекапів
            os.makedirs(backup_dir, exist_ok=True)
            
            # Створення архіву з датою
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"instagram_bot_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Створення архіву
            shutil.make_archive(backup_path, 'zip', '.', 
                              lambda path: any(file in path for file in source_files))
            
            backup_file = f"{backup_path}.zip"
            logging.info(f"Створено резервну копію: {backup_file}")
            return backup_file
            
        except Exception as e:
            logging.error(f"Помилка створення бекапу: {e}")
            return None
    
    @staticmethod
    def restore_backup(backup_file: str, restore_dir: str = ".") -> bool:
        """Відновлення з резервної копії"""
        try:
            import zipfile
            
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                zip_ref.extractall(restore_dir)
            
            logging.info(f"Відновлено з резервної копії: {backup_file}")
            return True
            
        except Exception as e:
            logging.error(f"Помилка відновлення: {e}")
            return False
    
    @staticmethod
    def clean_old_backups(backup_dir: str = "backups", days_to_keep: int = 7):
        """Очищення старих бекапів"""
        try:
            if not os.path.exists(backup_dir):
                return
            
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            removed_count = 0
            
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.zip'):
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        removed_count += 1
                        logging.info(f"Видалено старий бекап: {filename}")
            
            if removed_count > 0:
                logging.info(f"Видалено {removed_count} старих бекапів")
                
        except Exception as e:
            logging.error(f"Помилка очищення бекапів: {e}")
    
    @staticmethod
    def export_data(data: Dict, file_path: str, format: str = 'json'):
        """Експорт даних у різних форматах"""
        try:
            if format.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if isinstance(data, dict) and data:
                        # Якщо дані - словник з однотипними записами
                        first_key = next(iter(data))
                        if isinstance(data[first_key], dict):
                            fieldnames = ['key'] + list(data[first_key].keys())
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            for key, value in data.items():
                                row = {'key': key, **value}
                                writer.writerow(row)
                        else:
                            writer = csv.writer(f)
                            for key, value in data.items():
                                writer.writerow([key, value])
                    elif isinstance(data, list):
                        if data and isinstance(data[0], dict):
                            fieldnames = data[0].keys()
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(data)
                        else:
                            writer = csv.writer(f)
                            writer.writerows(data)
            
            elif format.lower() == 'txt':
                with open(file_path, 'w', encoding='utf-8') as f:
                    if isinstance(data, dict):
                        for key, value in data.items():
                            f.write(f"{key}: {value}\n")
                    elif isinstance(data, list):
                        for item in data:
                            f.write(f"{item}\n")
                    else:
                        f.write(str(data))
            
            return True
            
        except Exception as e:
            logging.error(f"Помилка експорту даних: {e}")
            return False


class NetworkUtils:
    """Утиліти для роботи з мережею"""
    
    @staticmethod
    def check_internet_connection() -> bool:
        """Перевірка підключення до інтернету"""
        try:
            response = requests.get('https://www.google.com', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def check_instagram_availability() -> bool:
        """Перевірка доступності Instagram"""
        try:
            response = requests.get('https://www.instagram.com', timeout=10)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def get_public_ip() -> str:
        """Отримання публічної IP адреси"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text.strip()
        except:
            return "Unknown"
    
    @staticmethod
    def test_proxy_speed(proxy: str) -> float:
        """Тестування швидкості проксі"""
        try:
            if proxy.count(':') >= 3:
                parts = proxy.split(':')
                proxy_url = f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
            else:
                proxy_url = f"http://{proxy}"
            
            proxies = {'http': proxy_url, 'https': proxy_url}
            
            start_time = time.time()
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                return end_time - start_time
            else:
                return float('inf')
                
        except:
            return float('inf')


class ValidationUtils:
    """Утиліти для валідації даних"""
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Валідація імені користувача Instagram"""
        if not username:
            return False
        
        # Instagram usernames: 1-30 символів, тільки букви, цифри, крапки та підкреслення
        import re
        pattern = r'^[a-zA-Z0-9._]{1,30}'
        
        if not re.match(pattern, username):
            return False
        
        # Не може починатися або закінчуватися крапкою
        if username.startswith('.') or username.endswith('.'):
            return False
        
        # Не може містити дві крапки підряд
        if '..' in username:
            return False
        
        return True
    
    @staticmethod
    def validate_proxy(proxy: str) -> bool:
        """Валідація формату проксі"""
        if not proxy:
            return False
        
        parts = proxy.split(':')
        
        # Формат ip:port або ip:port:user:pass
        if len(parts) not in [2, 4]:
            return False
        
        # Перевірка IP адреси
        ip = parts[0]
        try:
            import ipaddress
            ipaddress.ip_address(ip)
        except:
            return False
        
        # Перевірка порту
        try:
            port = int(parts[1])
            if not (1 <= port <= 65535):
                return False
        except:
            return False
        
        return True
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, bool]:
        """Валідація пароля"""
        result = {
            'length': len(password) >= 8,
            'uppercase': any(c.isupper() for c in password),
            'lowercase': any(c.islower() for c in password),
            'digit': any(c.isdigit() for c in password),
            'special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        }
        
        result['valid'] = all(result.values())
        return result
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Очищення імені файлу"""
        import re
        
        # Видалення небезпечних символів
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Обмеження довжини
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename


class ConfigValidator:
    """Валідатор конфігурації"""
    
    @staticmethod
    def validate_config(config: Dict) -> Dict[str, Any]:
        """Валідація конфігурації"""
        errors = []
        warnings = []
        
        # Перевірка обов'язкових полів
        required_fields = ['action_delays', 'story_replies', 'automation_settings']
        for field in required_fields:
            if field not in config:
                errors.append(f"Відсутнє обов'язкове поле: {field}")
        
        # Перевірка затримок
        if 'action_delays' in config:
            for action, delays in config['action_delays'].items():
                if not isinstance(delays, list) or len(delays) != 2:
                    errors.append(f"Некоректний формат затримок для {action}")
                elif delays[0] >= delays[1]:
                    errors.append(f"Мінімальна затримка більша за максимальну для {action}")
                elif delays[0] < 0:
                    errors.append(f"Від'ємна затримка для {action}")
        
        # Перевірка проксі
        if 'proxy_list' in config:
            for i, proxy in enumerate(config['proxy_list']):
                if not ValidationUtils.validate_proxy(proxy):
                    warnings.append(f"Некоректний формат проксі #{i+1}: {proxy}")
        
        # Перевірка лімітів
        if 'daily_action_limit' in config:
            limit = config['daily_action_limit']
            if not isinstance(limit, int) or limit <= 0:
                errors.append("Денний ліміт дій повинен бути позитивним числом")
            elif limit > 500:
                warnings.append("Високий денний ліміт дій може призвести до блокування")
        
        # Перевірка API ключа капчі
        if 'captcha_api_key' in config and config['captcha_api_key']:
            if len(config['captcha_api_key']) < 20:
                warnings.append("API ключ капчі здається некоректним")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


class SystemUtils:
    """Системні утиліти"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Отримання інформації про систему"""
        import platform
        try:
            import psutil
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_free': psutil.disk_usage('.').free
            }
        except ImportError:
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': 'Unknown',
                'memory_total': 'Unknown',
                'memory_available': 'Unknown',
                'disk_free': 'Unknown'
            }
    
    @staticmethod
    def check_dependencies() -> Dict[str, bool]:
        """Перевірка наявності залежностей"""
        dependencies = {
            'selenium': False,
            'requests': False,
            'opencv-python': False,
            'pillow': False,
            'numpy': False,
            'psutil': False
        }
        
        for dep in dependencies:
            try:
                if dep == 'opencv-python':
                    __import__('cv2')
                elif dep == 'pillow':
                    __import__('PIL')
                else:
                    __import__(dep)
                dependencies[dep] = True
            except ImportError:
                dependencies[dep] = False
        
        return dependencies
    
    @staticmethod
    def get_chrome_version() -> str:
        """Отримання версії Chrome"""
        try:
            import subprocess
            import re
            
            if os.name == 'nt':  # Windows
                result = subprocess.run(['reg', 'query', 
                                       'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', 
                                       '/v', 'version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if version:
                        return version.group(1)
            else:  # Linux/Mac
                result = subprocess.run(['google-chrome', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if version:
                        return version.group(1)
            
            return "Unknown"
            
        except Exception:
            return "Unknown"


# Константи та налаштування
DEFAULT_USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36'
]

DEFAULT_STORY_REPLIES = [
    "🔥🔥🔥", "❤️", "Круто!", "👍", "Супер!", 
    "💯", "🙌", "Класно!", "👏", "Wow!",
    "Дуже цікаво!", "Топ контент!", "Красиво!",
    "Чудово!", "Нереально!", "Бомба! 💥"
]

INSTAGRAM_LIMITS = {
    'likes_per_hour': 60,
    'likes_per_day': 1000,
    'follows_per_hour': 60,
    'follows_per_day': 400,
    'comments_per_hour': 30,
    'comments_per_day': 200,
    'story_views_per_hour': 100,
    'story_views_per_day': 1000
}

SAFE_DELAYS = {
    'like': [2, 5],
    'comment': [3, 8],
    'follow': [4, 10],
    'story_view': [1, 3],
    'story_reply': [2, 6],
    'between_accounts': [60, 180],
    'between_targets': [10, 30]
}


def setup_logging(log_file: str = "instagram_bot.log", level: str = "INFO"):
    """Налаштування глобального логування"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Форматер для логів
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обробник для файлу
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Обробник для консолі
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Налаштування root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Зменшення рівня логування для selenium
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logging.info("Логування налаштовано")


def create_default_config() -> Dict[str, Any]:
    """Створення стандартної конфігурації"""
    return {
        "captcha_api_key": "",
        "proxy_list": [],
        "max_accounts": 10,
        "daily_action_limit": 100,
        "action_delays": SAFE_DELAYS,
        "user_agents": DEFAULT_USER_AGENTS,
        "story_replies": DEFAULT_STORY_REPLIES,
        "automation_settings": {
            "run_schedule": "09:00-22:00",
            "break_duration": [30, 120],
            "max_actions_per_hour": 20,
            "rotate_accounts": True,
            "use_proxy_rotation": True,
            "respect_limits": True,
            "safe_mode": True
        },
        "instagram_limits": INSTAGRAM_LIMITS,
        "shadowban_indicators": [
            "your account has been restricted",
            "temporarily blocked",
            "unusual activity",
            "violating community guidelines",
            "account suspended",
            "verify your identity"
        ]
    }


if __name__ == "__main__":
    # Тестування утиліт
    print("Тестування Instagram Bot Utils...")
    
    # Тест ProxyManager
    proxy_manager = ProxyManager()
    proxy_manager.add_proxy("127.0.0.1:8080")
    print(f"Проксі додано: {len(proxy_manager.proxies)}")
    
    # Тест SecurityManager
    device_id = SecurityManager.generate_device_id()
    print(f"Device ID: {device_id}")
    
    user_agent = SecurityManager.random_user_agent()
    print(f"User Agent: {user_agent}")
    
    # Тест StatisticsManager
    stats = StatisticsManager()
    stats.record_action("test_user", "like", True, "target_user")
    print(f"Статистика: {stats.get_success_rate():.1f}% успішність")
    
    # Тест ValidationUtils
    print(f"Username валідний: {ValidationUtils.validate_username('test_user')}")
    print(f"Proxy валідний: {ValidationUtils.validate_proxy('127.0.0.1:8080')}")
    
    print("Тестування завершено!")