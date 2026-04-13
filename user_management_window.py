from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QComboBox, QFormLayout, QGroupBox,
                             QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt
from src.database import Database


class UserManagementWindow(QDialog):
    """Окно управления пользователями для администратора и менеджера"""

    def __init__(self, db: Database, current_user_role: str):
        super().__init__()
        self.db = db
        self.current_user_role = current_user_role
        self.init_ui()
        self.load_users()

    def init_ui(self):
        self.setWindowTitle("Управление пользователями")
        self.setGeometry(200, 200, 800, 550)

        layout = QVBoxLayout()

        title_label = QLabel("Управление пользователями системы")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        add_group = QGroupBox("Добавление нового пользователя")
        add_layout = QFormLayout()

        self.fio_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()

        if self.current_user_role == 'Администратор':
            self.role_combo.addItems(["Заказчик", "Мастер", "Оператор", "Менеджер"])
        else:
            self.role_combo.addItems(["Заказчик", "Мастер", "Оператор"])

        add_layout.addRow("ФИО:", self.fio_input)
        add_layout.addRow("Телефон:", self.phone_input)
        add_layout.addRow("Логин:", self.login_input)
        add_layout.addRow("Пароль:", self.password_input)
        add_layout.addRow("Роль:", self.role_combo)

        add_button = QPushButton("Добавить пользователя")
        add_button.clicked.connect(self.add_user)
        add_layout.addRow("", add_button)

        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        self.users_table = QTableWidget()
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.users_table)

        buttons_layout = QHBoxLayout()

        self.delete_button = QPushButton("Удалить выбранного пользователя")
        self.delete_button.clicked.connect(self.delete_user)
        buttons_layout.addWidget(self.delete_button)

        refresh_button = QPushButton("Обновить список")
        refresh_button.clicked.connect(self.load_users)
        buttons_layout.addWidget(refresh_button)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def load_users(self):
        """Загрузка списка пользователей"""
        users = self.db.get_all_users()

        self.users_table.clear()
        self.users_table.setRowCount(len(users))
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "ФИО", "Логин", "Роль"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for i, user in enumerate(users):
            self.users_table.setItem(i, 0, QTableWidgetItem(str(user['userid'])))
            self.users_table.setItem(i, 1, QTableWidgetItem(user['fio']))
            self.users_table.setItem(i, 2, QTableWidgetItem(user['login']))
            self.users_table.setItem(i, 3, QTableWidgetItem(user['type']))

            if user['type'] == 'Администратор':
                for col in range(4):
                    self.users_table.item(i, col).setBackground(Qt.green)

    def add_user(self):
        """Добавление нового пользователя"""
        fio = self.fio_input.text().strip()
        phone = self.phone_input.text().strip()
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()
        user_type = self.role_combo.currentText()

        if not all([fio, phone, login, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if len(phone) < 10:
            QMessageBox.warning(self, "Ошибка", "Введите корректный номер телефона!")
            return

        user_id = self.db.create_user(fio, phone, login, password, user_type)

        if user_id:
            QMessageBox.information(self, "Успех", f"Пользователь {fio} добавлен с ролью {user_type}")
            self.fio_input.clear()
            self.phone_input.clear()
            self.login_input.clear()
            self.password_input.clear()
            self.load_users()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось добавить пользователя. Логин уже существует!")

    def delete_user(self):
        """Удаление выбранного пользователя"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления")
            return

        user_id = int(self.users_table.item(current_row, 0).text())
        user_fio = self.users_table.item(current_row, 1).text()
        user_role = self.users_table.item(current_row, 3).text()

        if user_role == "Администратор":
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить администратора!")
            return

        reply = QMessageBox.question(self, "Подтверждение",
                                     f"Удалить пользователя {user_fio} с ролью {user_role}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_user(user_id)
            self.load_users()
            QMessageBox.information(self, "Успех", "Пользователь удален")