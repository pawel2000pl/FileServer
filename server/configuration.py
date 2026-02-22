import os
import base64
import hashlib
import logging

logging.basicConfig(level=logging.WARNING)

# EVERY PATH MUST BE ENDED WITH os.sep

SERVER_PATH = os.path.dirname(os.path.abspath(__file__)) + "/"
MAIN_PATH = SERVER_PATH + '../'
STATIC_PATH = SERVER_PATH + 'static/'
CP_CONFIG_PATH = SERVER_PATH + 'cp_config/'
DATABASE_FILENAME = MAIN_PATH + 'database.sqlite3'
STORAGE_PATH = MAIN_PATH + 'storage/'
BACKUP_PREFIX = 'backup'

DEFAULT_ADMIN_NAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin'
FAIL_LOGIN_DELAY_TIME = 10
BACKUPS_SCAN_LIMIT = 65536

PASSWORD_FORMAT = 'put-here-some-random-chars-%s-put-here-some-other-random-chars'

OPTIONAL_PASSWORD_SALT = MAIN_PATH + 'password_salt.bin'
if os.path.isfile(OPTIONAL_PASSWORD_SALT):
    raw_buf = open(OPTIONAL_PASSWORD_SALT, 'rb').read()
    checksum = base64.b85encode(hashlib.sha3_512(raw_buf).digest()).decode('utf-8')
    checksum = checksum.replace('%', ' ')
    half = len(checksum) // 2
    PASSWORD_FORMAT = checksum[:half] + PASSWORD_FORMAT + checksum[half:]


