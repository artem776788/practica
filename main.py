import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMessageBox
from src.database import Database
from src.auth import AuthManager
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    db = Database(
        host='localhost',
        database='repair_service',
        user='postgres',
        password='postgres123',
        port=5432
    )

    if not db.connect():
        QMessageBox.critical(None, "Ошибка",
                             "Не удалось подключиться к базе данных.\n\n"
                             "Проверьте параметры подключения:\n"
                             f"Хост: {db.connection_params['host']}\n"
                             f"БД: {db.connection_params['database']}\n"
                             f"Пользователь: {db.connection_params['user']}\n"
                             f"Порт: {db.connection_params['port']}\n\n"
                             "Убедитесь, что PostgreSQL запущен и пароль правильный.")
        sys.exit(1)

    auth_manager = AuthManager(db)
    login_window = LoginWindow(auth_manager)

    if login_window.exec_() == LoginWindow.Accepted:
        main_window = MainWindow(db, auth_manager)
        main_window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()