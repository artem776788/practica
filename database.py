import psycopg2
from psycopg2 import OperationalError
from typing import Optional, List, Dict
from contextlib import contextmanager


class Database:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self, host: str = 'localhost', database: str = 'repair_service',
                 user: str = 'postgres', password: str = 'postgres123', port: int = 5432):
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'client_encoding': 'UTF8'
        }
        self.connection = None

    def connect(self) -> bool:
        """Установка соединения с БД"""
        try:
            conn_str = f"host={self.connection_params['host']} port={self.connection_params['port']} dbname={self.connection_params['database']} user={self.connection_params['user']} password={self.connection_params['password']} client_encoding=UTF8"
            self.connection = psycopg2.connect(conn_str)
            print("Подключение к БД успешно")
            return True
        except OperationalError as e:
            print(f"Ошибка подключения к БД: {e}")
            return False

    def disconnect(self):
        """Закрытие соединения с БД"""
        if self.connection:
            self.connection.close()
            print("Соединение с БД закрыто")

    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для работы с курсором"""
        if not self.connection or self.connection.closed:
            self.connect()
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[tuple]]:
        """Выполнение SQL запроса и возврат результатов"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return cursor.fetchall()
                return None
        except Exception as e:
            print(f"Ошибка выполнения запроса: {e}")
            return None

    def get_user_by_credentials(self, login: str, password: str) -> Optional[Dict]:
        """Аутентификация пользователя"""
        query = "SELECT userid, fio, login, type FROM users WHERE login = %s AND password = %s"
        result = self.execute_query(query, (login, password))
        if result:
            return {
                'userid': result[0][0],
                'fio': result[0][1],
                'login': result[0][2],
                'type': result[0][3]
            }
        return None

    def get_requests_by_user_role(self, user_role: str, user_id: int = None, status_filter: str = None) -> List[Dict]:
        """Получение заявок в зависимости от роли пользователя"""

        if user_role == 'Менеджер':
            query = """
                SELECT r.requestid, r.startdate, r.hometechtype, r.hometechmodel,
                       r.problemdescryption, r.requeststatus, r.completiondate,
                       r.repairparts, u.fio as master_name, c.fio as client_name
                FROM repair_requests r
                LEFT JOIN users u ON r.masterid = u.userid
                JOIN users c ON r.clientid = c.userid
            """
        elif user_role == 'Оператор':
            query = """
                SELECT r.requestid, r.startdate, r.hometechtype, r.hometechmodel,
                       r.problemdescryption, r.requeststatus, r.completiondate,
                       r.repairparts, u.fio as master_name, c.fio as client_name
                FROM repair_requests r
                LEFT JOIN users u ON r.masterid = u.userid
                JOIN users c ON r.clientid = c.userid
            """
        elif user_role == 'Мастер':
            query = f"""
                SELECT r.requestid, r.startdate, r.hometechtype, r.hometechmodel,
                       r.problemdescryption, r.requeststatus, r.completiondate,
                       r.repairparts, u.fio as master_name, c.fio as client_name
                FROM repair_requests r
                LEFT JOIN users u ON r.masterid = u.userid
                JOIN users c ON r.clientid = c.userid
                WHERE r.masterid = {user_id}
            """
        elif user_role == 'Заказчик':
            query = f"""
                SELECT r.requestid, r.startdate, r.hometechtype, r.hometechmodel,
                       r.problemdescryption, r.requeststatus, r.completiondate,
                       r.repairparts, u.fio as master_name, c.fio as client_name
                FROM repair_requests r
                LEFT JOIN users u ON r.masterid = u.userid
                JOIN users c ON r.clientid = c.userid
                WHERE r.clientid = {user_id}
            """
        else:
            return []

        if status_filter:
            query += f" WHERE r.requeststatus = '{status_filter}'"
        query += " ORDER BY r.startdate DESC"

        result = self.execute_query(query)
        if result:
            return [{
                'requestid': row[0],
                'startdate': row[1],
                'hometechtype': row[2],
                'hometechmodel': row[3],
                'problemdescryption': row[4],
                'requeststatus': row[5],
                'completiondate': row[6],
                'repairparts': row[7],
                'mastername': row[8] or 'Не назначен',
                'clientname': row[9]
            } for row in result]
        return []

    def get_all_requests(self, status_filter: str = None) -> List[Dict]:
        """Получение всех заявок (для менеджера и оператора)"""
        query = """
            SELECT r.requestid, r.startdate, r.hometechtype, r.hometechmodel,
                   r.problemdescryption, r.requeststatus, r.completiondate,
                   r.repairparts, u.fio as master_name, c.fio as client_name
            FROM repair_requests r
            LEFT JOIN users u ON r.masterid = u.userid
            JOIN users c ON r.clientid = c.userid
        """
        if status_filter:
            query += f" WHERE r.requeststatus = '{status_filter}'"
        query += " ORDER BY r.startdate DESC"

        result = self.execute_query(query)
        if result:
            return [{
                'requestid': row[0],
                'startdate': row[1],
                'hometechtype': row[2],
                'hometechmodel': row[3],
                'problemdescryption': row[4],
                'requeststatus': row[5],
                'completiondate': row[6],
                'repairparts': row[7],
                'mastername': row[8] or 'Не назначен',
                'clientname': row[9]
            } for row in result]
        return []

    def update_request_status(self, request_id: int, new_status: str,
                              completion_date: str = None, repair_parts: str = None) -> bool:
        """Обновление статуса заявки"""
        query = """
            UPDATE repair_requests 
            SET requeststatus = %s, completiondate = %s, repairparts = %s
            WHERE requestid = %s
        """
        self.execute_query(query, (new_status, completion_date, repair_parts, request_id))
        return True

    def assign_master(self, request_id: int, master_id: int) -> bool:
        """Назначение мастера на заявку"""
        query = "UPDATE repair_requests SET masterid = %s WHERE requestid = %s"
        self.execute_query(query, (master_id, request_id))
        return True

    def add_comment(self, message: str, master_id: int, request_id: int) -> bool:
        """Добавление комментария к заявке"""
        query = """
            INSERT INTO comments (message, masterid, requestid) 
            VALUES (%s, %s, %s)
        """
        self.execute_query(query, (message, master_id, request_id))
        return True

    def get_comments(self, request_id: int) -> List[Dict]:
        """Получение комментариев по заявке"""
        query = """
            SELECT c.commentid, c.message, c.masterid, u.fio as mastername
            FROM comments c
            JOIN users u ON c.masterid = u.userid
            WHERE c.requestid = %s
            ORDER BY c.commentid DESC
        """
        result = self.execute_query(query, (request_id,))
        if result:
            return [{
                'commentid': row[0],
                'message': row[1],
                'masterid': row[2],
                'mastername': row[3]
            } for row in result]
        return []

    def get_masters(self) -> List[Dict]:
        """Получение списка всех мастеров"""
        query = "SELECT userid, fio FROM users WHERE type = 'Мастер'"
        result = self.execute_query(query)
        if result:
            return [{'userid': row[0], 'fio': row[1]} for row in result]
        return []

    def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей (для менеджера)"""
        query = "SELECT userid, fio, type FROM users ORDER BY userid"
        result = self.execute_query(query)
        if result:
            return [{'userid': row[0], 'fio': row[1], 'type': row[2]} for row in result]
        return []

    def delete_request(self, request_id: int) -> bool:
        """Удаление заявки (только для менеджера)"""
        query = "DELETE FROM repair_requests WHERE requestid = %s"
        self.execute_query(query, (request_id,))
        return True

    def get_statistics(self) -> Dict:
        """Получение статистики"""
        stats = {}

        result = self.execute_query(
            "SELECT COUNT(*) FROM repair_requests WHERE requeststatus = 'Готова к выдаче'"
        )
        stats['completed_count'] = result[0][0] if result else 0

        result = self.execute_query(
            "SELECT AVG(completiondate - startdate) FROM repair_requests WHERE completiondate IS NOT NULL"
        )
        avg_days = result[0][0] if result and result[0][0] else 0
        if avg_days and hasattr(avg_days, 'days'):
            stats['avg_completion_days'] = round(avg_days.days, 2)
        else:
            stats['avg_completion_days'] = round(float(avg_days) if avg_days else 0, 2)

        result = self.execute_query("""
            SELECT hometechtype, COUNT(*) as total,
                   SUM(CASE WHEN requeststatus = 'Готова к выдаче' THEN 1 ELSE 0 END) as completed
            FROM repair_requests
            GROUP BY hometechtype
        """)
        stats['problem_stats'] = []
        if result:
            for row in result:
                stats['problem_stats'].append({
                    'type': row[0],
                    'total': row[1],
                    'completed': row[2] or 0
                })

        return stats

    def create_new_request(self, client_id: int, tech_type: str, tech_model: str,
                           problem: str, start_date: str) -> Optional[int]:
        """Создание новой заявки"""
        query = """
            INSERT INTO repair_requests 
            (startdate, hometechtype, hometechmodel, problemdescryption, 
             requeststatus, clientid)
            VALUES (%s, %s, %s, %s, 'Новая заявка', %s)
            RETURNING requestid
        """
        result = self.execute_query(query, (start_date, tech_type, tech_model, problem, client_id))
        if result:
            return result[0][0]
        return None

    def get_request_by_id(self, request_id: int) -> Optional[Dict]:
        """Получение заявки по ID"""
        query = """
            SELECT r.requestid, r.startdate, r.hometechtype, r.hometechmodel,
                   r.problemdescryption, r.requeststatus, r.completiondate,
                   r.repairparts, r.masterid, r.clientid,
                   u.fio as master_name, c.fio as client_name
            FROM repair_requests r
            LEFT JOIN users u ON r.masterid = u.userid
            JOIN users c ON r.clientid = c.userid
            WHERE r.requestid = %s
        """
        result = self.execute_query(query, (request_id,))
        if result:
            row = result[0]
            return {
                'requestid': row[0],
                'startdate': row[1],
                'hometechtype': row[2],
                'hometechmodel': row[3],
                'problemdescryption': row[4],
                'requeststatus': row[5],
                'completiondate': row[6],
                'repairparts': row[7],
                'masterid': row[8],
                'clientid': row[9],
                'mastername': row[10] or 'Не назначен',
                'clientname': row[11]
            }
        return None