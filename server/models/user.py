import bcrypt
import liteorm
from time import time
from configuration import PASSWORD_FORMAT
from models import MainDatabaseModel


class User(MainDatabaseModel):

    id: int
    name: str
    password: str
    is_admin: bool = False

    not_null = ['is_admin']
    unique_index = ['name']


    def before_persist(self):
        self.name = self.name.replace('/', '')
        self.name = self.name.replace('\\', '')
        while '..' in self.name: self.name = self.name.replace('..', '.')


    @staticmethod
    def create_password_hash(password_text):
        return bcrypt.hashpw((PASSWORD_FORMAT%password_text).encode('utf-8'), bcrypt.gensalt(13)).decode('utf-8')


    def set_password_hash(self, password_text):
        self.password = self.create_password_hash(password_text)
        return self.password


    def check_password_hash(self, password_text):
        return bcrypt.checkpw((PASSWORD_FORMAT%password_text).encode('utf-8'), self.password.encode('utf-8'))
