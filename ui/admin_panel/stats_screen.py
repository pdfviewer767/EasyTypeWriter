# stats_screen.py
# شاشة الإحصائيات في لوحة التحكم
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QComboBox, QGroupBox, QHeaderView, QFrame, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import os, json, glob, datetime
from utils.tr import tr
from utils.translation_manager import TranslationManager
from utils.resource import resource_path, user_data_directory


def normalize_user_records(loaded):
    if isinstance(loaded, dict):
        records = loaded.get("users", loaded)
        if isinstance(records, dict):
            return [
                {**user, "username": username}
                for username, user in records.items()
                if username and isinstance(user, dict)
            ]
    elif isinstance(loaded, list):
        return [
            user if isinstance(user, dict) else {"username": user}
            for user in loaded
            if isinstance(user, dict) and user.get("username")
            or isinstance(user, str) and user
        ]
    return []


class StatsScreen(QWidget):
    def __init__(self, translation_manager=None):
        super().__init__()
        self.setMinimumSize(600, 400)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)

        # تهيئة الترجمة واللغة
        if translation_manager is not None:
            self.translator = translation_manager
        else:
            from utils.tr import set_translation_manager
            from PyQt5.QtWidgets import QApplication
            from core.settings_manager import SettingsManager
            app = QApplication.instance()
            settings_manager = SettingsManager()
            self.translator = TranslationManager(app, settings_manager)
            set_translation_manager(self.translator)
        self.lang = self.translator.get_language() if hasattr(self.translator, "get_language") else "ar"
        self.is_rtl = self.lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)

        # تعديل مسار ملف التنسيق (QSS) لاستخدام resource_path
        try:
            qss_path = resource_path('styles/app.qss')
        except Exception:
            qss_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'styles', 'app.qss')

        if os.path.exists(qss_path):
            try:
                with open(qss_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                    self.setStyleSheet(qss_content)
            except Exception as e:
                print(f"[QSS ERROR] Could not parse stylesheet: {e}")
        else:
            self.setStyleSheet("")
        # مسار مجلد البيانات بعد التحزيم باستخدام resource_path
        try:
            data_dir = user_data_directory('data')
        except Exception:
            # fallback لمسار عادي في التطوير
            data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

        users_file = os.path.join(data_dir, "users.json")
        progress_files = glob.glob(os.path.join(data_dir, 'user_progress_*.json'))

        # --- تحميل بيانات المستخدمين ---
        users = []
        try:
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    users = normalize_user_records(loaded)
        except Exception as e:
            print(f"Error loading users: {e}")
            users = []
        users = [u for u in users if 'username' in u and u['username'] and isinstance(u['username'], str)]

        # --- تجميع بيانات الأداء ---
        from collections import Counter
        self.user_stats = []
        self.all_sessions = []
        self.error_counter = Counter()
        total_sessions = 0
        total_duration = 0
        total_wpm = 0
        total_accuracy = 0
        self.user_progress_data = {}

        for user in users:
            username = user['username']
            progress_path = os.path.join(data_dir, f'user_progress_{username}.json')
            sessions = 0
            user_sessions = []
            user_total_wpm = 0
            user_total_accuracy = 0
            user_total_duration = 0

            if os.path.exists(progress_path):
                try:
                    with open(progress_path, 'r', encoding='utf-8') as pf:
                        pdata = json.load(pf)
                    for lang in ['ar', 'en']:
                        lang_sessions = pdata.get(f'sessions_{lang}', [])
                        sessions += len(lang_sessions)
                        for session in lang_sessions:
                            date_str = session.get('date', '')
                            try:
                                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                                date_display = date_obj.strftime('%d %b')
                            except:
                                date_display = date_str
                            errors = session.get('errors', {})
                            for char, count in errors.items():
                                self.error_counter[char] += count
                            session_data = {
                                'username': username,
                                'date': date_str,
                                'date_display': date_display,
                                'lesson': session.get('lesson', ''),
                                'duration': session.get('duration_seconds', 0),
                                'wpm': session.get('wpm', 0),
                                'accuracy': session.get('accuracy', 0),
                                'errors': session.get('errors', {}),
                                'error_count': session.get('error_count', 0)
                            }
                            self.all_sessions.append(session_data)
                            user_sessions.append(session_data)
                            total_sessions += 1
                            total_duration += session_data['duration']
                            total_wpm += session_data['wpm']
                            total_accuracy += session_data['accuracy']
                            user_total_wpm += session_data['wpm']
                            user_total_accuracy += session_data['accuracy']
                            user_total_duration += session_data['duration']
                except Exception as e:
                    print(f"Error loading progress for {username}: {e}")

            user_avg_wpm = user_total_wpm / sessions if sessions else 0
            user_avg_accuracy = user_total_accuracy / sessions if sessions else 0
            user_hours = user_total_duration // 3600
            user_minutes = (user_total_duration % 3600) // 60
            user_duration_str = f"{int(user_hours)} س {int(user_minutes)} د" if user_hours else f"{int(user_minutes)} د"

            self.user_progress_data[username] = {
                'sessions': sessions,
                'avg_wpm': user_avg_wpm,
                'avg_accuracy': user_avg_accuracy,
                'total_duration': user_duration_str,
                'sessions_data': user_sessions
            }

            self.user_stats.append({
                'username': username,
                'sessions': sessions,
                'is_admin': user.get('is_admin', False),
                'user_sessions': user_sessions
            })

        avg_wpm = total_wpm / total_sessions if total_sessions else 0
        avg_accuracy = total_accuracy / total_sessions if total_sessions else 0
        total_hours = total_duration // 3600
        total_minutes = (total_duration % 3600) // 60
        total_duration_str = f"{int(total_hours)} س {int(total_minutes)} د" if total_hours else f"{int(total_minutes)} د"
        top_errors = self.error_counter.most_common(3)
        errors_str = "، ".join([f"{char}" for char, _ in top_errors]) if top_errors else "لا توجد أخطاء"

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_container = QFrame()
        title_container.setGraphicsEffect(self.create_shadow_effect())
        title_layout = QHBoxLayout(title_container)
        title_label = QLabel("📊 لوحة الإحصائيات")
        title_label.setFont(QFont("Arial", 22, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setMinimumHeight(60)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_container)

        user_summary_box = QFrame()
        user_summary_box.setGraphicsEffect(self.create_shadow_effect())
        user_summary_box.setMinimumHeight(180)
        user_summary_box.setMaximumWidth(700)
        user_summary_layout = QVBoxLayout(user_summary_box)
        user_summary_layout.setSpacing(18)
        title_row = QHBoxLayout()
        icon_label = QLabel("👤")
        icon_label.setFont(QFont("Arial", 24))
        title = QLabel("اختر اسم المستخدم")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title_row.addWidget(icon_label)
        title_row.addWidget(title)
        title_row.addStretch()
        user_summary_layout.addLayout(title_row)

        users_list = QComboBox()
        users_list.addItem("اختر مستخدمًا ...")
        if users:
            users_list.addItems([user['username'] for user in users])
        users_list.setMinimumHeight(64)
        user_summary_layout.addWidget(users_list)

        self.user_summary_label = QLabel("اختر مستخدمًا لعرض ملخص تقدمه.")
        self.user_summary_label.setWordWrap(True)
        self.user_summary_label.setAlignment(Qt.AlignCenter)
        user_summary_layout.addWidget(self.user_summary_label)

        def show_user_summary(idx):
            if idx <= 0:
                self.user_summary_label.setText("اختر مستخدمًا لعرض ملخص تقدمه.")
                return
            username = users_list.currentText()
            progress = self.user_progress_data.get(username, {})
            sessions = progress.get('sessions_data', [])
            lessons = [p for p in sessions if 'lesson' in p and p['lesson']]
            if not lessons:
                msg = f"<div style='text-align:center; font-size:16px;'>لا توجد بيانات للمستخدم <b>{username}</b></div>"
                self.user_summary_label.setText(msg)
                return
            avg_accuracy = sum(p.get('accuracy', 0) for p in lessons) / len(lessons) if lessons else 0
            avg_time = sum(p.get('duration', 0) for p in lessons) / len(lessons) if lessons else 0
            last_entry = lessons[-1] if lessons else None
            msg = f"""
            <div style='font-size:16px; line-height:1.7;'>
                <b style='font-size:18px; color:#3498db;'>إحصاءات المستخدم: {username}</b><br>
                عدد الدروس المنجزة: <span style='color:#2ecc71;'>{len(lessons)}</span><br>
                متوسط الدقة: <span style='color:#e74c3c;'>{avg_accuracy:.1f}%</span><br>
                متوسط الوقت: <span style='color:#f39c12;'>{avg_time:.1f} ثانية</span><br>
                {f"آخر درس: {last_entry.get('lesson', '-')}، الدقة: {last_entry.get('accuracy', 0):.1f}%, الوقت: {last_entry.get('duration', 0):.1f} ثانية<br>آخر تحديث: {last_entry.get('date_display', '-')}" if last_entry else ''}
            </div>
            """
            self.user_summary_label.setText(msg)

        users_list.currentIndexChanged.connect(show_user_summary)
        main_layout.addWidget(user_summary_box)

        main_layout.addWidget(self.create_section_title("الأداء العام"))
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        card_colors = ["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
        card_icons = ["📋", "⚡", "🎯", "⏱️", "❌"]

        def create_card(title, value, icon, color):
            card_frame = QFrame()
            card_frame.setGraphicsEffect(self.create_shadow_effect())
            card_layout = QVBoxLayout(card_frame)
            card_layout.setSpacing(8)

            top_layout = QHBoxLayout()
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Arial", 20))
            top_layout.addWidget(icon_label)

            title_label = QLabel(title)
            title_label.setFont(QFont("Arial", 12))
            top_layout.addWidget(title_label)
            top_layout.setStretch(1, 1)

            card_layout.addLayout(top_layout)

            value_label = QLabel(value)
            value_label.setFont(QFont("Arial", 18, QFont.Bold))
            value_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value_label)

            return card_frame

        cards_data = [
            ("عدد الجلسات", str(total_sessions)),
            ("متوسط السرعة", f"{avg_wpm:.1f} WPM"),
            ("متوسط الدقة", f"{avg_accuracy:.1f}%"),
            ("المدة الإجمالية", total_duration_str),
            ("الأخطاء الشائعة", errors_str)
        ]

        for i, (title, value) in enumerate(cards_data):
            cards_layout.addWidget(create_card(title, value, card_icons[i], card_colors[i]))

        main_layout.addLayout(cards_layout)

    def create_shadow_effect(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        return shadow

    def create_section_title(self, text):
        title = QLabel(text)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 5px 0;")
        return title

    def create_divider(self):
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #d0d0d0;")
        divider.setFixedHeight(1)
        return divider

    def get_user_progress(self, username):
        base_dir = None
        try:
            base_dir = user_data_directory('data')
        except Exception:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        progress_path = os.path.join(base_dir, f'user_progress_{username}.json')
        sessions = []
        if os.path.exists(progress_path):
            try:
                with open(progress_path, 'r', encoding='utf-8') as pf:
                    pdata = json.load(pf)
                for lang in ['ar', 'en']:
                    lang_sessions = pdata.get(f'sessions_{lang}', [])
                    sessions.extend(lang_sessions)
            except Exception as e:
                print(f"Error loading progress for {username}: {e}")
        return sessions
