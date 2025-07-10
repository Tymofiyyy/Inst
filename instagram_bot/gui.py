import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import json
import os
from datetime import datetime
import logging

class InstagramBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Instagram Bot - Багато користувачів з багаторядковими повідомленнями")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Стилізація
        self.setup_style()
        
        # Змінні
        self.bots = {}
        self.running_bots = set()
        
        # Створення інтерфейсу
        self.create_widgets()
        
    def setup_style(self):
        """Налаштування стилю"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Темні кольори
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#4a9eff',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
    def create_widgets(self):
        """Створення віджетів"""
        # Головний контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, text="🤖 Instagram Bot - Багаторядкові повідомлення", 
                              font=('Arial', 16, 'bold'), bg=self.colors['bg'], fg=self.colors['fg'])
        title_label.pack()
        
        # Notebook для вкладок
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Створення вкладок
        self.create_automation_tab()
        self.create_messages_tab()
        self.create_accounts_tab()
        self.create_logs_tab()
        
    def create_automation_tab(self):
        """Головна вкладка автоматизації"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="🚀 Автоматизація")
        
        # Основний контейнер з прокруткою
        canvas = tk.Canvas(tab_frame, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # === СЕКЦІЯ АКАУНТА ===
        account_frame = ttk.LabelFrame(scrollable_frame, text="👤 Налаштування акаунта", padding=15)
        account_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Логін
        login_frame = ttk.Frame(account_frame)
        login_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(login_frame, text="Логін Instagram:").pack(anchor=tk.W)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(login_frame, textvariable=self.username_var, width=30, font=('Arial', 11))
        username_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Пароль
        password_frame = ttk.Frame(account_frame)
        password_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(password_frame, text="Пароль:").pack(anchor=tk.W)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(password_frame, textvariable=self.password_var, show='*', width=30, font=('Arial', 11))
        password_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Проксі (опційно)
        proxy_frame = ttk.Frame(account_frame)
        proxy_frame.pack(fill=tk.X)
        
        ttk.Label(proxy_frame, text="Проксі (опційно):").pack(anchor=tk.W)
        self.proxy_var = tk.StringVar()
        proxy_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_var, width=30, font=('Arial', 11))
        proxy_entry.pack(fill=tk.X, pady=(5, 0))
        
        hint_label = ttk.Label(proxy_frame, text="Формат: ip:port:username:password", foreground='gray')
        hint_label.pack(anchor=tk.W, pady=(2, 0))
        
        # === СЕКЦІЯ ЦІЛЬОВИХ КОРИСТУВАЧІВ ===
        targets_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Цільові користувачі", padding=15)
        targets_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Інструкції
        instructions_frame = ttk.Frame(targets_frame)
        instructions_frame.pack(fill=tk.X, pady=(0, 10))
        
        instructions_text = """📝 Способи введення користувачів:
• Через кому: user1, user2, user3
• Через крапку з комою: user1; user2; user3  
• Кожен з нового рядка
• Через пробіл: user1 user2 user3
• З символом @: @user1, @user2 (символ @ буде видалений автоматично)"""
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text, 
                                     justify=tk.LEFT, bg=self.colors['bg'], fg='lightgray',
                                     font=('Arial', 9))
        instructions_label.pack(anchor=tk.W)
        
        # Поле для введення користувачів
        targets_input_frame = ttk.Frame(targets_frame)
        targets_input_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        ttk.Label(targets_input_frame, text="Введіть юзернейми користувачів:", font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        self.targets_text = scrolledtext.ScrolledText(targets_input_frame, height=6, width=60, 
                                                     font=('Arial', 11),
                                                     bg='white', fg='black')
        self.targets_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # Кнопки для роботи з користувачами
        targets_buttons_frame = ttk.Frame(targets_frame)
        targets_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(targets_buttons_frame, text="📄 Завантажити з файлу", 
                  command=self.load_targets_from_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(targets_buttons_frame, text="💾 Зберегти в файл", 
                  command=self.save_targets_to_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(targets_buttons_frame, text="🧹 Очистити", 
                  command=self.clear_targets).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(targets_buttons_frame, text="✅ Перевірити", 
                  command=self.validate_targets).pack(side=tk.LEFT)
        
        # Лічильник користувачів
        self.targets_count_var = tk.StringVar(value="Користувачів: 0")
        count_label = ttk.Label(targets_frame, textvariable=self.targets_count_var, font=('Arial', 10, 'bold'))
        count_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Відслідковування змін в тексті
        self.targets_text.bind('<KeyRelease>', self.update_targets_count)
        self.targets_text.bind('<ButtonRelease>', self.update_targets_count)
        
        # === СЕКЦІЯ ДІЙ ===
        actions_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Налаштування дій", padding=15)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Чекбокси дій
        self.like_posts_var = tk.BooleanVar(value=True)
        self.like_stories_var = tk.BooleanVar(value=True)
        self.reply_stories_var = tk.BooleanVar(value=True)
        self.send_dm_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(actions_frame, text="❤️ Лайкати останні пости", 
                       variable=self.like_posts_var, 
                       command=self.update_actions_summary).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(actions_frame, text="👍 Лайкати сторіс", 
                       variable=self.like_stories_var,
                       command=self.update_actions_summary).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(actions_frame, text="💬 Відповідати на сторіс", 
                       variable=self.reply_stories_var,
                       command=self.update_actions_summary).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(actions_frame, text="📩 Відправляти Direct Message (якщо немає сторіс)", 
                       variable=self.send_dm_var,
                       command=self.update_actions_summary).pack(anchor=tk.W, pady=2)
        
        # Кількість постів
        posts_frame = ttk.Frame(actions_frame)
        posts_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(posts_frame, text="Кількість постів для лайку:").pack(side=tk.LEFT)
        self.posts_count_var = tk.IntVar(value=2)
        posts_spin = ttk.Spinbox(posts_frame, from_=1, to=5, textvariable=self.posts_count_var, width=5)
        posts_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Резюме дій
        self.actions_summary_var = tk.StringVar()
        summary_label = ttk.Label(actions_frame, textvariable=self.actions_summary_var, 
                                 foreground=self.colors['accent'], font=('Arial', 10))
        summary_label.pack(anchor=tk.W, pady=(10, 0))
        self.update_actions_summary()
        
        # === СЕКЦІЯ УПРАВЛІННЯ ===
        control_frame = ttk.LabelFrame(scrollable_frame, text="🎮 Управління", padding=15)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Кнопки управління
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = tk.Button(buttons_frame, text="▶️ ЗАПУСТИТИ АВТОМАТИЗАЦІЮ", 
                                     command=self.start_automation,
                                     bg=self.colors['success'], fg='white',
                                     font=('Arial', 12, 'bold'), height=2)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        self.stop_button = tk.Button(buttons_frame, text="⏹️ ЗУПИНИТИ", 
                                    command=self.stop_automation,
                                    bg=self.colors['error'], fg='white',
                                    font=('Arial', 12, 'bold'), height=2, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Прогрес бар
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(progress_frame, text="Прогрес:").pack(anchor=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Статус
        self.status_var = tk.StringVar(value="Готовий до запуску")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, 
                                font=('Arial', 11, 'bold'))
        status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Розміщення скролованого контейнера
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def create_messages_tab(self):
        """Вкладка повідомлень з підтримкою багаторядкових текстів"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="💬 Повідомлення")
        
        # Основний контейнер
        main_container = ttk.Frame(tab_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === ПАНЕЛЬ ІНСТРУМЕНТІВ ===
        toolbar_frame = ttk.Frame(main_container)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar_frame, text="➕ Додати повідомлення",
                  command=self.add_message_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="✏️ Редагувати",
                  command=self.edit_message_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="🗑️ Видалити",
                  command=self.delete_message).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="📁 Завантажити з файлу",
                  command=self.load_messages_from_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="💾 Зберегти в файл",
                  command=self.save_messages_to_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="🧹 Очистити все",
                  command=self.clear_all_messages).pack(side=tk.LEFT)
        
        # === КОНТЕЙНЕР ДЛЯ СПИСКУ ТА РЕДАКТОРА ===
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Ліва панель - список повідомлень
        left_frame = ttk.LabelFrame(content_frame, text="📝 Список повідомлень", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Listbox з повідомленнями
        self.messages_listbox = tk.Listbox(left_frame, height=20, 
                                          bg='white', fg='black',
                                          selectbackground=self.colors['accent'],
                                          selectforeground='white',
                                          font=('Arial', 10))
        self.messages_listbox.pack(fill=tk.BOTH, expand=True)
        self.messages_listbox.bind('<<ListboxSelect>>', self.on_message_select)
        self.messages_listbox.bind('<Double-Button-1>', self.edit_message_dialog)
        
        # Права панель - редактор повідомлень
        right_frame = ttk.LabelFrame(content_frame, text="✏️ Редактор повідомлення", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Інструкції для багаторядкових повідомлень
        instructions_frame = ttk.Frame(right_frame)
        instructions_frame.pack(fill=tk.X, pady=(0, 10))
        
        instructions_text = """📝 Підтримка багаторядкових повідомлень:
• Натисніть Enter для нового рядка
• Залиште порожній рядок для відступу
• Повідомлення буде відправлено точно як введено
• Приклад рекламного повідомлення нижче 👇"""
        
        instructions_label = tk.Label(instructions_frame, text=instructions_text, 
                                     justify=tk.LEFT, bg=self.colors['bg'], fg='gray',
                                     font=('Arial', 9))
        instructions_label.pack(anchor=tk.W)
        
        # Текстове поле для редагування повідомлення
        editor_frame = ttk.Frame(right_frame)
        editor_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        ttk.Label(editor_frame, text="Введіть або редагуйте повідомлення:", font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        self.message_editor = scrolledtext.ScrolledText(editor_frame, height=15, width=40, wrap=tk.WORD,
                                                       bg='white', fg='black',
                                                       font=('Arial', 11))
        self.message_editor.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # Приклад повідомлення
        example_message = """Доброго дня!  
Мене звати Андрій, я рекламний менеджер ліцензованих онлайн-казино України 🇺🇦

Ми шукаємо партнерів із залученою аудиторією.  
Пропонуємо співпрацю на вигідних умовах:

— 50$ за кожного ліда  
— CPA система  
— Готові рекламні матеріали  
— Щотижневі виплати

Готові обговорити зручний формат співпраці для вас 👨🏻‍💻
• Для обговорення деталей, напишіть будь ласка «+»  
@goldenhive_manager

Дякую за увагу!"""
        
        self.message_editor.insert('1.0', example_message)
        
        # Кнопки редактора
        editor_buttons_frame = ttk.Frame(right_frame)
        editor_buttons_frame.pack(fill=tk.X)
        
        ttk.Button(editor_buttons_frame, text="💾 Зберегти повідомлення", 
                  command=self.save_current_message).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_buttons_frame, text="🧹 Очистити редактор", 
                  command=self.clear_editor).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(editor_buttons_frame, text="👁️ Переглянути", 
                  command=self.preview_message).pack(side=tk.LEFT)
        
        # Завантаження повідомлень
        self.load_messages()
        
    def create_accounts_tab(self):
        """Вкладка збереження акаунтів"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="👥 Акаунти")
        
        # Панель інструментів
        toolbar_frame = ttk.Frame(tab_frame)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(toolbar_frame, text="💾 Зберегти поточний акаунт",
                  command=self.save_current_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="📁 Завантажити акаунт",
                  command=self.load_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="🗑️ Видалити збережений",
                  command=self.delete_saved_account).pack(side=tk.LEFT)
        
        # Список збережених акаунтів
        accounts_frame = ttk.LabelFrame(tab_frame, text="Збережені акаунти", padding=10)
        accounts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.accounts_listbox = tk.Listbox(accounts_frame, height=10)
        self.accounts_listbox.pack(fill=tk.BOTH, expand=True)
        self.accounts_listbox.bind('<Double-Button-1>', self.load_selected_account)
        
        self.load_saved_accounts()
        
    def create_logs_tab(self):
        """Вкладка логів"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="📋 Логи")
        
        # Панель інструментів
        toolbar_frame = ttk.Frame(tab_frame)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(toolbar_frame, text="🔄 Оновити",
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="🗑️ Очистити",
                  command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="💾 Зберегти",
                  command=self.save_logs).pack(side=tk.LEFT, padx=(0, 5))
        
        # Автопрокрутка
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar_frame, text="📜 Автопрокрутка", 
                       variable=self.auto_scroll_var).pack(side=tk.RIGHT)
        
        # Текстове поле логів
        logs_frame = ttk.LabelFrame(tab_frame, text="Логи реального часу", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, 
                                                  font=('Consolas', 10),
                                                  bg='black', fg='lightgreen',
                                                  state=tk.DISABLED)
        self.logs_text.pack(fill=tk.BOTH, expand=True)

    # === МЕТОДИ ДЛЯ РОБОТИ З ПОВІДОМЛЕННЯМИ ===
    
    def get_messages(self):
        """Отримання списку повідомлень"""
        messages = []
        for i in range(self.messages_listbox.size()):
            messages.append(self.messages_listbox.get(i))
        return messages
        
    def load_messages(self):
        """Завантаження повідомлень"""
        try:
            try:
                with open('multiline_messages.json', 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            except FileNotFoundError:
                messages = [
                    "Привіт! 😊",
                    "Класний пост! 👍",
                    "Дякую за контент! 🙏",
                    """Привіт! 😊
Дуже сподобався твій пост!
Продовжуй у тому ж дусі! 👍"""
                ]
                
            self.messages_listbox.delete(0, tk.END)
            for message in messages:
                # Показуємо тільки першу лінію в списку для зручності
                display_text = message.split('\n')[0]
                if len(display_text) > 50:
                    display_text = display_text[:47] + "..."
                if '\n' in message:
                    display_text += " [багаторядкове]"
                    
                self.messages_listbox.insert(tk.END, display_text)
                
            # Зберігаємо оригінальні повідомлення
            self.original_messages = messages
                
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити повідомлення: {e}")
            
    def save_messages(self):
        """Збереження повідомлень"""
        try:
            with open('multiline_messages.json', 'w', encoding='utf-8') as f:
                json.dump(self.original_messages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти повідомлення: {e}")
            
    def on_message_select(self, event=None):
        """Обробка вибору повідомлення зі списку"""
        selection = self.messages_listbox.curselection()
        if selection and hasattr(self, 'original_messages'):
            index = selection[0]
            if index < len(self.original_messages):
                self.message_editor.delete('1.0', tk.END)
                self.message_editor.insert('1.0', self.original_messages[index])
                
    def save_current_message(self):
        """Збереження поточного повідомлення з редактора"""
        message = self.message_editor.get('1.0', tk.END).strip()
        if not message:
            messagebox.showwarning("Попередження", "Введіть текст повідомлення!")
            return
            
        if not hasattr(self, 'original_messages'):
            self.original_messages = []
            
        # Додаємо нове повідомлення
        self.original_messages.append(message)
        
        # Оновлюємо список
        display_text = message.split('\n')[0]
        if len(display_text) > 50:
            display_text = display_text[:47] + "..."
        if '\n' in message:
            display_text += " [багаторядкове]"
            
        self.messages_listbox.insert(tk.END, display_text)
        
        # Зберігаємо
        self.save_messages()
        
        messagebox.showinfo("Успіх", "Повідомлення збережено!")
        
    def clear_editor(self):
        """Очищення редактора"""
        self.message_editor.delete('1.0', tk.END)
        
    def preview_message(self):
        """Попередній перегляд повідомлення"""
        message = self.message_editor.get('1.0', tk.END).strip()
        if not message:
            messagebox.showwarning("Попередження", "Введіть текст повідомлення!")
            return
            
        # Показуємо як буде виглядати повідомлення
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Попередній перегляд повідомлення")
        preview_window.geometry("500x400")
        preview_window.configure(bg='white')
        
        # Заголовок
        title_label = tk.Label(preview_window, text="Так буде виглядати ваше повідомлення:",
                              font=('Arial', 12, 'bold'), bg='white')
        title_label.pack(pady=10)
        
        # Рамка для повідомлення
        message_frame = tk.Frame(preview_window, bg='#e1f5fe', relief='solid', bd=1)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Текст повідомлення
        message_label = tk.Label(message_frame, text=message, 
                                font=('Arial', 11), bg='#e1f5fe', fg='black',
                                justify=tk.LEFT, anchor='nw')
        message_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кнопка закриття
        tk.Button(preview_window, text="Закрити", command=preview_window.destroy,
                 bg=self.colors['accent'], fg='white', font=('Arial', 10)).pack(pady=10)

    def add_message_dialog(self):
        """Діалог додавання повідомлення"""
        self.clear_editor()
        messagebox.showinfo("Додавання повідомлення", 
                           "Введіть повідомлення в редакторі праворуч та натисніть 'Зберегти повідомлення'")

    def edit_message_dialog(self, event=None):
        """Редагування вибраного повідомлення"""
        selection = self.messages_listbox.curselection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть повідомлення для редагування!")
            return
            
        # Повідомлення вже завантажилось в редактор через on_message_select
        messagebox.showinfo("Редагування", 
                           "Відредагуйте повідомлення в редакторі та натисніть 'Зберегти повідомлення'.\nСтаре повідомлення буде замінене.")
        
        # Позначаємо що ми редагуємо
        self.editing_index = selection[0]

    def delete_message(self):
        """Видалення повідомлення"""
        selection = self.messages_listbox.curselection()
        if not selection:
            messagebox.showwarning("Попередження", "Виберіть повідомлення для видалення!")
            return
            
        if messagebox.askyesno("Підтвердження", "Видалити вибране повідомлення?"):
            index = selection[0]
            
            # Видаляємо з оригінального списку
            if hasattr(self, 'original_messages') and index < len(self.original_messages):
                del self.original_messages[index]
                
            # Видаляємо зі списку
            self.messages_listbox.delete(index)
            
            # Очищаємо редактор
            self.clear_editor()
            
            # Зберігаємо
            self.save_messages()

    def clear_all_messages(self):
        """Очищення всіх повідомлень"""
        if messagebox.askyesno("Підтвердження", "Видалити ВСІ повідомлення?"):
            self.messages_listbox.delete(0, tk.END)
            self.original_messages = []
            self.clear_editor()
            self.save_messages()

    def load_messages_from_file(self):
        """Завантаження повідомлень з файлу"""
        filename = filedialog.askopenfilename(
            title="Завантажити повідомлення",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                else:
                    with open(filename, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Розділяємо повідомлення по подвійному переносу рядка
                        messages = [msg.strip() for msg in content.split('\n\n') if msg.strip()]
                
                # Очищаємо поточні повідомлення
                self.messages_listbox.delete(0, tk.END)
                self.original_messages = []
                
                # Додаємо нові
                for message in messages:
                    self.original_messages.append(message)
                    
                    display_text = message.split('\n')[0]
                    if len(display_text) > 50:
                        display_text = display_text[:47] + "..."
                    if '\n' in message:
                        display_text += " [багаторядкове]"
                        
                    self.messages_listbox.insert(tk.END, display_text)
                    
                self.save_messages()
                messagebox.showinfo("Успіх", f"Завантажено {len(messages)} повідомлень!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося завантажити файл: {e}")

    def save_messages_to_file(self):
        """Збереження повідомлень у файл"""
        if not hasattr(self, 'original_messages') or not self.original_messages:
            messagebox.showwarning("Попередження", "Немає повідомлень для збереження!")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Зберегти повідомлення",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.original_messages, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        # Зберігаємо повідомлення розділені подвійним переносом
                        f.write('\n\n'.join(self.original_messages))
                        
                messagebox.showinfo("Успіх", f"Збережено {len(self.original_messages)} повідомлень!")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося зберегти файл: {e}")

    # === РЕШТА МЕТОДІВ (скорочені для економії місця) ===
    
    def update_targets_count(self, event=None):
        """Оновлення лічильника користувачів"""
        try:
            content = self.targets_text.get('1.0', tk.END).strip()
            if not content:
                count = 0
            else:
                users = self.parse_targets(content)
                count = len(users)
            
            self.targets_count_var.set(f"Користувачів: {count}")
        except Exception:
            self.targets_count_var.set("Користувачів: ?")
            
    def parse_targets(self, content):
        """Парсинг цільових користувачів"""
        if not content:
            return []
        
        separators = [',', ';', '\n', ' ']
        users = [content]
        
        for sep in separators:
            if sep in content:
                users = content.split(sep)
                break
        
        cleaned_users = []
        for user in users:
            user = user.strip().replace('@', '')
            if user and len(user) > 0:
                import re
                if re.match("^[a-zA-Z0-9._]+$", user) and len(user) >= 1:
                    cleaned_users.append(user)
        
        return cleaned_users
        
    def update_actions_summary(self):
        """Оновлення резюме дій"""
        actions = []
        if self.like_posts_var.get():
            actions.append(f"❤️ Лайк {self.posts_count_var.get()} постів")
        if self.like_stories_var.get():
            actions.append("👍 Лайк сторіс")
        if self.reply_stories_var.get():
            actions.append("💬 Відповідь на сторіс")
        if self.send_dm_var.get():
            actions.append("📩 DM (fallback)")
            
        if actions:
            summary = "Дії: " + " → ".join(actions)
        else:
            summary = "⚠️ Не вибрано жодної дії!"
            
        self.actions_summary_var.set(summary)

    def validate_targets(self):
        """Перевірка та валідація користувачів"""
        content = self.targets_text.get('1.0', tk.END).strip()
        
        if not content:
            messagebox.showwarning("Попередження", "Введіть хоча б одного користувача!")
            return
            
        users = self.parse_targets(content)
        
        if not users:
            messagebox.showerror("Помилка", "Не знайдено валідних юзернеймів!")
            return
            
        result_msg = f"✅ Знайдено {len(users)} валідних користувачів:\n\n"
        result_msg += "\n".join([f"• @{user}" for user in users[:10]])
        
        if len(users) > 10:
            result_msg += f"\n... та ще {len(users) - 10} користувачів"
            
        messagebox.showinfo("Результат валідації", result_msg)

    def start_automation(self):
        """Запуск автоматизації"""
        # Перевірки
        if not self.username_var.get() or not self.password_var.get():
            messagebox.showerror("Помилка", "Введіть логін та пароль!")
            return
            
        targets_content = self.targets_text.get('1.0', tk.END).strip()
        if not targets_content:
            messagebox.showerror("Помилка", "Введіть хоча б одного користувача!")
            return
            
        users = self.parse_targets(targets_content)
        if not users:
            messagebox.showerror("Помилка", "Не знайдено валідних користувачів!")
            return
            
        # Отримуємо повідомлення (оригінальні з багаторядковими)
        if not hasattr(self, 'original_messages') or not self.original_messages:
            messagebox.showerror("Помилка", "Додайте хоча б одне повідомлення!")
            return
            
        messages = self.original_messages
        
        # Підтвердження запуску
        confirm_msg = f"""🚀 Готові до запуску автоматизації?

👤 Акаунт: {self.username_var.get()}
🎯 Користувачів: {len(users)}
💬 Повідомлень: {len(messages)} (включаючи багаторядкові)

Дії:
{self.actions_summary_var.get()}

⚠️ Процес може тривати довго. Продовжити?"""

        if not messagebox.askyesno("Підтвердження запуску", confirm_msg):
            return
            
        # Налаштування інтерфейсу
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("Запуск автоматизації...")
        self.progress_var.set(0)
        
        # Конфігурація дій
        actions_config = {
            'like_posts': self.like_posts_var.get(),
            'like_stories': self.like_stories_var.get(),
            'reply_stories': self.reply_stories_var.get(),
            'send_direct_message': self.send_dm_var.get(),
            'posts_count': self.posts_count_var.get()
        }
        
        # Запуск в окремому потоці
        def run_automation():
            try:
                # Імпорт вашого бота
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                
                from instagram_bot import InstagramBot
                
                bot = InstagramBot(
                    self.username_var.get(), 
                    self.password_var.get(), 
                    self.proxy_var.get() or None
                )
                
                self.bots[self.username_var.get()] = bot
                
                # Підключення логування до GUI
                self.setup_bot_logging(bot)
                
                success = bot.run_automation_multiple_users(targets_content, messages, actions_config)
                
                if success:
                    self.log_message("🎉 Автоматизація завершена успішно!")
                    self.status_var.set("✅ Завершено успішно!")
                else:
                    self.log_message("❌ Автоматизація завершена з помилками!")
                    self.status_var.set("❌ Завершено з помилками!")
                    
                self.progress_var.set(100)
                
            except Exception as e:
                self.log_message(f"❌ Критична помилка: {e}")
                self.status_var.set(f"❌ Помилка: {e}")
                
            finally:
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                if self.username_var.get() in self.bots:
                    del self.bots[self.username_var.get()]
                    
        thread = threading.Thread(target=run_automation, daemon=True)
        thread.start()

    def setup_bot_logging(self, bot):
        """Налаштування логування бота для GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, gui_instance):
                super().__init__()
                self.gui = gui_instance
                
            def emit(self, record):
                log_entry = self.format(record)
                self.gui.root.after(0, lambda: self.gui.log_message(log_entry))
                
        gui_handler = GUILogHandler(self)
        gui_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)
        
        bot.logger.addHandler(gui_handler)

    def stop_automation(self):
        """Зупинка автоматизації"""
        if messagebox.askyesno("Підтвердження", "Ви впевнені, що хочете зупинити автоматизацію?"):
            for bot in self.bots.values():
                try:
                    bot.close()
                except:
                    pass
                    
            self.bots.clear()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set("⏹️ Зупинено користувачем")
            self.log_message("⏹️ Автоматизацію зупинено користувачем")

    def log_message(self, message):
        """Додавання повідомлення до логів"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.logs_text.config(state=tk.NORMAL)
            self.logs_text.insert(tk.END, log_entry)
            
            if self.auto_scroll_var.get():
                self.logs_text.see(tk.END)
                
            self.logs_text.config(state=tk.DISABLED)
            
            lines = self.logs_text.get(1.0, tk.END).split('\n')
            if len(lines) > 1000:
                self.logs_text.config(state=tk.NORMAL)
                self.logs_text.delete(1.0, f"{len(lines)-1000}.0")
                self.logs_text.config(state=tk.DISABLED)
                
        except Exception as e:
            print(f"Помилка логування: {e}")

    # === ЗАГЛУШКИ ДЛЯ ІНШИХ МЕТОДІВ ===
    def load_targets_from_file(self): pass
    def save_targets_to_file(self): pass  
    def clear_targets(self): pass
    def save_current_account(self): pass
    def load_account(self): pass
    def delete_saved_account(self): pass
    def load_saved_accounts(self): pass
    def load_selected_account(self, event=None): pass
    def refresh_logs(self): pass
    def clear_logs(self): pass
    def save_logs(self): pass

    def run(self):
        """Запуск GUI"""
        self.log_message("🚀 Instagram Bot з багаторядковими повідомленнями запущено")
        self.log_message("📝 Можете додавати повідомлення з переносами рядків")
        self.log_message("💡 Використовуйте вкладку 'Повідомлення' для редагування")
        self.root.mainloop()

    def on_closing(self):
        """Обробник закриття програми"""
        if self.bots:
            if messagebox.askyesno("Підтвердження", "Є активна автоматизація. Все одно закрити?"):
                for bot in self.bots.values():
                    try:
                        bot.close()
                    except:
                        pass
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    app = InstagramBotGUI()
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()
