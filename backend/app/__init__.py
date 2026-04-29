from flask import Flask
from flask_cors import CORS
import sqlite3
import os

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    CORS(app)
    
    # Initialize database
    init_db(app.config['DATABASE_PATH'])
    
    # Register routes
    from app.routes import api
    app.register_blueprint(api.bp)
    
    return app

def init_db(db_path):
    """Create database tables if they don't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            latency TEXT,
            packet_loss TEXT,
            dns TEXT,
            tcp TEXT,
            status TEXT,
            date TEXT,
            time TEXT
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_service_datetime
        ON checks(service, date DESC, time DESC)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_datetime
        ON checks(date DESC, time DESC)
    ''')

    conn.commit()
    conn.close()

