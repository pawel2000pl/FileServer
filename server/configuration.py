import os
import base64
import hashlib
import logging

logging.basicConfig(level=logging.WARNING)

# EVERY PATH MUST BE ENDED WITH os.sep

SERVER_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"
MAIN_PATH = SERVER_PATH + '../'
STATIC_PATH = SERVER_PATH + 'static/'
STORAGE_PATH = MAIN_PATH + 'storage/'
DATABASE_FILENAME = STORAGE_PATH + 'database.sqlite3'

BACKUP_PREFIX = 'backup'
ALLOW_LINKS = False
SHOW_BACKUPS_IN_FILES = False

DEFAULT_ADMIN_NAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin'
FAIL_LOGIN_DELAY_TIME = 10
BACKUPS_SYMLINKS_LIMIT = 65536

BUFFER_SIZE = 65536
TIMEOUT = 30
SESSION_CLEANUP_INTERVAL = 3600
SESSION_EXPIRES = 3600*24*7
SESSION_DIR = "/tmp/flask_sessions"

