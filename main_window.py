from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QTabWidget, QLabel, QGroupBox, QMessageBox,
                             QComboBox, QHeaderView, QLineEdit, QFormLayout,
                             QDialog, QDialogButtonBox, QMenu, QAction)
from PyQt5.QtCore import Qt
from src.database import Database
from src.auth import AuthManager
from src.statistics import StatisticsCalculator
from src.qr_generator import QRGenerator
from ui.styles import MAIN_WINDOW_STYLE
from ui.request_window import RequestWindow


class SearchDialog(QDialog):
    """Диалог поиска заявок"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Поиск заявки")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.search_by_combo = QComboBox()
        self.search_by_combo.addItems(["ID заявки", "Тип техники", "Модель", "ФИО клиента"])
        form_layout.addRow("Искать по:", self.search_by_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите значение для поиска...")
        form_layout.addRow("Значение:", self.search_input)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_search_params(self):
        return self.search_by_combo.currentText(), self.search_input.text().strip()


class MainWindow(QMainWindow):

    def __init__(self, db: Database, auth_manager: AuthManager):
        super().__init__()
        self.db = db
        self.auth_manager = auth_manager
        self.user_role = auth_manager.get_current_user_role()
        self.user_id = auth_manager.get_current_user_id()
        self.stats_calculator = StatisticsCalculator(db)
        self.all_requests = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setWindowTitle("Сервисный центр - Учет заявок на ремонт")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        top_panel = QHBoxLayout()
        user_info = QLabel(f"Пользователь: {self.auth_manager.current_user['fio']} "
                           f"({self.user_role})")
        user_info.setStyleSheet("font-weight: bold; padding: 10px;")
        top_panel.addWidget(user_info)

        logout_button = QPushButton("Выйти")
        logout_button.clicked.connect(self.logout)
        top_panel.addWidget(logout_button)
        top_panel.addStretch()

        main_layout.addLayout(top_panel)

        self.tabs = QTabWidget()

        self.requests_tab = self.create_requests_tab()
        self.tabs.addTab(self.requests_tab, "Заявки")

        if self.user_role in ['Администратор', 'Менеджер', 'Оператор']:
            self.stats_tab = self.create_stats_tab()
            self.tabs.addTab(self.stats_tab, "Статистика")

        if self.user_role in ['Администратор', 'Менеджер', 'Оператор', 'Заказчик']:
            self.qr_tab = self.create_qr_tab()
            self.tabs.addTab(self.qr_tab, "Оценка качества")

        main_layout.addWidget(self.tabs)

        bottom_panel = QHBoxLayout()

        if self.user_role in ['Администратор', 'Оператор', 'Менеджер', 'Заказчик']:
            add_button = QPushButton("Новая заявка")
            add_button.clicked.connect(self.add_request)
            bottom_panel.addWidget(add_button)

        search_button = QPushButton("Поиск")
        search_button.clicked.connect(self.search_request)
        bottom_panel.addWidget(search_button)

        clear_search_button = QPushButton("Сбросить поиск")
        clear_search_button.clicked.connect(self.clear_search)
        bottom_panel.addWidget(clear_search_button)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_data)
        bottom_panel.addWidget(refresh_button)

        if self.user_role in ['Администратор', 'Менеджер']:
            delete_button = QPushButton("Удалить заявку")
            delete_button.clicked.connect(self.delete_request)
            bottom_panel.addWidget(delete_button)

        if self.user_role in ['Администратор', 'Менеджер']:
            manage_users_button = QPushButton("Управление пользователями")
            manage_users_button.clicked.connect(self.open_user_management)
            bottom_panel.addWidget(manage_users_button)

        bottom_panel.addStretch()
        main_layout.addLayout(bottom_panel)

    def create_requests_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр по статусу:"))

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все", "Новая заявка", "В процессе ремонта",
                                     "Готова к выдаче", "Ожидание запчастей"])
        self.status_filter.currentTextChanged.connect(self.filter_requests)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.requests_table = QTableWidget()
        self.requests_table.setAlternatingRowColors(True)
        self.requests_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.requests_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.requests_table.doubleClicked.connect(self.edit_request)

        if self.user_role in ['Администратор', 'Менеджер']:
            self.requests_table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.requests_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.requests_table)

        widget.setLayout(layout)
        return widget

    def create_stats_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        stats_group = QGroupBox("Статистика сервисного центра")
        stats_layout = QVBoxLayout()

        self.completed_label = QLabel()
        self.completed_label.setStyleSheet("font-size: 14px; padding: 5px;")
        stats_layout.addWidget(self.completed_label)

        self.avg_time_label = QLabel()
        self.avg_time_label.setStyleSheet("font-size: 14px; padding: 5px;")
        stats_layout.addWidget(self.avg_time_label)

        self.total_users_label = QLabel()
        self.total_users_label.setStyleSheet("font-size: 14px; padding: 5px;")
        stats_layout.addWidget(self.total_users_label)

        self.new_requests_label = QLabel()
        self.new_requests_label.setStyleSheet("font-size: 14px; padding: 5px;")
        stats_layout.addWidget(self.new_requests_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        problem_group = QGroupBox("Статистика по типам техники")
        problem_layout = QVBoxLayout()

        self.problem_stats_table = QTableWidget()
        self.problem_stats_table.setColumnCount(3)
        self.problem_stats_table.setHorizontalHeaderLabels(["Тип техники", "Всего заявок", "Выполнено"])
        self.problem_stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        problem_layout.addWidget(self.problem_stats_table)

        problem_group.setLayout(problem_layout)
        layout.addWidget(problem_group)

        refresh_stats_button = QPushButton("Обновить статистику")
        refresh_stats_button.clicked.connect(self.update_statistics)
        layout.addWidget(refresh_stats_button)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_qr_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel("Отсканируйте QR-код для оценки качества обслуживания")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 20px;")
        layout.addWidget(info_label)

        qr_label = QLabel()
        qr_label.setAlignment(Qt.AlignCenter)

        qr_pixmap = QRGenerator.generate_qr_code()
        scaled_pixmap = qr_pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        qr_label.setPixmap(scaled_pixmap)
        layout.addWidget(qr_label)

        link_label = QLabel("Ссылка для оценки:\n"
                            "https://docs.google.com/forms/d/e/1FAIpQLSdhZcExx6LSIXxk0ub55mSu-WIh23WYdGG9HY5EZhLDo7P8eA/viewform")
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setWordWrap(True)
        link_label.setStyleSheet("color: blue; padding: 20px;")
        layout.addWidget(link_label)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def show_context_menu(self, position):
        menu = QMenu()
        delete_action = QAction("Удалить заявку", self)
        delete_action.triggered.connect(self.delete_request)
        menu.addAction(delete_action)
        menu.exec_(self.requests_table.viewport().mapToGlobal(position))

    def load_data(self):
        status = self.status_filter.currentText()
        if status == "Все":
            status = None

        self.all_requests = self.db.get_requests_by_user_role(self.user_role, self.user_id, status)
        self.display_requests(self.all_requests)

        if hasattr(self, 'stats_tab'):
            self.update_statistics()

    def display_requests(self, requests):
        self.requests_table.clear()
        self.requests_table.setRowCount(len(requests))
        self.requests_table.setColumnCount(8)
        self.requests_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Тип техники", "Модель", "Проблема",
            "Статус", "Мастер", "Клиент"
        ])

        for i, req in enumerate(requests):
            self.requests_table.setItem(i, 0, QTableWidgetItem(str(req['requestid'])))
            self.requests_table.setItem(i, 1, QTableWidgetItem(str(req['startdate'])))
            self.requests_table.setItem(i, 2, QTableWidgetItem(req['hometechtype']))
            self.requests_table.setItem(i, 3, QTableWidgetItem(req['hometechmodel']))
            problem_text = req['problemdescryption'][:50] + "..." if len(req['problemdescryption']) > 50 else req[
                'problemdescryption']
            self.requests_table.setItem(i, 4, QTableWidgetItem(problem_text))
            self.requests_table.setItem(i, 5, QTableWidgetItem(req['requeststatus']))
            self.requests_table.setItem(i, 6, QTableWidgetItem(req['mastername']))
            self.requests_table.setItem(i, 7, QTableWidgetItem(req['clientname']))

        self.requests_table.resizeColumnsToContents()

    def search_request(self):
        dialog = SearchDialog(self)
        if dialog.exec_() == SearchDialog.Accepted:
            search_by, search_value = dialog.get_search_params()
            if not search_value:
                QMessageBox.warning(self, "Ошибка", "Введите значение для поиска!")
                return

            results = []
            for req in self.all_requests:
                if search_by == "ID заявки" and str(req['requestid']) == search_value:
                    results.append(req)
                elif search_by == "Тип техники" and search_value.lower() in req['hometechtype'].lower():
                    results.append(req)
                elif search_by == "Модель" and search_value.lower() in req['hometechmodel'].lower():
                    results.append(req)
                elif search_by == "ФИО клиента" and search_value.lower() in req['clientname'].lower():
                    results.append(req)

            if results:
                self.display_requests(results)
                QMessageBox.information(self, "Результат", f"Найдено {len(results)} заявок")
            else:
                QMessageBox.information(self, "Результат", "Заявки не найдены")
                self.display_requests([])

    def clear_search(self):
        self.display_requests(self.all_requests)

    def filter_requests(self):
        self.load_data()

    def update_statistics(self):
        stats = self.db.get_statistics()

        self.completed_label.setText(f"Выполненные заявки: {stats['completed_count']}")
        self.avg_time_label.setText(f"Среднее время выполнения: {stats['avg_completion_days']} дней")

        if hasattr(self, 'total_users_label'):
            self.total_users_label.setText(f"Всего пользователей: {stats.get('total_users', 0)}")
            self.new_requests_label.setText(f"Новых заявок: {stats.get('new_requests', 0)}")

        self.problem_stats_table.setRowCount(len(stats['problem_stats']))
        for i, stat in enumerate(stats['problem_stats']):
            self.problem_stats_table.setItem(i, 0, QTableWidgetItem(stat['type']))
            self.problem_stats_table.setItem(i, 1, QTableWidgetItem(str(stat['total'])))
            self.problem_stats_table.setItem(i, 2, QTableWidgetItem(str(stat['completed'])))

    def add_request(self):
        dialog = RequestWindow(self.db, None, self.auth_manager)
        if dialog.exec_() == RequestWindow.Accepted:
            self.load_data()
            QMessageBox.information(self, "Успех", "Заявка успешно создана")

    def edit_request(self, index):
        row = index.row()
        request_id = int(self.requests_table.item(row, 0).text())

        if self.user_role == 'Заказчик':
            QMessageBox.warning(self, "Доступ запрещен", "Заказчик не может редактировать заявки")
            return

        dialog = RequestWindow(self.db, request_id, self.auth_manager)
        if dialog.exec_() == RequestWindow.Accepted:
            self.load_data()
            QMessageBox.information(self, "Успех", "Заявка успешно обновлена")

    def delete_request(self):
        current_row = self.requests_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку для удаления")
            return

        request_id = int(self.requests_table.item(current_row, 0).text())

        reply = QMessageBox.question(self, "Подтверждение удаления",
                                     f"Вы уверены, что хотите удалить заявку N{request_id}?\nЭто действие необратимо.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_request(request_id)
            self.load_data()
            QMessageBox.information(self, "Успех", f"Заявка N{request_id} удалена")

    def open_user_management(self):
        """Открыть окно управления пользователями"""
        from ui.user_management_window import UserManagementWindow
        dialog = UserManagementWindow(self.db, self.user_role)
        dialog.exec_()
        self.update_statistics()

    def logout(self):
        reply = QMessageBox.question(self, "Подтверждение",
                                     "Вы уверены, что хотите выйти?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.auth_manager.logout()
            self.close()