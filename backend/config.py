import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'netradar.db')
    SERVICES_FILE = os.path.join(BASE_DIR, '..', 'services.json')
    CHECK_INTERVAL = 15  # seconds
    MAX_WORKERS = 20
