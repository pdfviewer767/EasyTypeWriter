# users_manager.py
# إدارة المستخدمين في لوحة التحكم
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QGroupBox, QCheckBox, QMessageBox, QFrame
from PyQt5.QtCore import Qt
import os, json
from utils.tr import tr
from utils.translation_manager import TranslationManager
import hashlib, binascii
import time
from utils.resource import user_data_path

def get_user_file_path():
    return user_data_path(os.path.join("data", "users.json"))

class UsersManager(QWidget):
    def __init__(self, translation_manager=None):
        super().__init__()
        self.translation_manager = translation_manager or self.create_translation_manager()
        self.lang = self.translation_manager.get_language()
        self.is_rtl = self.lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)
        
        self.init_ui()
        self.load_users()
        
    def create_translation_manager(self):
        from PyQt5.QtWidgets import QApplication
        from core.settings_manager import SettingsManager
        app = QApplication.instance()
        settings_manager = SettingsManager()
        return TranslationManager(app, settings_manager)

    def init_ui(self):
        self.setMinimumSize(600, 400)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        self.main_layout = QHBoxLayout(self)
        
        # Left section: Search and user table
        self.left_layout = QVBoxLayout()
        
        # Title
        self.title = QLabel(tr("users_list"))
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.left_layout.addWidget(self.title)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(tr("search_placeholder"))
        self.left_layout.addWidget(self.search_box)
        
        # User table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            tr("username"),
            tr("account_type"),
            tr("status"),
            tr("actions")
        ])
        self.left_layout.addWidget(self.table)
        
        # Add user button
        self.add_btn = QPushButton(tr("add_user_button"))
        self.add_btn.setStyleSheet("""
            QPushButton {
                font-size: 15px; 
                padding: 8px 18px; 
                border-radius: 7px; 
                background: #1976d2; 
                color: #fff;
            }
            QPushButton:hover {
                background: #1565c0;
            }
        """)
        self.left_layout.addWidget(self.add_btn)

        # Right section: User details and permissions
        right_layout = QVBoxLayout()
        
        # User details
        self.details_box = QGroupBox(tr("user_details"))
        self.details_box.setStyleSheet("""
            QGroupBox {
                font-size:17px;
                margin-bottom:8px;
                border: 1px solid #bdbdbd;
                border-radius: 5px;
                margin-top: 1.5ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 5px;
            }
        """)
        details_layout = QVBoxLayout()
        
        self.lbl_name = QLabel()
        self.lbl_name.setStyleSheet("font-size:18px;font-weight:bold;color:#263238;")
        
        self.lbl_email = QLabel()
        self.lbl_email.setStyleSheet("font-size:15px;color:#607d8b;")
        
        # Role selection
        hlayout1 = QHBoxLayout()
        self.role_label = QLabel(tr("account_type") + ":")
        self.role_combo = QComboBox()
        self.role_combo.addItems([tr("role_admin"), tr("role_teacher"), tr("role_student")])
        self.role_combo.setStyleSheet("font-size:15px; padding:5px; border-radius:5px; border:1px solid #bdbdbd;")
        hlayout1.addWidget(self.role_label)
        hlayout1.addWidget(self.role_combo)
        hlayout1.addStretch()
        
        # Status
        hlayout2 = QHBoxLayout()
        self.status_label = QLabel(tr("status") + ":")
        self.status_btn = QPushButton()
        self.status_btn.setStyleSheet("font-size:14px; padding:5px 14px; border-radius:6px;")
        hlayout2.addWidget(self.status_label)
        hlayout2.addWidget(self.status_btn)
        hlayout2.addStretch()
        
        # Action buttons
        action_buttons = QHBoxLayout()
        
        self.reset_pw_btn = QPushButton(tr("reset_password"))
        self.reset_pw_btn.setStyleSheet("""
            QPushButton {
                font-size:14px;
                background:#fbc02d;
                color:#fff;
                border-radius:6px;
                padding:5px 14px;
            }
            QPushButton:hover {
                background:#f9a825;
            }
        """)
        
        self.delete_btn = QPushButton(tr("delete_user_button"))
        self.delete_btn.setStyleSheet("""
            QPushButton {
                font-size:14px;
                background:#d32f2f;
                color:#fff;
                border-radius:6px;
                padding:5px 14px;
            }
            QPushButton:hover {
                background:#c62828;
            }
            QPushButton:disabled {
                background: #bdbdbd;
            }
        """)
        
        action_buttons.addWidget(self.reset_pw_btn)
        action_buttons.addWidget(self.delete_btn)
        
        details_layout.addWidget(self.lbl_name)
        details_layout.addWidget(self.lbl_email)
        details_layout.addLayout(hlayout1)
        details_layout.addLayout(hlayout2)
        details_layout.addLayout(action_buttons)
        self.details_box.setLayout(details_layout)
        right_layout.addWidget(self.details_box)
        
        # Permissions
        self.perms_box = QGroupBox(tr("custom_permissions"))
        self.perms_box.setStyleSheet("""
            QGroupBox {
                font-size:17px;
                margin-bottom:8px;
                border: 1px solid #bdbdbd;
                border-radius: 5px;
                margin-top: 1.5ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 5px;
            }
        """)
        perms_layout = QVBoxLayout()
        self.perm_checks = []
        self.perm_labels = [
            ("view_stats", tr("view_stats")),
            ("manage_lessons", tr("manage_lessons")),
            ("manage_users", tr("manage_users")),
            ("upload_files", tr("upload_files")),
            ("export_data", tr("export_data")),
        ]
        for key, label in self.perm_labels:
            cb = QCheckBox(label)
            cb.setStyleSheet("font-size:15px;")
            perms_layout.addWidget(cb)
            self.perm_checks.append((cb, key))
        self.perms_box.setLayout(perms_layout)
        right_layout.addWidget(self.perms_box)
        
        # Save button
        self.save_btn = QPushButton(tr("save_changes"))
        self.save_btn.setStyleSheet("""
            QPushButton {
                font-size:15px;
                background:#388e3c;
                color:#fff;
                border-radius:7px;
                padding:7px 18px;
            }
            QPushButton:hover {
                background:#2e7d32;
            }
        """)
        right_layout.addWidget(self.save_btn)
        right_layout.addStretch()

        # Assemble layouts
        self.main_layout.addLayout(self.left_layout, 2)
        
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("color:#cfd8dc;")
        self.main_layout.addWidget(line)
        
        self.main_layout.addLayout(right_layout, 3)
        
        # Initialize data
        self.users_file = get_user_file_path()
        self.users = []
        self.selected_idx = None
        
        # Connect signals
        self.connect_signals()
        
        # Disable controls initially
        self.disable_controls(True)
    
    def connect_signals(self):
        self.add_btn.clicked.connect(self.add_user)
        self.search_box.textChanged.connect(self.refresh_table)
        self.table.cellClicked.connect(self.handle_table_click)
        self.role_combo.currentIndexChanged.connect(self.on_role_change)
        self.status_btn.clicked.connect(self.toggle_user_status)
        self.reset_pw_btn.clicked.connect(self.reset_password)
        self.save_btn.clicked.connect(self.save_user_data)
        self.delete_btn.clicked.connect(self.delete_selected_user)
    
    def load_users(self):
        # Create default user file if not exists
        if not os.path.exists(self.users_file):
            self.create_default_user_file()
            
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = f.read()
                if not data.strip():
                    raise Exception("Empty user file")
                loaded = json.loads(data)
                if isinstance(loaded, dict):
                    users = loaded.get("users", {})
                    self.users = list(users.values()) if isinstance(users, dict) else users
                else:
                    self.users = loaded if isinstance(loaded, list) else []
                self.users = [user for user in self.users if isinstance(user, dict)]
        except Exception as e:
            print(f"Error loading users: {e}")
            self.create_default_user_file()
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    users = loaded.get("users", {}) if isinstance(loaded, dict) else loaded
                    self.users = list(users.values()) if isinstance(users, dict) else users
                    self.users = [user for user in self.users if isinstance(user, dict)]
            except:
                self.users = []
                
        self.refresh_table()
        
    def create_default_user_file(self):
        default_users = {"users": {}}
        
        data_dir = os.path.dirname(self.users_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, ensure_ascii=False, indent=2)
    
    def hash_password(self, password):
        salt = binascii.hexlify(os.urandom(16)).decode('ascii')
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                 binascii.unhexlify(salt), 100000, dklen=32)
        hashed_password = binascii.hexlify(key).decode('ascii')
        return hashed_password, salt
    
    def refresh_table(self):
        self.table.setRowCount(0)
        query = self.search_box.text().strip().lower()
        
        for idx, user in enumerate(self.users):
            if not isinstance(user, dict):
                continue
            username = user.get('username', '').lower()
            if query and query not in username:
                continue
                
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Username
            self.table.setItem(row, 0, QTableWidgetItem(user.get('username', '')))
            
            # Account type
            role = user.get('role', tr("role_admin") if user.get('is_admin') else tr("role_student"))
            self.table.setItem(row, 1, QTableWidgetItem(role))
            
            # Status
            status = tr("active") if user.get('active', True) else tr("inactive")
            status_item = QTableWidgetItem(status)
            self.table.setItem(row, 2, status_item)
            
            # Highlight inactive users
            if not user.get('active', True):
                for col in range(3):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(Qt.yellow)
            
            # Delete button
            delete_btn = QPushButton(tr("delete"))
            delete_btn.setStyleSheet("""
                QPushButton {
                    font-size:13px;
                    background:#d32f2f;
                    color:#fff;
                    border-radius:5px;
                    padding:3px 10px;
                }
                QPushButton:hover {
                    background:#c62828;
                }
            """)
            delete_btn.clicked.connect(lambda _, i=idx: self.delete_user(i))
            
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(delete_btn)
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 3, cell_widget)
            
        self.table.resizeColumnsToContents()
        
    def handle_table_click(self, row, column):
        if row < len(self.users):
            self.select_user(row)
    
    def select_user(self, idx):
        self.selected_idx = idx
        user = self.users[idx]
        
        self.lbl_name.setText(user.get('username', ''))
        self.lbl_email.setText(user.get('email', ''))
        
        # Account type
        role = user.get('role', tr("role_admin") if user.get('is_admin') else tr("role_student"))
        self.role_combo.setCurrentText(role)
        
        # Status
        active = user.get('active', True)
        self.status_btn.setText(tr("disable") if active else tr("enable"))
        self.status_btn.setStyleSheet(f"""
            background: {'#b71c1c' if active else '#388e3c'};
            color: #fff;
        """)
        
        # Permissions
        perms = user.get('permissions', self.get_default_permissions(role))
        for cb, key in self.perm_checks:
            cb.setChecked(perms.get(key, False))
        
        # Enable controls
        self.disable_controls(False)
        
        # Prevent deleting the only admin
        if user.get('username') == 'admin' and self.is_only_admin():
            self.delete_btn.setEnabled(False)
            self.delete_btn.setToolTip(tr("cannot_delete_only_admin"))
        else:
            self.delete_btn.setEnabled(True)
            self.delete_btn.setToolTip("")
    
    def disable_controls(self, disabled):
        self.status_btn.setDisabled(disabled)
        self.role_combo.setDisabled(disabled)
        self.delete_btn.setDisabled(disabled)
        self.perms_box.setDisabled(disabled)
        self.save_btn.setDisabled(disabled)
        self.reset_pw_btn.setDisabled(disabled)
        
        if disabled:
            self.details_box.setStyleSheet("color: #9e9e9e; border: 1px solid #e0e0e0;")
            self.perms_box.setStyleSheet("color: #9e9e9e; border: 1px solid #e0e0e0;")
        else:
            self.details_box.setStyleSheet("border: 1px solid #bdbdbd;")
            self.perms_box.setStyleSheet("border: 1px solid #bdbdbd;")
    
    def get_default_permissions(self, role):
        permissions = {}
        for _, key in self.perm_checks:
            if role == tr("role_admin"):
                permissions[key] = True
            elif role == tr("role_teacher"):
                permissions[key] = key in ['view_stats', 'manage_lessons', 'upload_files']
            else:
                permissions[key] = key == 'view_stats'
        return permissions
    
    def is_only_admin(self):
        return sum(1 for u in self.users 
                  if u.get('role') == tr("role_admin") and u.get('active', True)) == 1
    
    def on_role_change(self):
        if self.selected_idx is None:
            return
            
        user = self.users[self.selected_idx]
        new_role = self.role_combo.currentText()
        user['role'] = new_role
        
        # Update permissions if not customized
        if 'permissions' not in user:
            user['permissions'] = self.get_default_permissions(new_role)
            
        self.save_users()
        self.refresh_table()
        self.select_user(self.selected_idx)
    
    def toggle_user_status(self):
        if self.selected_idx is None:
            return
            
        user = self.users[self.selected_idx]
        
        # Prevent disabling the only admin
        if user.get('role') == tr("role_admin") and self.is_only_admin() and user.get('active', True):
            QMessageBox.warning(self, tr("error"), tr("cannot_disable_only_admin"))
            return
            
        user['active'] = not user.get('active', True)
        self.save_users()
        self.refresh_table()
        self.select_user(self.selected_idx)
    
    def reset_password(self):
        if self.selected_idx is None:
            return
            
        user = self.users[self.selected_idx]
        from PyQt5.QtWidgets import QInputDialog
        
        new_pw, ok = QInputDialog.getText(  
            self, 
            tr("reset_password_title"), 
            tr("enter_new_password").format(user.get('username','')),
            QLineEdit.Password
        )
        
        if ok and new_pw:
            hashed_password, salt = self.hash_password(new_pw)
            user['password'] = hashed_password
            user['salt'] = salt
            self.save_users()
            QMessageBox.information(self, tr("success"), tr("password_reset_success"))
    
    def save_user_data(self):
        if self.selected_idx is None:
            return
            
        user = self.users[self.selected_idx]
        perms = {key: cb.isChecked() for cb, key in self.perm_checks}
        user['permissions'] = perms
        self.save_users()
        QMessageBox.information(self, tr("success"), tr("changes_saved"))
    
    def add_user(self):
        from PyQt5.QtWidgets import QInputDialog
        
        username, ok = QInputDialog.getText(self, tr("add_user_title"), tr("enter_username"))
        if not ok or not username:
            return
            
        # Check for duplicate username
        if any(u['username'].lower() == username.lower() for u in self.users):
            QMessageBox.warning(self, tr("error"), tr("username_exists"))
            return
            
        email, ok = QInputDialog.getText(self, tr("add_user_title"), tr("enter_email"))
        if not ok:
            return
            
        pw, ok = QInputDialog.getText(
            self, 
            tr("add_user_title"), 
            tr("enter_password"),
            QLineEdit.Password
        )
        if not ok or not pw:
            return
            
        roles = [tr("role_admin"), tr("role_teacher"), tr("role_student")]
        role, ok = QInputDialog.getItem(
            self, 
            tr("add_user_title"), 
            tr("select_role"), 
            roles, 
            2, 
            False
        )
        if not ok:
            return
            
        # Hash password
        hashed_password, salt = self.hash_password(pw)
        
        # Create new user
        new_user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'salt': salt,
            'role': role,
            'active': True,
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': None,
            'failed_attempts': 0,
            'locked': False,
            'is_admin': role == tr("role_admin"),
            'permissions': self.get_default_permissions(role)
        }
        
        self.users.append(new_user)
        self.save_users()
        self.refresh_table()
        
        # Select the new user
        for i, u in enumerate(self.users):
            if u['username'] == username:
                self.select_user(i)
                break
    
    def delete_user(self, idx):
        user = self.users[idx]
        
        # Prevent deleting the only admin
        if user.get('role') == tr("role_admin") and self.is_only_admin():
            QMessageBox.warning(self, tr("error"), tr("cannot_delete_only_admin"))
            return
            
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            tr("confirm_delete_title"),
            tr("confirm_delete_user").format(user.get("username", "")),
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.users[idx]
            self.save_users()
            self.refresh_table()
            
            if self.users:
                self.select_user(0)
            else:
                self.disable_controls(True)
                self.lbl_name.setText("")
                self.lbl_email.setText("")
    
    def delete_selected_user(self):
        if self.selected_idx is not None:
            self.delete_user(self.selected_idx)
    
    def save_users(self):
        data_dir = os.path.dirname(self.users_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(
                {"users": {user["username"]: user for user in self.users}},
                f,
                ensure_ascii=False,
                indent=2,
            )
