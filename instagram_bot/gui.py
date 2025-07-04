"""
Графічний інтерфейс для Instagram Bot
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
from datetime import datetime
import queue
import os
from config import BotConfig

class InstagramBotGUI:
    """Графічний інтерфейс бота"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Automation Bot v2.0")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Ініціалізація бота
        self.bot = None
        self.config = BotConfig()
        self.log_queue = queue.Queue()
        self.automation_running = False
        
        # Стилі
        self.setup_styles()
        
        self.setup_gui()
        self.setup_logging()
        
        # Запуск обробки логів
        self.root.after(100, self.process_log_queue)
        
        # Завантаження збережених даних
        self.load_saved_data()
    
    def setup_styles(self):
        """Налаштування стилів інтерфейсу"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Кольорова схема
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def setup_gui(self):
        """Налаштування інтерфейсу"""
        # Головне меню
        self.create_menu()
        
        # Панель статусу
        self.create_status_bar()
        
        # Створення вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка акаунтів
        self.accounts_frame = ttk.Frame(notebook)
        notebook.add(self.accounts_frame, text="🔐 Акаунти")
        self.setup_accounts_tab()
        
        # Вкладка цілей
        self.targets_frame = ttk.Frame(notebook)
        notebook.add(self.targets_frame, text="🎯 Цілі")
        self.setup_targets_tab()
        
        # Вкладка налаштувань
        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text="⚙️ Налаштування")
        self.setup_settings_tab()
        
        # Вкладка автоматизації
        self.automation_frame = ttk.Frame(notebook)
        notebook.add(self.automation_frame, text="🤖 Автоматизація")
        self.setup_automation_tab()
        
        # Вкладка логів
        self.logs_frame = ttk.Frame(notebook)
        notebook.add(self.logs_frame, text="📋 Логи")
        self.setup_logs_tab()
        
        # Вкладка статистики
        self.stats_frame = ttk.Frame(notebook)
        notebook.add(self.stats_frame, text="📊 Статистика")
        self.setup_stats_tab()
    
    def create_menu(self):
        """Створення головного меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Імпорт акаунтів", command=self.import_accounts)
        file_menu.add_command(label="Експорт акаунтів", command=self.export_accounts)
        file_menu.add_separator()
        file_menu.add_command(label="Імпорт конфігурації", command=self.import_config)
        file_menu.add_command(label="Експорт конфігурації", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="Вихід", command=self.root.quit)
        
        # Меню інструменти
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Інструменти", menu=tools_menu)
        tools_menu.add_command(label="Тест проксі", command=self.test_proxies)
        tools_menu.add_command(label="Очистити логи", command=self.clear_logs)
        tools_menu.add_command(label="Перезапустити бота", command=self.restart_bot)
        
        # Меню довідка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Довідка", menu=help_menu)
        help_menu.add_command(label="Про програму", command=self.show_about)
        help_menu.add_command(label="Інструкція", command=self.show_help)
    
    def create_status_bar(self):
        """Створення панелі статусу"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side='bottom', fill='x')
        
        # Статус автоматизації
        self.status_label = ttk.Label(self.status_frame, text="Статус: Очікування")
        self.status_label.pack(side='left', padx=5)
        
        # Лічильник акаунтів
        self.accounts_count_label = ttk.Label(self.status_frame, text="Акаунти: 0")
        self.accounts_count_label.pack(side='left', padx=20)
        
        # Лічильник цілей
        self.targets_count_label = ttk.Label(self.status_frame, text="Цілі: 0")
        self.targets_count_label.pack(side='left', padx=20)
        
        # Час останньої дії
        self.last_action_label = ttk.Label(self.status_frame, text="Остання дія: --")
        self.last_action_label.pack(side='right', padx=5)
    
    def setup_accounts_tab(self):
        """Налаштування вкладки акаунтів"""
        main_frame = ttk.Frame(self.accounts_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Управління акаунтами Instagram", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # Панель додавання акаунту
        add_frame = ttk.LabelFrame(main_frame, text="Додати новий акаунт")
        add_frame.pack(fill='x', pady=(0, 10))
        
        # Поля введення
        fields_frame = ttk.Frame(add_frame)
        fields_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(fields_frame, text="Логін:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.username_entry = ttk.Entry(fields_frame, width=20)
        self.username_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(fields_frame, text="Пароль:").grid(row=0, column=2, sticky='w', padx=(10, 5))
        self.password_entry = ttk.Entry(fields_frame, width=20, show='*')
        self.password_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(fields_frame, text="Проксі:").grid(row=0, column=4, sticky='w', padx=(10, 5))
        self.proxy_entry = ttk.Entry(fields_frame, width=25)
        self.proxy_entry.grid(row=0, column=5, padx=5)
        
        ttk.Button(fields_frame, text="Додати", command=self.add_account).grid(row=0, column=6, padx=10)
        
        # Список акаунтів
        list_frame = ttk.LabelFrame(main_frame, text="Список акаунтів")
        list_frame.pack(fill='both', expand=True)
        
        # Таблиця акаунтів
        columns = ('Логін', 'Статус', 'Дії сьогодні', 'Остання активність', 'Проксі')
        self.accounts_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=150)
        
        # Скролбар для таблиці
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        
        self.accounts_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # Кнопки управління
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=10)
        
        ttk.Button(buttons_frame, text="Оновити", command=self.refresh_accounts).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Видалити", command=self.remove_account).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Тест входу", command=self.test_account_login).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Скинути ліміти", command=self.reset_daily_limits).pack(side='left', padx=5)
    
    def setup_targets_tab(self):
        """Налаштування вкладки цілей"""
        main_frame = ttk.Frame(self.targets_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Управління цільовими акаунтами", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # Панель додавання
        add_frame = ttk.LabelFrame(main_frame, text="Додати ціль")
        add_frame.pack(fill='x', pady=(0, 10))
        
        entry_frame = ttk.Frame(add_frame)
        entry_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(entry_frame, text="Ім'я користувача:").pack(side='left')
        self.target_entry = ttk.Entry(entry_frame, width=30)
        self.target_entry.pack(side='left', padx=10)
        self.target_entry.bind('<Return>', lambda e: self.add_target())
        
        ttk.Button(entry_frame, text="Додати", command=self.add_target).pack(side='left', padx=5)
        ttk.Button(entry_frame, text="Додати з файлу", command=self.import_targets).pack(side='left', padx=5)
        
        # Список цілей
        list_frame = ttk.LabelFrame(main_frame, text="Список цілей")
        list_frame.pack(fill='both', expand=True)
        
        # Контейнер для списку та скролбара
        container = ttk.Frame(list_frame)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.targets_listbox = tk.Listbox(container, height=15)
        scrollbar_targets = ttk.Scrollbar(container, orient='vertical', command=self.targets_listbox.yview)
        self.targets_listbox.configure(yscrollcommand=scrollbar_targets.set)
        
        self.targets_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_targets.pack(side='right', fill='y')
        
        # Кнопки управління
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=10)
        
        ttk.Button(buttons_frame, text="Видалити", command=self.remove_target).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Очистити все", command=self.clear_targets).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Експорт", command=self.export_targets).pack(side='left', padx=5)
        
        # Лічильник
        self.targets_counter = ttk.Label(buttons_frame, text="Цілей: 0")
        self.targets_counter.pack(side='right', padx=5)
    
    def setup_settings_tab(self):
        """Налаштування вкладки налаштувань"""
        main_frame = ttk.Frame(self.settings_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Налаштування бота", style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # Створення canvas для прокручування
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Налаштування капчі
        captcha_frame = ttk.LabelFrame(scrollable_frame, text="🔐 Налаштування розв'язання капчі")
        captcha_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(captcha_frame, text="API ключ 2captcha:").pack(anchor='w', padx=10, pady=(10, 0))
        self.captcha_key_entry = ttk.Entry(captcha_frame, width=60, show='*')
        self.captcha_key_entry.pack(fill='x', padx=10, pady=5)
        
        # Налаштування проксі
        proxy_frame = ttk.LabelFrame(scrollable_frame, text="🌐 Налаштування проксі")
        proxy_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(proxy_frame, text="Проксі (формат: ip:port:user:pass або ip:port):").pack(anchor='w', padx=10, pady=(10, 0))
        self.proxy_text = scrolledtext.ScrolledText(proxy_frame, height=6)
        self.proxy_text.pack(fill='x', padx=10, pady=5)
        
        proxy_buttons = ttk.Frame(proxy_frame)
        proxy_buttons.pack(fill='x', padx=10, pady=5)
        ttk.Button(proxy_buttons, text="Тест проксі", command=self.test_proxies).pack(side='left', padx=5)
        ttk.Button(proxy_buttons, text="Очистити", command=lambda: self.proxy_text.delete('1.0', 'end')).pack(side='left', padx=5)
        
        # Налаштування затримок
        delays_frame = ttk.LabelFrame(scrollable_frame, text="⏱️ Налаштування затримок (секунди)")
        delays_frame.pack(fill='x', pady=5, padx=5)
        
        delays_grid = ttk.Frame(delays_frame)
        delays_grid.pack(fill='x', padx=10, pady=10)
        
        # Лайки
        ttk.Label(delays_grid, text="Лайки (мін-макс):").grid(row=0, column=0, sticky='w')
        self.like_delay_entry = ttk.Entry(delays_grid, width=15)
        self.like_delay_entry.grid(row=0, column=1, padx=5)
        self.like_delay_entry.insert(0, "2-5")
        
        # Коментарі
        ttk.Label(delays_grid, text="Коментарі (мін-макс):").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.comment_delay_entry = ttk.Entry(delays_grid, width=15)
        self.comment_delay_entry.grid(row=0, column=3, padx=5)
        self.comment_delay_entry.insert(0, "3-8")
        
        # Сторіс
        ttk.Label(delays_grid, text="Сторіс (мін-макс):").grid(row=1, column=0, sticky='w', pady=(10,0))
        self.story_delay_entry = ttk.Entry(delays_grid, width=15)
        self.story_delay_entry.grid(row=1, column=1, padx=5, pady=(10,0))
        self.story_delay_entry.insert(0, "1-3")
        
        # Між акаунтами
        ttk.Label(delays_grid, text="Між акаунтами (мін-макс):").grid(row=1, column=2, sticky='w', padx=(20,0), pady=(10,0))
        self.account_delay_entry = ttk.Entry(delays_grid, width=15)
        self.account_delay_entry.grid(row=1, column=3, padx=5, pady=(10,0))
        self.account_delay_entry.insert(0, "60-180")
        
        # Ліміти
        limits_frame = ttk.LabelFrame(scrollable_frame, text="📊 Ліміти безпеки")
        limits_frame.pack(fill='x', pady=5, padx=5)
        
        limits_grid = ttk.Frame(limits_frame)
        limits_grid.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(limits_grid, text="Дій на день:").grid(row=0, column=0, sticky='w')
        self.daily_limit_entry = ttk.Entry(limits_grid, width=10)
        self.daily_limit_entry.grid(row=0, column=1, padx=5)
        self.daily_limit_entry.insert(0, "50")
        
        ttk.Label(limits_grid, text="Дій на годину:").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.hourly_limit_entry = ttk.Entry(limits_grid, width=10)
        self.hourly_limit_entry.grid(row=0, column=3, padx=5)
        self.hourly_limit_entry.insert(0, "15")
        
        # Кнопки збереження
        settings_buttons = ttk.Frame(scrollable_frame)
        settings_buttons.pack(fill='x', pady=20)
        
        ttk.Button(settings_buttons, text="💾 Зберегти налаштування", 
                  command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(settings_buttons, text="📁 Завантажити налаштування", 
                  command=self.load_settings).pack(side='left', padx=5)
        ttk.Button(settings_buttons, text="🔄 Скинути до стандартних", 
                  command=self.reset_settings).pack(side='left', padx=5)
        
        # Упаковка canvas та scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_automation_tab(self):
        """Налаштування вкладки автоматизації"""
        main_frame = ttk.Frame(self.automation_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Налаштування автоматизації", style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # Панель налаштувань дій
        actions_frame = ttk.LabelFrame(main_frame, text="🎯 Дії для виконання")
        actions_frame.pack(fill='x', pady=(0, 10))
        
        actions_grid = ttk.Frame(actions_frame)
        actions_grid.pack(fill='x', padx=10, pady=10)
        
        self.like_posts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(actions_grid, text="Лайкати останні 2 пости", 
                       variable=self.like_posts_var).grid(row=0, column=0, sticky='w', pady=2)
        
        self.like_stories_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(actions_grid, text="Лайкати сторіс", 
                       variable=self.like_stories_var).grid(row=1, column=0, sticky='w', pady=2)
        
        self.reply_stories_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(actions_grid, text="Відповідати на сторіс", 
                       variable=self.reply_stories_var).grid(row=2, column=0, sticky='w', pady=2)
        
        # Повідомлення для сторіс
        messages_frame = ttk.LabelFrame(main_frame, text="💬 Повідомлення для відповідей на сторіс")
        messages_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Кнопки швидкого додавання
        quick_buttons = ttk.Frame(messages_frame)
        quick_buttons.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(quick_buttons, text="🔥 Додати емодзі", 
                  command=self.add_emoji_messages).pack(side='left', padx=5)
        ttk.Button(quick_buttons, text="👍 Додати позитивні", 
                  command=self.add_positive_messages).pack(side='left', padx=5)
        ttk.Button(quick_buttons, text="🗑️ Очистити", 
                  command=self.clear_messages).pack(side='left', padx=5)
        
        self.messages_text = scrolledtext.ScrolledText(messages_frame, height=8)
        self.messages_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Додавання стандартних повідомлень
        default_messages = "\n".join([
            "🔥🔥🔥", "❤️", "Круто!", "👍", "Супер!", 
            "💯", "🙌", "Класно!", "👏", "Wow!",
            "Дуже цікаво!", "Топ контент!", "Красиво!"
        ])
        self.messages_text.insert('1.0', default_messages)
        
        # Панель управління
        control_frame = ttk.LabelFrame(main_frame, text="🚀 Управління автоматизацією")
        control_frame.pack(fill='x', pady=10)
        
        control_buttons = ttk.Frame(control_frame)
        control_buttons.pack(fill='x', padx=10, pady=10)
        
        self.start_button = ttk.Button(control_buttons, text="▶️ Запустити автоматизацію", 
                                      command=self.start_automation)
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(control_buttons, text="⏹️ Зупинити автоматизацію", 
                                     command=self.stop_automation, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        self.pause_button = ttk.Button(control_buttons, text="⏸️ Пауза", 
                                      command=self.pause_automation, state='disabled')
        self.pause_button.pack(side='left', padx=5)
        
        # Прогрес-бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_buttons, variable=self.progress_var, 
                                           length=200, mode='determinate')
        self.progress_bar.pack(side='right', padx=10)
        
        # Статус
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.automation_status_label = ttk.Label(status_frame, text="Статус: Очікування", style='Header.TLabel')
        self.automation_status_label.pack(side='left')
        
        self.eta_label = ttk.Label(status_frame, text="")
        self.eta_label.pack(side='right')
    
    def setup_logs_tab(self):
        """Налаштування вкладки логів"""
        main_frame = ttk.Frame(self.logs_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Журнал подій", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        # Панель фільтрів
        filter_frame = ttk.LabelFrame(main_frame, text="🔍 Фільтри")
        filter_frame.pack(fill='x', pady=(0, 10))
        
        filter_controls = ttk.Frame(filter_frame)
        filter_controls.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(filter_controls, text="Рівень:").pack(side='left')
        self.log_level_var = tk.StringVar(value="Всі")
        log_level_combo = ttk.Combobox(filter_controls, textvariable=self.log_level_var, 
                                      values=["Всі", "INFO", "WARNING", "ERROR"], width=10)
        log_level_combo.pack(side='left', padx=5)
        
        ttk.Button(filter_controls, text="Застосувати фільтр", 
                  command=self.apply_log_filter).pack(side='left', padx=10)
        
        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_controls, text="Автопрокрутка", 
                       variable=self.autoscroll_var).pack(side='left', padx=5)
        
        # Область для логів
        logs_container = ttk.Frame(main_frame)
        logs_container.pack(fill='both', expand=True)
        
        self.logs_text = scrolledtext.ScrolledText(logs_container, height=20, wrap='word')
        self.logs_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Кнопки управління логами
        logs_buttons = ttk.Frame(main_frame)
        logs_buttons.pack(fill='x', pady=10)
        
        ttk.Button(logs_buttons, text="🗑️ Очистити логи", 
                  command=self.clear_logs).pack(side='left', padx=5)
        ttk.Button(logs_buttons, text="💾 Зберегти логи", 
                  command=self.export_logs).pack(side='left', padx=5)
        ttk.Button(logs_buttons, text="🔄 Оновити", 
                  command=self.refresh_logs).pack(side='left', padx=5)
        
        # Лічильники
        self.logs_counter = ttk.Label(logs_buttons, text="Записів: 0")
        self.logs_counter.pack(side='right', padx=5)
    
    def setup_stats_tab(self):
        """Налаштування вкладки статистики"""
        main_frame = ttk.Frame(self.stats_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Статистика роботи", style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # Загальна статистика
        general_frame = ttk.LabelFrame(main_frame, text="📊 Загальна статистика")
        general_frame.pack(fill='x', pady=(0, 10))
        
        stats_grid = ttk.Frame(general_frame)
        stats_grid.pack(fill='x', padx=10, pady=10)
        
        # Статистика по рядках
        self.total_actions_label = ttk.Label(stats_grid, text="Всього дій: 0")
        self.total_actions_label.grid(row=0, column=0, sticky='w', pady=2)
        
        self.successful_actions_label = ttk.Label(stats_grid, text="Успішних: 0")
        self.successful_actions_label.grid(row=0, column=1, sticky='w', padx=20, pady=2)
        
        self.failed_actions_label = ttk.Label(stats_grid, text="Неуспішних: 0")
        self.failed_actions_label.grid(row=0, column=2, sticky='w', padx=20, pady=2)
        
        self.success_rate_label = ttk.Label(stats_grid, text="Успішність: 0%")
        self.success_rate_label.grid(row=1, column=0, sticky='w', pady=2)
        
        self.active_accounts_label = ttk.Label(stats_grid, text="Активних акаунтів: 0")
        self.active_accounts_label.grid(row=1, column=1, sticky='w', padx=20, pady=2)
        
        # Статистика по акаунтах
        accounts_stats_frame = ttk.LabelFrame(main_frame, text="👥 Статистика по акаунтах")
        accounts_stats_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Таблиця статистики акаунтів
        stats_columns = ('Акаунт', 'Дій сьогодні', 'Всього дій', 'Успішність', 'Статус')
        self.stats_tree = ttk.Treeview(accounts_stats_frame, columns=stats_columns, show='headings', height=10)
        
        for col in stats_columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=120)
        
        stats_scrollbar = ttk.Scrollbar(accounts_stats_frame, orient='vertical', command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        stats_scrollbar.pack(side='right', fill='y', pady=10)
        
        # Кнопки оновлення
        stats_buttons = ttk.Frame(main_frame)
        stats_buttons.pack(fill='x', pady=5)
        
        ttk.Button(stats_buttons, text="🔄 Оновити статистику", 
                  command=self.refresh_stats).pack(side='left', padx=5)
        ttk.Button(stats_buttons, text="📊 Експорт статистики", 
                  command=self.export_stats).pack(side='left', padx=5)
        ttk.Button(stats_buttons, text="🗑️ Очистити статистику", 
                  command=self.clear_stats).pack(side='left', padx=5)

    # Методи для роботи з акаунтами
    def add_account(self):
        """Додавання акаунту"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        proxy = self.proxy_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Помилка", "Заповніть логін та пароль!")
            return
        
        try:
            if not self.bot:
                from instagram_bot import InstagramBot
                self.bot = InstagramBot(self.config.get('captcha_api_key'))
            
            self.bot.account_manager.add_account(username, password, proxy or None)
            
            # Очищення полів
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')
            self.proxy_entry.delete(0, 'end')
            
            self.refresh_accounts()
            self.update_status_bar()
            self.log(f"Акаунт {username} додано успішно!")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка додавання акаунту: {e}")
    
    def remove_account(self):
        """Видалення акаунту"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("Увага", "Виберіть акаунт для видалення!")
            return
        
        item = self.accounts_tree.item(selection[0])
        username = item['values'][0]
        
        if messagebox.askyesno("Підтвердження", f"Видалити акаунт {username}?"):
            try:
                if self.bot:
                    self.bot.account_manager.remove_account(username)
                    self.refresh_accounts()
                    self.update_status_bar()
                    self.log(f"Акаунт {username} видалено!")
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка видалення: {e}")
    
    def refresh_accounts(self):
        """Оновлення списку акаунтів"""
        # Очищення таблиці
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        # Додавання акаунтів
        if self.bot:
            for username, info in self.bot.account_manager.accounts.items():
                self.accounts_tree.insert('', 'end', values=(
                    username,
                    info.get('status', 'unknown'),
                    info.get('actions_count', 0),
                    info.get('last_activity', 'Ніколи'),
                    info.get('proxy', 'Без проксі')[:20] + '...' if info.get('proxy') and len(info.get('proxy', '')) > 20 else info.get('proxy', 'Без проксі')
                ))
    
    def test_account_login(self):
        """Тест входу в акаунт"""
        selection = self.accounts_tree.selection()
        if not selection:
            messagebox.showwarning("Увага", "Виберіть акаунт для тестування!")
            return
        
        item = self.accounts_tree.item(selection[0])
        username = item['values'][0]
        
        def test_login():
            try:
                if not self.bot:
                    from instagram_bot import InstagramBot
                    self.bot = InstagramBot(self.config.get('captcha_api_key'))
                
                success = self.bot.login_account(username)
                if success:
                    self.log(f"✅ Тест входу для {username} успішний!")
                    messagebox.showinfo("Успіх", f"Вхід в акаунт {username} успішний!")
                else:
                    self.log(f"❌ Тест входу для {username} неуспішний!")
                    messagebox.showerror("Помилка", f"Помилка входу в акаунт {username}")
            except Exception as e:
                self.log(f"❌ Помилка тесту для {username}: {e}")
                messagebox.showerror("Помилка", f"Помилка тестування: {e}")
        
        # Запуск в окремому потоці
        threading.Thread(target=test_login, daemon=True).start()
    
    def reset_daily_limits(self):
        """Скидання денних лімітів"""
        if self.bot:
            self.bot.account_manager.reset_daily_limits()
            self.refresh_accounts()
            self.log("Денні ліміти скинуто!")
            messagebox.showinfo("Успіх", "Денні ліміти скинуто!")
    
    # Методи для роботи з цілями
    def add_target(self):
        """Додавання цілі"""
        target = self.target_entry.get().strip()
        if target:
            # Перевірка на дублікати
            current_targets = [self.targets_listbox.get(i) for i in range(self.targets_listbox.size())]
            if target not in current_targets:
                self.targets_listbox.insert('end', target)
                self.target_entry.delete(0, 'end')
                self.update_targets_counter()
                self.update_status_bar()
                self.log(f"Ціль {target} додана!")
            else:
                messagebox.showwarning("Увага", "Ця ціль вже існує!")
    
    def remove_target(self):
        """Видалення цілі"""
        selection = self.targets_listbox.curselection()
        if selection:
            target = self.targets_listbox.get(selection[0])
            self.targets_listbox.delete(selection[0])
            self.update_targets_counter()
            self.update_status_bar()
            self.log(f"Ціль {target} видалена!")
    
    def clear_targets(self):
        """Очищення всіх цілей"""
        if messagebox.askyesno("Підтвердження", "Очистити всі цілі?"):
            self.targets_listbox.delete(0, 'end')
            self.update_targets_counter()
            self.update_status_bar()
            self.log("Всі цілі очищено!")
    
    def update_targets_counter(self):
        """Оновлення лічильника цілей"""
        count = self.targets_listbox.size()
        self.targets_counter.config(text=f"Цілей: {count}")
    
    def import_targets(self):
        """Імпорт цілей з файлу"""
        file_path = filedialog.askopenfilename(
            title="Виберіть файл з цілями",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.endswith('.json'):
                        targets = json.load(f)
                    else:
                        targets = f.read().splitlines()
                
                added_count = 0
                current_targets = [self.targets_listbox.get(i) for i in range(self.targets_listbox.size())]
                
                for target in targets:
                    target = target.strip()
                    if target and target not in current_targets:
                        self.targets_listbox.insert('end', target)
                        current_targets.append(target)
                        added_count += 1
                
                self.update_targets_counter()
                self.update_status_bar()
                self.log(f"Імпортовано {added_count} нових цілей!")
                messagebox.showinfo("Успіх", f"Імпортовано {added_count} нових цілей!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка імпорту: {e}")
    
    def export_targets(self):
        """Експорт цілей до файлу"""
        if self.targets_listbox.size() == 0:
            messagebox.showwarning("Увага", "Немає цілей для експорту!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Зберегти цілі",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                targets = [self.targets_listbox.get(i) for i in range(self.targets_listbox.size())]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.json'):
                        json.dump(targets, f, indent=2, ensure_ascii=False)
                    else:
                        f.write('\n'.join(targets))
                
                self.log(f"Експортовано {len(targets)} цілей!")
                messagebox.showinfo("Успіх", f"Експортовано {len(targets)} цілей!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка експорту: {e}")
    
    # Методи для налаштувань
    def save_settings(self):
        """Збереження налаштувань"""
        try:
            # Збереження API ключа капчі
            self.config.set('captcha_api_key', self.captcha_key_entry.get())
            
            # Збереження проксі
            proxy_text = self.proxy_text.get('1.0', 'end').strip()
            proxy_list = [line.strip() for line in proxy_text.split('\n') if line.strip()]
            self.config.set('proxy_list', proxy_list)
            
            # Збереження затримок
            delays = {}
            try:
                like_range = self.like_delay_entry.get().split('-')
                delays['like'] = [int(like_range[0]), int(like_range[1])]
            except:
                delays['like'] = [2, 5]
            
            try:
                comment_range = self.comment_delay_entry.get().split('-')
                delays['comment'] = [int(comment_range[0]), int(comment_range[1])]
            except:
                delays['comment'] = [3, 8]
            
            try:
                story_range = self.story_delay_entry.get().split('-')
                delays['story_reply'] = [int(story_range[0]), int(story_range[1])]
            except:
                delays['story_reply'] = [1, 3]
            
            self.config.set('action_delays', delays)
            
            # Збереження лімітів
            try:
                daily_limit = int(self.daily_limit_entry.get())
                self.config.set('daily_action_limit', daily_limit)
            except:
                pass
            
            try:
                hourly_limit = int(self.hourly_limit_entry.get())
                automation_settings = self.config.get_automation_settings()
                automation_settings['max_actions_per_hour'] = hourly_limit
                self.config.set('automation_settings', automation_settings)
            except:
                pass
            
            self.log("Налаштування збережено!")
            messagebox.showinfo("Успіх", "Налаштування збережено!")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка збереження: {e}")
    
    def load_settings(self):
        """Завантаження налаштувань"""
        try:
            # Завантаження API ключа
            self.captcha_key_entry.delete(0, 'end')
            self.captcha_key_entry.insert(0, self.config.get('captcha_api_key', ''))
            
            # Завантаження проксі
            proxy_list = self.config.get('proxy_list', [])
            self.proxy_text.delete('1.0', 'end')
            self.proxy_text.insert('1.0', '\n'.join(proxy_list))
            
            # Завантаження затримок
            delays = self.config.get('action_delays', {})
            
            like_delay = delays.get('like', [2, 5])
            self.like_delay_entry.delete(0, 'end')
            self.like_delay_entry.insert(0, f"{like_delay[0]}-{like_delay[1]}")
            
            comment_delay = delays.get('comment', [3, 8])
            self.comment_delay_entry.delete(0, 'end')
            self.comment_delay_entry.insert(0, f"{comment_delay[0]}-{comment_delay[1]}")
            
            story_delay = delays.get('story_reply', [1, 3])
            self.story_delay_entry.delete(0, 'end')
            self.story_delay_entry.insert(0, f"{story_delay[0]}-{story_delay[1]}")
            
            # Завантаження лімітів
            daily_limit = self.config.get('daily_action_limit', 50)
            self.daily_limit_entry.delete(0, 'end')
            self.daily_limit_entry.insert(0, str(daily_limit))
            
            automation_settings = self.config.get_automation_settings()
            hourly_limit = automation_settings.get('max_actions_per_hour', 15)
            self.hourly_limit_entry.delete(0, 'end')
            self.hourly_limit_entry.insert(0, str(hourly_limit))
            
            self.log("Налаштування завантажено!")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка завантаження: {e}")
    
    def reset_settings(self):
        """Скидання налаштувань до стандартних"""
        if messagebox.askyesno("Підтвердження", "Скинути всі налаштування до стандартних?"):
            # Очищення полів
            self.captcha_key_entry.delete(0, 'end')
            self.proxy_text.delete('1.0', 'end')
            
            # Стандартні затримки
            self.like_delay_entry.delete(0, 'end')
            self.like_delay_entry.insert(0, "2-5")
            
            self.comment_delay_entry.delete(0, 'end')
            self.comment_delay_entry.insert(0, "3-8")
            
            self.story_delay_entry.delete(0, 'end')
            self.story_delay_entry.insert(0, "1-3")
            
            self.account_delay_entry.delete(0, 'end')
            self.account_delay_entry.insert(0, "60-180")
            
            # Стандартні ліміти
            self.daily_limit_entry.delete(0, 'end')
            self.daily_limit_entry.insert(0, "50")
            
            self.hourly_limit_entry.delete(0, 'end')
            self.hourly_limit_entry.insert(0, "15")
            
            self.log("Налаштування скинуто до стандартних!")
    
    # Методи для повідомлень
    def add_emoji_messages(self):
        """Додавання емодзі повідомлень"""
        emoji_messages = ["🔥🔥🔥", "❤️", "💯", "🙌", "👏", "😍", "🤩", "💪", "✨", "🎉"]
        current_text = self.messages_text.get('1.0', 'end').strip()
        if current_text:
            current_text += "\n"
        current_text += "\n".join(emoji_messages)
        
        self.messages_text.delete('1.0', 'end')
        self.messages_text.insert('1.0', current_text)
        self.log("Додано емодзі повідомлення!")
    
    def add_positive_messages(self):
        """Додавання позитивних повідомлень"""
        positive_messages = [
            "Круто!", "Супер!", "Класно!", "Чудово!", "Топ!", 
            "Дуже цікаво!", "Красиво!", "Нереально!", "Бомба!"
        ]
        current_text = self.messages_text.get('1.0', 'end').strip()
        if current_text:
            current_text += "\n"
        current_text += "\n".join(positive_messages)
        
        self.messages_text.delete('1.0', 'end')
        self.messages_text.insert('1.0', current_text)
        self.log("Додано позитивні повідомлення!")
    
    def clear_messages(self):
        """Очищення повідомлень"""
        if messagebox.askyesno("Підтвердження", "Очистити всі повідомлення?"):
            self.messages_text.delete('1.0', 'end')
            self.log("Повідомлення очищено!")
    
    # Методи автоматизації
    def start_automation(self):
        """Запуск автоматизації"""
        try:
            # Перевірка наявності акаунтів та цілей
            if not self.bot or not self.bot.account_manager.accounts:
                messagebox.showerror("Помилка", "Додайте хоча б один акаунт!")
                return
            
            if self.targets_listbox.size() == 0:
                messagebox.showerror("Помилка", "Додайте хоча б одну ціль!")
                return
            
            # Ініціалізація бота
            if not self.bot:
                from instagram_bot import InstagramBot
                self.bot = InstagramBot(self.config.get('captcha_api_key'))
            
            # Підготовка конфігурації
            accounts = [{'username': username} for username in self.bot.account_manager.accounts.keys()]
            targets = [self.targets_listbox.get(i) for i in range(self.targets_listbox.size())]
            
            messages = [line.strip() for line in self.messages_text.get('1.0', 'end').split('\n') if line.strip()]
            
            if not messages:
                messages = self.config.get_story_replies()
            
            config = {
                'accounts': accounts,
                'targets': targets,
                'actions': {
                    'like_posts': self.like_posts_var.get(),
                    'like_stories': self.like_stories_var.get(),
                    'reply_stories': self.reply_stories_var.get()
                },
                'story_messages': messages
            }
            
            # Запуск в окремому потоці
            self.automation_thread = threading.Thread(
                target=self.run_automation_thread,
                args=(config,),
                daemon=True
            )
            self.automation_thread.start()
            
            # Оновлення інтерфейсу
            self.automation_running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.pause_button.config(state='normal')
            
            self.automation_status_label.config(text="Статус: Працює", style='Success.TLabel')
            self.status_label.config(text="Статус: Автоматизація запущена")
            
            self.log("🚀 Автоматизація запущена!")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка запуску: {e}")
    
    def run_automation_thread(self, config):
        """Потік виконання автоматизації"""
        try:
            self.bot.run_automation(config)
            self.log("✅ Автоматизація завершена!")
        except Exception as e:
            self.log(f"❌ Помилка автоматизації: {e}")
        finally:
            # Повернення інтерфейсу до початкового стану
            self.root.after(0, self.automation_finished)
    
    def stop_automation(self):
        """Зупинка автоматизації"""
        try:
            self.automation_running = False
            if self.bot:
                self.bot.close_all_drivers()
            
            self.automation_finished()
            self.log("⏹️ Автоматизація зупинена!")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка зупинки: {e}")
    
    def pause_automation(self):
        """Пауза автоматизації"""
        # Реалізація паузи (спрощена версія)
        self.log("⏸️ Автоматизація призупинена!")
    
    def automation_finished(self):
        """Завершення автоматизації"""
        self.automation_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.pause_button.config(state='disabled')
        
        self.automation_status_label.config(text="Статус: Завершено", style='Header.TLabel')
        self.status_label.config(text="Статус: Очікування")
        self.progress_var.set(0)
    
    # Методи для логів
    def setup_logging(self):
        """Налаштування логування"""
        import logging
        
        class GuiLogHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                log_entry = self.format(record)
                self.log_queue.put(log_entry)
        
        # Додавання обробника для GUI
        gui_handler = GuiLogHandler(self.log_queue)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        logger = logging.getLogger()
        logger.addHandler(gui_handler)
        logger.setLevel(logging.INFO)
    
    def process_log_queue(self):
        """Обробка черги логів"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.add_log_entry(log_entry)
        except queue.Empty:
            pass
        
        # Планування наступної обробки
        self.root.after(100, self.process_log_queue)
    
    def add_log_entry(self, log_entry):
        """Додавання запису до логів"""
        self.logs_text.insert('end', log_entry + '\n')
        
        # Автопрокрутка
        if self.autoscroll_var.get():
            self.logs_text.see('end')
        
        # Обмеження кількості рядків (залишаємо останні 1000)
        lines = int(self.logs_text.index('end-1c').split('.')[0])
        if lines > 1000:
            self.logs_text.delete('1.0', f'{lines-1000}.0')
    
    def log(self, message: str):
        """Додавання повідомлення до логів"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.add_log_entry(log_entry)
        
        # Оновлення часу останньої дії
        self.last_action_label.config(text=f"Остання дія: {timestamp}")
    
    def clear_logs(self):
        """Очищення логів"""
        if messagebox.askyesno("Підтвердження", "Очистити всі логи?"):
            self.logs_text.delete('1.0', 'end')
            self.log("Логи очищено!")
    
    def export_logs(self):
        """Експорт логів"""
        file_path = filedialog.asksaveasfilename(
            title="Зберегти логи",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                logs_content = self.logs_text.get('1.0', 'end')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(logs_content)
                self.log("Логи збережено!")
                messagebox.showinfo("Успіх", "Логи збережено!")
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка збереження: {e}")
    
    def apply_log_filter(self):
        """Застосування фільтра логів"""
        filter_level = self.log_level_var.get()
        self.log(f"Застосовано фільтр: {filter_level}")
    
    def refresh_logs(self):
        """Оновлення логів"""
        self.log("🔄 Логи оновлено")
    
    # Методи для статистики
    def refresh_stats(self):
        """Оновлення статистики"""
        try:
            # Очищення таблиці
            for item in self.stats_tree.get_children():
                self.stats_tree.delete(item)
            
            # Оновлення загальної статистики
            total_actions = 0
            successful_actions = 0
            failed_actions = 0
            active_accounts = 0
            
            if self.bot:
                for username, info in self.bot.account_manager.accounts.items():
                    actions_count = info.get('actions_count', 0)
                    status = info.get('status', 'unknown')
                    
                    total_actions += actions_count
                    if status == 'active':
                        active_accounts += 1
                        successful_actions += actions_count
                    else:
                        failed_actions += actions_count
                    
                    # Додавання до таблиці
                    success_rate = "100%" if actions_count > 0 else "0%"
                    self.stats_tree.insert('', 'end', values=(
                        username,
                        actions_count,
                        actions_count,
                        success_rate,
                        status
                    ))
            
            # Оновлення лейблів
            self.total_actions_label.config(text=f"Всього дій: {total_actions}")
            self.successful_actions_label.config(text=f"Успішних: {successful_actions}")
            self.failed_actions_label.config(text=f"Неуспішних: {failed_actions}")
            self.active_accounts_label.config(text=f"Активних акаунтів: {active_accounts}")
            
            # Розрахунок успішності
            if total_actions > 0:
                success_rate = (successful_actions / total_actions) * 100
                self.success_rate_label.config(text=f"Успішність: {success_rate:.1f}%")
            else:
                self.success_rate_label.config(text="Успішність: 0%")
            
            self.log("📊 Статистика оновлена")
            
        except Exception as e:
            self.log(f"❌ Помилка оновлення статистики: {e}")
    
    def export_stats(self):
        """Експорт статистики"""
        file_path = filedialog.asksaveasfilename(
            title="Зберегти статистику",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("Text files", "*.txt")]
        )
        
        if file_path:
            try:
                stats_data = {
                    'timestamp': datetime.now().isoformat(),
                    'accounts': {},
                    'summary': {
                        'total_actions': 0,
                        'successful_actions': 0,
                        'failed_actions': 0,
                        'active_accounts': 0
                    }
                }
                
                if self.bot:
                    for username, info in self.bot.account_manager.accounts.items():
                        stats_data['accounts'][username] = info
                        stats_data['summary']['total_actions'] += info.get('actions_count', 0)
                        if info.get('status') == 'active':
                            stats_data['summary']['active_accounts'] += 1
                
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(stats_data, f, indent=2, ensure_ascii=False)
                elif file_path.endswith('.csv'):
                    import csv
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Акаунт', 'Дій сьогодні', 'Статус', 'Остання активність'])
                        for username, info in stats_data['accounts'].items():
                            writer.writerow([
                                username,
                                info.get('actions_count', 0),
                                info.get('status', 'unknown'),
                                info.get('last_activity', 'Ніколи')
                            ])
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("=== СТАТИСТИКА INSTAGRAM BOT ===\n\n")
                        f.write(f"Час створення: {stats_data['timestamp']}\n")
                        f.write(f"Всього дій: {stats_data['summary']['total_actions']}\n")
                        f.write(f"Активних акаунтів: {stats_data['summary']['active_accounts']}\n\n")
                        f.write("=== ДЕТАЛІ ПО АКАУНТАХ ===\n")
                        for username, info in stats_data['accounts'].items():
                            f.write(f"\n{username}:\n")
                            f.write(f"  Дій: {info.get('actions_count', 0)}\n")
                            f.write(f"  Статус: {info.get('status', 'unknown')}\n")
                            f.write(f"  Остання активність: {info.get('last_activity', 'Ніколи')}\n")
                
                self.log("📊 Статистика експортована!")
                messagebox.showinfo("Успіх", "Статистика експортована!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка експорту: {e}")
    
    def clear_stats(self):
        """Очищення статистики"""
        if messagebox.askyesno("Підтвердження", "Очистити всю статистику?"):
            if self.bot:
                self.bot.account_manager.reset_daily_limits()
                self.refresh_stats()
                self.log("📊 Статистика очищена!")
    
    # Додаткові методи
    def update_status_bar(self):
        """Оновлення панелі статусу"""
        accounts_count = len(self.bot.account_manager.accounts) if self.bot else 0
        targets_count = self.targets_listbox.size()
        
        self.accounts_count_label.config(text=f"Акаунти: {accounts_count}")
        self.targets_count_label.config(text=f"Цілі: {targets_count}")
    
    def load_saved_data(self):
        """Завантаження збережених даних"""
        try:
            # Завантаження налаштувань
            self.load_settings()
            
            # Ініціалізація бота
            from instagram_bot import InstagramBot
            self.bot = InstagramBot(self.config.get('captcha_api_key'))
            
            # Оновлення інтерфейсу
            self.refresh_accounts()
            self.update_status_bar()
            
        except Exception as e:
            self.log(f"⚠️ Помилка завантаження даних: {e}")
    
    # Методи меню
    def import_accounts(self):
        """Імпорт акаунтів з файлу"""
        file_path = filedialog.askopenfilename(
            title="Виберіть файл з акаунтами",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                if not self.bot:
                    from instagram_bot import InstagramBot
                    self.bot = InstagramBot(self.config.get('captcha_api_key'))
                
                added_count = 0
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.endswith('.json'):
                        accounts_data = json.load(f)
                        for account in accounts_data:
                            username = account.get('username')
                            password = account.get('password')
                            proxy = account.get('proxy')
                            if username and password:
                                self.bot.account_manager.add_account(username, password, proxy)
                                added_count += 1
                    else:
                        for line in f:
                            parts = line.strip().split(':')
                            if len(parts) >= 2:
                                username = parts[0]
                                password = parts[1]
                                proxy = ':'.join(parts[2:]) if len(parts) > 2 else None
                                self.bot.account_manager.add_account(username, password, proxy)
                                added_count += 1
                
                self.refresh_accounts()
                self.update_status_bar()
                self.log(f"📥 Імпортовано {added_count} акаунтів!")
                messagebox.showinfo("Успіх", f"Імпортовано {added_count} акаунтів!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка імпорту: {e}")
    
    def export_accounts(self):
        """Експорт акаунтів до файлу"""
        if not self.bot or not self.bot.account_manager.accounts:
            messagebox.showwarning("Увага", "Немає акаунтів для експорту!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Зберегти акаунти",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    accounts_data = []
                    for username, info in self.bot.account_manager.accounts.items():
                        accounts_data.append({
                            'username': username,
                            'password': info['password'],
                            'proxy': info.get('proxy'),
                            'status': info.get('status'),
                            'actions_count': info.get('actions_count', 0)
                        })
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(accounts_data, f, indent=2, ensure_ascii=False)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for username, info in self.bot.account_manager.accounts.items():
                            line = f"{username}:{info['password']}"
                            if info.get('proxy'):
                                line += f":{info['proxy']}"
                            f.write(line + '\n')
                
                self.log(f"📤 Експортовано {len(self.bot.account_manager.accounts)} акаунтів!")
                messagebox.showinfo("Успіх", f"Експортовано {len(self.bot.account_manager.accounts)} акаунтів!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка експорту: {e}")
    
    def import_config(self):
        """Імпорт конфігурації"""
        file_path = filedialog.askopenfilename(
            title="Виберіть файл конфігурації",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            if self.config.import_config(file_path):
                self.load_settings()
                self.log("📥 Конфігурацію імпортовано!")
                messagebox.showinfo("Успіх", "Конфігурацію імпортовано!")
            else:
                messagebox.showerror("Помилка", "Помилка імпорту конфігурації!")
    
    def export_config(self):
        """Експорт конфігурації"""
        file_path = filedialog.asksaveasfilename(
            title="Зберегти конфігурацію",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            if self.config.export_config(file_path):
                self.log("📤 Конфігурацію експортовано!")
                messagebox.showinfo("Успіх", "Конфігурацію експортовано!")
            else:
                messagebox.showerror("Помилка", "Помилка експорту конфігурації!")
    
    def test_proxies(self):
        """Тестування проксі"""
        proxy_text = self.proxy_text.get('1.0', 'end').strip()
        if not proxy_text:
            messagebox.showwarning("Увага", "Додайте проксі для тестування!")
            return
        
        def test_proxies_thread():
            try:
                from utils import ProxyManager
                proxy_manager = ProxyManager()
                
                proxy_list = [line.strip() for line in proxy_text.split('\n') if line.strip()]
                self.log(f"🔍 Тестування {len(proxy_list)} проксі...")
                
                working_count = 0
                for proxy in proxy_list:
                    proxy_manager.add_proxy(proxy)
                    if proxy_manager.test_proxy(proxy):
                        working_count += 1
                        self.log(f"✅ Проксі {proxy} працює")
                    else:
                        self.log(f"❌ Проксі {proxy} не працює")
                
                self.log(f"📊 Результат: {working_count}/{len(proxy_list)} проксі працюють")
                
                def show_result():
                    messagebox.showinfo("Результат", 
                                      f"Працюючих проксі: {working_count} з {len(proxy_list)}")
                
                self.root.after(0, show_result)
                
            except Exception as e:
                self.log(f"❌ Помилка тестування проксі: {e}")
        
        threading.Thread(target=test_proxies_thread, daemon=True).start()
    
    def restart_bot(self):
        """Перезапуск бота"""
        if messagebox.askyesno("Підтвердження", "Перезапустити бота? Всі активні сесії будуть закриті."):
            try:
                if self.bot:
                    self.bot.close_all_drivers()
                
                from instagram_bot import InstagramBot
                self.bot = InstagramBot(self.config.get('captcha_api_key'))
                
                self.refresh_accounts()
                self.update_status_bar()
                self.log("🔄 Бот перезапущено!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка перезапуску: {e}")
    
    def show_about(self):
        """Показати інформацію про програму"""
        about_text = """
Instagram Automation Bot v2.0

🤖 Функціональність:
• Автоматичне лайкання постів
• Лайки сторіс та відповіді
• Мультиакаунтність
• Обхід систем захисту
• Розв'язання капчі
• Ротація проксі

🛡️ Безпека:
• Обхід капчі
• Детекція ботів
• IP блокування
• Shadowban захист
• Постійні бани

⚙️ Особливості:
• GUI інтерфейс
• CLI режим
• Планувальник
• Статистика
• Логування

📧 Підтримка: telegram @your_username
🌐 Версія: 2.0.0
📅 Дата: 2024
        """
        messagebox.showinfo("Про програму", about_text)
    
    def show_help(self):
        """Показати інструкцію"""
        help_text = """
📖 ІНСТРУКЦІЯ ПО ВИКОРИСТАННЮ:

1️⃣ ДОДАВАННЯ АКАУНТІВ:
   • Перейдіть на вкладку "🔐 Акаунти"
   • Введіть логін, пароль та проксі (опціонально)
   • Натисніть "Додати"

2️⃣ НАЛАШТУВАННЯ ЦІЛЕЙ:
   • Вкладка "🎯 Цілі"
   • Додайте імена користувачів для автоматизації
   • Можна імпортувати з файлу

3️⃣ КОНФІГУРАЦІЯ:
   • Вкладка "⚙️ Налаштування"
   • Налаштуйте затримки та ліміти
   • Додайте API ключ капчі (опціонально)
   • Налаштуйте проксі

4️⃣ АВТОМАТИЗАЦІЯ:
   • Вкладка "🤖 Автоматизація"
   • Виберіть дії для виконання:
     - Лайкати останні 2 пости
     - Лайкати сторіс
     - Відповідати на сторіс
   • Налаштуйте повідомлення для сторіс
   • Натисніть "▶️ Запустити автоматизацію"

5️⃣ МОНІТОРИНГ:
   • Слідкуйте за процесом у вкладці "📋 Логи"
   • Переглядайте статистику у вкладці "📊 Статистика"

🔒 БЕЗПЕКА:
   • Використовуйте помірні налаштування
   • Не перевищуйте ліміти (50-100 дій на день)
   • Робіть перерви між сесіями
   • Використовуйте проксі для кожного акаунту

⚠️ ВАЖЛИВО:
   • Дотримуйтесь умов використання Instagram
   • Не спамте користувачів
   • Регулярно перевіряйте стан акаунтів
   • Робіть резервні копії даних
        """
        
        # Створення окремого вікна для інструкції
        help_window = tk.Toplevel(self.root)
        help_window.title("Інструкція")
        help_window.geometry("700x600")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Центрування вікна
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (help_window.winfo_width() // 2)
        y = (help_window.winfo_screenheight() // 2) - (help_window.winfo_height() // 2)
        help_window.geometry(f"+{x}+{y}")
        
        help_text_widget = scrolledtext.ScrolledText(help_window, wrap='word', font=('Arial', 10))
        help_text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        help_text_widget.insert('1.0', help_text)
        help_text_widget.config(state='disabled')
        
        # Кнопка закриття
        close_button = ttk.Button(help_window, text="Закрити", command=help_window.destroy)
        close_button.pack(pady=10)


def main():
    """Запуск GUI"""
    root = tk.Tk()
    app = InstagramBotGUI(root)
    
    # Обробка закриття вікна
    def on_closing():
        if hasattr(app, 'automation_running') and app.automation_running:
            if messagebox.askokcancel("Вихід", "Автоматизація працює. Завершити роботу?"):
                if hasattr(app, 'stop_automation'):
                    app.stop_automation()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Встановлення мінімального розміру вікна
    root.minsize(1000, 700)
    
    # Центрування вікна
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Встановлення іконки (якщо є)
    try:
        # Можна додати іконку програми
        # root.iconbitmap('icon.ico')
        pass
    except:
        pass
    
    print("🚀 Instagram Bot GUI запущено!")
    root.mainloop()


if __name__ == "__main__":
    main()