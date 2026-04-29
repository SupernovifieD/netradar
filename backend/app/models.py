import sqlite3
from datetime import datetime
from config import Config

class CheckResult:
    @staticmethod
    def save(service, latency, packet_loss, dns, tcp, status):
        """Save a check result to database with split date/time"""
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO checks (service, latency, packet_loss, dns, tcp, status, date, time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (service, latency, packet_loss, dns, tcp, status, date, time))

        conn.commit()
        conn.close()

    @staticmethod
    def get_latest(limit=100):
        """Get latest check results"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM checks
            ORDER BY date DESC, time DESC
            LIMIT ?
        ''', (limit,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    @staticmethod
    def get_by_service(service, limit=2000):
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM checks
            WHERE service = ?
            ORDER BY date DESC, time DESC
            LIMIT ?
        ''', (service, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    @staticmethod
    def get_services_status():
        """Latest row per service"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT c1.*
            FROM checks c1
            INNER JOIN (
                SELECT service, MAX(date || ' ' || time) AS maxts
                FROM checks
                GROUP BY service
            ) c2 ON c1.service = c2.service
                 AND (c1.date || ' ' || c1.time) = c2.maxts
            ORDER BY c1.service
        ''')

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    @staticmethod
    def get_last_24h():
        """Get rows from last 24 hours"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # SQLite hack: reconstruct timestamp
        cursor.execute('''
            SELECT *
            FROM checks
            WHERE datetime(date || ' ' || time) >= datetime('now', '-24 hours')
            ORDER BY date DESC, time DESC
        ''')

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
