from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt
from ui.styles import LOGIN_STYLE
from src.database import Database


class RegisterWindow(QDialog):

    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.db = auth_manager.db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Регистрация - Сервисный центр")
        self.setFixedSize(400, 500)
        self.setStyleSheet(LOGIN_STYLE)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        title_label = QLabel("Регистрация нового пользователя")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 15px;")
        layout.addWidget(title_label)

        self.fio_input = QLineEdit()
        self.fio_input.setPlaceholderText("ФИО (например: Иванов Иван Иванович)")
        self.fio_input.setFixedHeight(40)
        layout.addWidget(self.fio_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Телефон (например: 89001234567)")
        self.phone_input.setFixedHeight(40)
        layout.addWidget(self.phone_input)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин (придумайте уникальный логин)")
        self.login_input.setFixedHeight(40)
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        layout.addWidget(self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Подтверждение пароля")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setFixedHeight(40)
        layout.addWidget(self.confirm_password_input)

        register_button = QPushButton("Зарегистрироваться")
        register_button.setFixedHeight(40)
        register_button.clicked.connect(self.handle_register)
        layout.addWidget(register_button)

        cancel_button = QPushButton("Назад")
        cancel_button.setFixedHeight(40)
        cancel_button.setStyleSheet("background-color: #f44336;")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        info_label = QLabel("После регистрации вы сможете:\n"
                            "- Создавать заявки на ремонт\n"
                            "- Отслеживать статус своих заявок\n"
                            "- Оценивать качество обслуживания")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 11px; margin-top: 20px; color: #cccccc;")
        layout.addWidget(info_label)

        self.setLayout(layout)

    def handle_register(self):
        fio = self.fio_input.text().strip()
        phone = self.phone_input.text().strip()
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not all([fio, phone, login, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return

        if len(phone) < 10:
            QMessageBox.warning(self, "Ошибка", "Введите корректный номер телефона!")
            return

        # Создаем пользователя с ролью "Заказчик"
        user_id = self.db.create_user(fio, phone, login, password, "Заказчик")

        if user_id:
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось зарегистрироваться. Логин уже существует!")