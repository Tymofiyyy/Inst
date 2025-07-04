#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основний файл запуску Instagram Bot
"""

import sys
import os
import argparse
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

# Додавання поточної директорії до шляху
sys.path.append(str(Path(__file__).parent))

try:
    from instagram_bot import InstagramBot
    from config import BotConfig
    from utils import (
        setup_logging, ProxyManager, StatisticsManager, 
        DatabaseManager, FileManager, SystemUtils,
        ConfigValidator, create_default_config
    )
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    print("Переконайтесь, що всі файли знаходяться в одній директорії")
    sys.exit(1)


class BotScheduler:
    """Планувальник для автоматизації бота"""
    
    def __init__(self, bot: InstagramBot):
        self.bot = bot
        self.running = False
        self.scheduler_thread = None
        
    def schedule_daily_automation(self, config: dict, start_time: str = "09:00"):
        """Планування щоденної автоматизації"""
        try:
            import schedule
            schedule.every().day.at(start_time).do(
                self.run_automation_job, config
            )
            logging.info(f"Заплановано щоденну автоматизацію на {start_time}")
        except ImportError:
            logging.error("Для планувальника потрібна бібліотека 'schedule': pip install schedule")
            
    def schedule_account_rotation(self, interval_hours: int = 4):
        """Планування ротації акаунтів"""
        try:
            import schedule
            schedule.every(interval_hours).hours.do(self.rotate_accounts)
            logging.info(f"Заплановано ротацію акаунтів кожні {interval_hours} годин")
        except ImportError:
            pass
        
    def schedule_health_check(self, interval_minutes: int = 30):
        """Планування перевірки здоров'я акаунтів"""
        try:
            import schedule
            schedule.every(interval_minutes).minutes.do(self.check_account_health)
            logging.info(f"Заплановано перевірку здоров'я кожні {interval_minutes} хвилин")
        except ImportError:
            pass
        
    def run_automation_job(self, config: dict):
        """Виконання автоматизації"""
        try:
            logging.info("🚀 Запуск запланованої автоматизації")
            self.bot.run_automation(config)
            logging.info("✅ Запланована автоматизація завершена")
        except Exception as e:
            logging.error(f"❌ Помилка автоматизації: {e}")
    
    def rotate_accounts(self):
        """Ротація акаунтів"""
        try:
            logging.info("🔄 Ротація акаунтів")
            self.bot.close_all_drivers()
            time.sleep(60)  # Пауза між ротаціями
            logging.info("✅ Ротація завершена")
        except Exception as e:
            logging.error(f"❌ Помилка ротації акаунтів: {e}")
    
    def check_account_health(self):
        """Перевірка здоров'я акаунтів"""
        try:
            logging.info("🏥 Перевірка здоров'я акаунтів")
            for username in self.bot.account_manager.accounts:
                if self.bot.account_manager.is_account_available(username):
                    self.bot.monitor_account_health(username)
            logging.info("✅ Перевірка здоров'я завершена")
        except Exception as e:
            logging.error(f"❌ Помилка перевірки здоров'я: {e}")
    
    def start_scheduler(self):
        """Запуск планувальника"""
        try:
            import schedule
            import threading
            
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logging.info("📅 Планувальник запущено")
        except ImportError:
            logging.error("Для планувальника потрібна бібліотека 'schedule': pip install schedule")
    
    def stop_scheduler(self):
        """Зупинка планувальника"""
        try:
            import schedule
            self.running = False
            schedule.clear()
            logging.info("⏹️ Планувальник зупинено")
        except ImportError:
            pass
    
    def _run_scheduler(self):
        """Внутрішній цикл планувальника"""
        try:
            import schedule
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Перевірка кожну хвилину
        except ImportError:
            pass


def check_system_requirements():
    """Перевірка системних вимог"""
    print("🔍 Перевірка системних вимог...")
    
    # Перевірка версії Python
    if sys.version_info < (3, 8):
        print("❌ Потрібна версія Python 3.8 або вища")
        return False
    
    print(f"✅ Python {sys.version}")
    
    # Перевірка залежностей
    dependencies = SystemUtils.check_dependencies()
    missing_deps = [dep for dep, available in dependencies.items() if not available]
    
    if missing_deps:
        print(f"❌ Відсутні залежності: {', '.join(missing_deps)}")
        print("Встановіть їх командою: pip install -r requirements.txt")
        return False
    
    print("✅ Всі залежності встановлені")
    
    # Перевірка Chrome
    chrome_version = SystemUtils.get_chrome_version()
    if chrome_version == "Unknown":
        print("⚠️ Chrome не знайдено або версію не вдалося визначити")
        print("Встановіть Google Chrome для роботи з Selenium")
    else:
        print(f"✅ Chrome {chrome_version}")
    
    return True


def setup_environment():
    """Налаштування робочого середовища"""
    print("⚙️ Налаштування середовища...")
    
    # Створення необхідних директорій
    directories = ['logs', 'backups', 'data', 'exports']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Налаштування логування
    setup_logging('logs/instagram_bot.log')
    
    # Створення стандартних файлів
    config_file = 'bot_config.json'
    if not os.path.exists(config_file):
        config = BotConfig(config_file)
        default_config = create_default_config()
        config.config = default_config
        config.save_config()
        print(f"✅ Створено файл конфігурації: {config_file}")
    
    # Створення файлу requirements.txt якщо відсутній
    requirements_file = 'requirements.txt'
    if not os.path.exists(requirements_file):
        requirements = [
            "selenium==4.15.2",
            "opencv-python==4.8.1.78",
            "Pillow==10.0.1", 
            "requests==2.31.0",
            "pytesseract==0.3.10",
            "psutil==5.9.6",
            "numpy==1.24.3",
            "webdriver-manager==4.0.1",
            "schedule==1.2.0"
        ]
        
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(requirements))
        print(f"✅ Створено файл залежностей: {requirements_file}")
    
    print("✅ Середовище налаштовано")


def run_gui_mode():
    """Запуск в GUI режимі"""
    try:
        import tkinter as tk
        from gui import InstagramBotGUI
        
        print("🖥️ Запуск GUI режиму...")
        
        root = tk.Tk()
        app = InstagramBotGUI(root)
        
        # Обробка закриття вікна
        def on_closing():
            if hasattr(app, 'automation_running') and app.automation_running:
                import tkinter.messagebox as messagebox
                if messagebox.askokcancel("Вихід", "Автоматизація працює. Завершити роботу?"):
                    if hasattr(app, 'stop_automation'):
                        app.stop_automation()
                    root.destroy()
            else:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Встановлення іконки (якщо є)
        try:
            root.iconbitmap('icon.ico')
        except:
            pass
        
        print("✅ GUI запущено")
        root.mainloop()
        
    except ImportError:
        print("❌ Для GUI режиму потрібен tkinter")
        print("В Ubuntu/Debian: sudo apt-get install python3-tk")
        return False
    except Exception as e:
        print(f"❌ Помилка запуску GUI: {e}")
        return False
    
    return True


def run_cli_mode(args):
    """Запуск в CLI режимі"""
    print("💻 Запуск CLI режиму...")
    
    try:
        # Завантаження конфігурації
        config = BotConfig(args.config)
        
        # Валідація конфігурації
        validation = ConfigValidator.validate_config(config.config)
        if not validation['valid']:
            print("❌ Помилки конфігурації:")
            for error in validation['errors']:
                print(f"  - {error}")
            return False
        
        if validation['warnings']:
            print("⚠️ Попередження конфігурації:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        # Ініціалізація бота
        bot = InstagramBot(config.get('captcha_api_key'))
        
        # Завантаження акаунтів з файлу
        if args.accounts:
            account_count = load_accounts_from_file(bot, args.accounts)
            print(f"📥 Завантажено {account_count} акаунтів")
        
        if not bot.account_manager.accounts:
            print("❌ Немає акаунтів для роботи")
            print("Додайте акаунти через файл або GUI режим")
            return False
        
        # Завантаження цілей з файлу
        targets = []
        if args.targets:
            targets = load_targets_from_file(args.targets)
            print(f"🎯 Завантажено {len(targets)} цілей")
        
        if not targets:
            print("❌ Немає цілей для автоматизації")
            print("Додайте цілі через файл або GUI режим")
            return False
        
        # Конфігурація автоматизації
        automation_config = {
            'accounts': [{'username': username} for username in bot.account_manager.accounts.keys()],
            'targets': targets,
            'actions': {
                'like_posts': args.like_posts if hasattr(args, 'like_posts') else True,
                'like_stories': args.like_stories if hasattr(args, 'like_stories') else True,
                'reply_stories': args.reply_stories if hasattr(args, 'reply_stories') else True
            },
            'story_messages': config.get('story_replies', [])
        }
        
        print("🚀 Запуск автоматизації...")
        print(f"📊 Акаунтів: {len(automation_config['accounts'])}")
        print(f"🎯 Цілей: {len(automation_config['targets'])}")
        print(f"⚡ Дії: {list(automation_config['actions'].keys())}")
        
        try:
            bot.run_automation(automation_config)
            print("✅ Автоматизація завершена успішно!")
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ Автоматизація зупинена користувачем")
            return True
            
        except Exception as e:
            print(f"❌ Помилка автоматизації: {e}")
            logging.error(f"CLI automation error: {e}")
            return False
            
        finally:
            bot.close_all_drivers()
            
    except Exception as e:
        print(f"❌ Помилка CLI режиму: {e}")
        logging.error(f"CLI mode error: {e}")
        return False


def run_scheduler_mode(args):
    """Запуск планувальника"""
    print("📅 Запуск режиму планувальника...")
    
    try:
        # Перевірка наявності schedule
        try:
            import schedule
        except ImportError:
            print("❌ Для планувальника потрібна бібліотека 'schedule'")
            print("Встановіть її: pip install schedule")
            return False
        
        # Завантаження конфігурації
        config = BotConfig(args.config)
        bot = InstagramBot(config.get('captcha_api_key'))
        scheduler = BotScheduler(bot)
        
        # Завантаження даних
        if args.accounts:
            load_accounts_from_file(bot, args.accounts)
        
        targets = []
        if args.targets:
            targets = load_targets_from_file(args.targets)
        else:
            targets = config.get('targets', [])
        
        if not bot.account_manager.accounts:
            print("❌ Немає акаунтів для планувальника")
            return False
        
        if not targets:
            print("❌ Немає цілей для планувальника")
            return False
        
        # Налаштування розкладу
        automation_config = {
            'accounts': [{'username': username} for username in bot.account_manager.accounts.keys()],
            'targets': targets,
            'actions': {
                'like_posts': True,
                'like_stories': True,
                'reply_stories': True
            },
            'story_messages': config.get('story_replies', [])
        }
        
        # Планування завдань
        start_time = args.start_time if hasattr(args, 'start_time') else "09:00"
        scheduler.schedule_daily_automation(automation_config, start_time)
        scheduler.schedule_account_rotation(4)
        scheduler.schedule_health_check(30)
        
        print(f"⏰ Заплановано автоматизацію на {start_time}")
        print(f"📊 Акаунтів: {len(automation_config['accounts'])}")
        print(f"🎯 Цілей: {len(automation_config['targets'])}")
        
        try:
            print("🔄 Запуск планувальника...")
            scheduler.start_scheduler()
            
            print("✅ Планувальник працює. Натисніть Ctrl+C для зупинки")
            
            # Очікування
            while True:
                time.sleep(60)
                # Показуємо статус кожну хвилину
                current_time = time.strftime("%H:%M:%S")
                print(f"⏱️ {current_time} - Планувальник активний")
                
        except KeyboardInterrupt:
            print("\n⏹️ Планувальник зупинений користувачем")
            
        finally:
            scheduler.stop_scheduler()
            bot.close_all_drivers()
            
        return True
        
    except Exception as e:
        print(f"❌ Помилка планувальника: {e}")
        logging.error(f"Scheduler error: {e}")
        return False


def load_accounts_from_file(bot: InstagramBot, file_path: str) -> int:
    """Завантаження акаунтів з файлу"""
    if not os.path.exists(file_path):
        print(f"❌ Файл акаунтів не знайдено: {file_path}")
        return 0
    
    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(':')
                if len(parts) >= 2:
                    username = parts[0].strip()
                    password = parts[1].strip()
                    proxy = ':'.join(parts[2:]).strip() if len(parts) > 2 else None
                    
                    # Валідація
                    from utils import ValidationUtils
                    if not ValidationUtils.validate_username(username):
                        print(f"⚠️ Некоректний логін в рядку {line_num}: {username}")
                        continue
                    
                    if proxy and not ValidationUtils.validate_proxy(proxy):
                        print(f"⚠️ Некоректний проксі в рядку {line_num}: {proxy}")
                        proxy = None
                    
                    bot.account_manager.add_account(username, password, proxy)
                    count += 1
                else:
                    print(f"⚠️ Некоректний формат в рядку {line_num}: {line}")
        
        logging.info(f"Завантажено {count} акаунтів з файлу {file_path}")
        
    except Exception as e:
        print(f"❌ Помилка завантаження акаунтів: {e}")
        logging.error(f"Error loading accounts: {e}")
    
    return count


def load_targets_from_file(file_path: str) -> List[str]:
    """Завантаження цілей з файлу"""
    if not os.path.exists(file_path):
        print(f"❌ Файл цілей не знайдено: {file_path}")
        return []
    
    targets = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                target = line.strip()
                if target and not target.startswith('#'):
                    # Валідація
                    from utils import ValidationUtils
                    if ValidationUtils.validate_username(target):
                        targets.append(target)
                    else:
                        print(f"⚠️ Некоректна ціль в рядку {line_num}: {target}")
        
        logging.info(f"Завантажено {len(targets)} цілей з файлу {file_path}")
        
    except Exception as e:
        print(f"❌ Помилка завантаження цілей: {e}")
        logging.error(f"Error loading targets: {e}")
    
    return targets


def create_sample_files():
    """Створення зразків файлів"""
    print("📝 Створення зразків файлів...")
    
    # Зразок файлу акаунтів
    accounts_sample = """# Формат: username:password:proxy (proxy опціонально)
# Приклади:
# my_account:my_password
# account2:password2:127.0.0.1:8080
# account3:password3:proxy.example.com:3128:user:pass

# Ваші акаунти:
"""
    
    if not os.path.exists('accounts_sample.txt'):
        with open('accounts_sample.txt', 'w', encoding='utf-8') as f:
            f.write(accounts_sample)
        print("✅ Створено accounts_sample.txt")
    
    # Зразок файлу цілей
    targets_sample = """# Список цільових користувачів (по одному на рядок)
# Приклади:
# target_user1
# target_user2
# target_user3

# Ваші цілі:
"""
    
    if not os.path.exists('targets_sample.txt'):
        with open('targets_sample.txt', 'w', encoding='utf-8') as f:
            f.write(targets_sample)
        print("✅ Створено targets_sample.txt")


def show_help():
    """Показати довідку"""
    help_text = """
🤖 INSTAGRAM AUTOMATION BOT

📖 КОМАНДИ ЗАПУСКУ:
  python run.py --mode gui                    # GUI режим (рекомендовано)
  python run.py --mode cli                    # CLI режим
  python run.py --mode scheduler              # Планувальник

🔧 ПАРАМЕТРИ:
  --config FILE                               # Файл конфігурації (за замовчуванням: bot_config.json)
  --accounts FILE                             # Файл з акаунтами
  --targets FILE                              # Файл з цілями
  --start-time TIME                           # Час запуску для планувальника (HH:MM)

📋 ПРИКЛАДИ ВИКОРИСТАННЯ:

  # Запуск GUI
  python run.py

  # CLI з власними файлами
  python run.py --mode cli --accounts my_accounts.txt --targets my_targets.txt

  # Планувальник з запуском о 10:00
  python run.py --mode scheduler --start-time 10:00

📁 СТРУКТУРА ФАЙЛІВ:

  bot_config.json                             # Основна конфігурація
  accounts.txt                                # Акаунти (username:password:proxy)
  targets.txt                                 # Цілі (по одному на рядок)
  
📊 ЛОГИ ТА ДАНІ:
  
  logs/instagram_bot.log                      # Основний лог
  account_sessions.json                       # Сесії акаунтів  
  statistics.json                             # Статистика роботи

🔒 БЕЗПЕКА:

  • Використовуйте унікальні проксі для кожного акаунту
  • Не перевищуйте денні ліміти (50-100 дій)
  • Робіть перерви між сесіями
  • Моніторьте стан акаунтів

📞 ПІДТРИМКА:

  Логи помилок: logs/instagram_bot.log
  Конфігурація: bot_config.json
  Документація: README.md
"""
    
    print(help_text)


def main():
    """Основна функція"""
    # Банер
    print("\n" + "="*60)
    print("🤖  INSTAGRAM AUTOMATION BOT v2.0")
    print("="*60)
    
    # Парсинг аргументів
    parser = argparse.ArgumentParser(
        description='Instagram Automation Bot - безпечна автоматизація дій в Instagram',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Приклади використання:
  python run.py                              # GUI режим
  python run.py --mode cli --accounts accounts.txt --targets targets.txt
  python run.py --mode scheduler --start-time 09:00
        """
    )
    
    parser.add_argument('--mode', 
                       choices=['gui', 'cli', 'scheduler'], 
                       default='gui', 
                       help='Режим роботи (за замовчуванням: gui)')
    
    parser.add_argument('--config', 
                       default='bot_config.json', 
                       help='Файл конфігурації')
    
    parser.add_argument('--accounts', 
                       help='Файл з акаунтами (username:password:proxy)')
    
    parser.add_argument('--targets', 
                       help='Файл з цілями')
    
    parser.add_argument('--start-time', 
                       default='09:00',
                       help='Час запуску для планувальника (HH:MM)')
    
    parser.add_argument('--like-posts', 
                       action='store_true',
                       help='Лайкати пости')
    
    parser.add_argument('--like-stories', 
                       action='store_true',
                       help='Лайкати сторіс')
    
    parser.add_argument('--reply-stories', 
                       action='store_true',
                       help='Відповідати на сторіс')
    
    parser.add_argument('--create-samples', 
                       action='store_true',
                       help='Створити зразки файлів')
    
    parser.add_argument('--check-system', 
                       action='store_true',
                       help='Перевірити системні вимоги')
    
    parser.add_argument('--help-detailed', 
                       action='store_true',
                       help='Показати детальну довідку')
    
    parser.add_argument('--version', 
                       action='store_true',
                       help='Показати версію')
    
    # Обробка аргументів
    try:
        args = parser.parse_args()
    except SystemExit:
        return 1
    
    # Спеціальні команди
    if args.version:
        print("Instagram Bot v2.0.0")
        print("Python:", sys.version)
        return 0
    
    if args.help_detailed:
        show_help()
        return 0
    
    if args.create_samples:
        create_sample_files()
        return 0
    
    if args.check_system:
        if check_system_requirements():
            print("✅ Система готова до роботи")
            return 0
        else:
            print("❌ Система не готова")
            return 1
    
    # Перевірка системних вимог
    if not check_system_requirements():
        print("\n❌ Системні вимоги не виконані")
        print("Запустіть: python run.py --check-system для деталей")
        return 1
    
    # Налаштування середовища
    setup_environment()
    
    # Запуск відповідного режиму
    success = False
    
    try:
        if args.mode == 'gui':
            success = run_gui_mode()
        elif args.mode == 'cli':
            success = run_cli_mode(args)
        elif args.mode == 'scheduler':
            success = run_scheduler_mode(args)
        
    except KeyboardInterrupt:
        print("\n⏹️ Програма зупинена користувачем")
        success = True
    except Exception as e:
        print(f"\n❌ Критична помилка: {e}")
        logging.error(f"Critical error: {e}")
        success = False
    
    # Завершення
    print("\n" + "="*60)
    if success:
        print("✅ Програма завершена успішно")
    else:
        print("❌ Програма завершена з помилками")
        print("Перевірте логи: logs/instagram_bot.log")
    print("="*60)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)