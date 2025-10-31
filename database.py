# database.py
import sqlite3
import csv
from datetime import datetime


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot.db', check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                test_result TEXT,
                total_score INTEGER,
                registration_date TEXT
            )
        ''')
        self.conn.commit()

    def user_exists(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

    def add_user(self, user_id, username, test_result, total_score):
        cursor = self.conn.cursor()
        registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, test_result, total_score, registration_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, test_result, total_score, registration_date))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, username, test_result, total_score, registration_date
            FROM users ORDER BY registration_date DESC
        ''')
        return cursor.fetchall()

    def get_users_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]

    def export_to_excel(self):
        """Экспорт в CSV"""
        users = self.get_all_users()
        filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['User ID', 'Username', 'Результат теста', 'Баллы', 'Дата регистрации'])
            writer.writerows(users)

        return filename