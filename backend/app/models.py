import sqlite3
from datetime import datetime
from config import Config

class CheckResult:
    @staticmethod
    def save(service, latency, packet_loss, dns, tcp, status):
        """Save a check result to database"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO checks (service, latency, packet_loss, dns, tcp, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (service, latency, packet_loss, dns, tcp, status))
        
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
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def get_by_service(service, limit=2000):
        """Get check results for a specific service"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM checks 
            WHERE service = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (service, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def get_services_status():
        """Get latest status for all services"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c1.* FROM checks c1
            INNER JOIN (
                SELECT service, MAX(timestamp) as max_time
                FROM checks
                GROUP BY service
            ) c2 ON c1.service = c2.service AND c1.timestamp = c2.max_time
            ORDER BY c1.service
        ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    @staticmethod
    def get_last_24h():
        """Get check results from the last 24 hours"""
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM checks
            WHERE timestamp >= datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        ''')

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

