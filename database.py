import sqlite3
import hashlib
import os
from datetime import datetime, date
import pandas as pd

class Database:
    def __init__(self, db_name='clinic.db'):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """Create new database connection"""
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """Initialize database and tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                national_id TEXT UNIQUE,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                date_of_birth DATE,
                gender TEXT,
                address TEXT,
                emergency_contact TEXT,
                blood_type TEXT,
                allergies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                doctor_name TEXT,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                status TEXT DEFAULT 'Scheduled',
                type TEXT DEFAULT 'Regular',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')

        # Medical records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_records
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                visit_date DATE NOT NULL,
                diagnosis TEXT,
                prescription TEXT,
                symptoms TEXT,
                tests TEXT,
                notes TEXT,
                doctor_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')

        # Bills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                appointment_id INTEGER,
                amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'Unpaid',
                services TEXT,
                payment_method TEXT,
                bill_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')

        # Add default user if not exists
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            default_password = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, email)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', default_password, 'System Administrator', 'admin', 'admin@clinic.com'))

        conn.commit()
        conn.close()

    def execute_query(self, query, params=()):
        """Execute database query"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return result, columns
            else:
                conn.commit()
                return cursor.rowcount, None
        except Exception as e:
            print(f"Database error: {e}")
            return None, str(e)
        finally:
            conn.close()

    def get_dataframe(self, query, params=()):
        """Get data as DataFrame"""
        try:
            data, columns = self.execute_query(query, params)
            if data and columns:
                return pd.DataFrame(data, columns=columns)
            return pd.DataFrame()
        except Exception as e:
            print(f"Error in get_dataframe: {e}")
            return pd.DataFrame()

# Global database instance
db = Database()