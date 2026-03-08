import os
import bcrypt
import models
import liteorm
import configuration
from time import time
from models import MainDatabaseModel


class User(MainDatabaseModel):

    id: int
    name: str
    password: str
    is_admin: bool = False
    show_in_share_list: bool = True
    active: bool = True
    use_home: bool = False

    not_null = ['is_admin', 'active']
    unique_index = ['name']


    def before_persist(self):
        self.name = self.name.replace('/', '')
        self.name = self.name.replace('\\', '')
        while '..' in self.name: self.name = self.name.replace('..', '.')


    def after_persist(self):
        home_path = '%s/user%d'%(configuration.USERS_HOME_STORAGE, self.id)
        cap = models.Capability.query().where('user', self.id).where('name', configuration.HOME_CAP_NAME).where('storage_path', home_path).where('write').get_one()
        if self.use_home:
            if cap is None:
                cap = models.Capability()
                cap.user = self
                cap.storage_path = home_path
                cap.write = True
                cap.name = configuration.HOME_CAP_NAME
                cap.persist(recurrent=False)
            system_path = configuration.STORAGE_PATH + home_path
            if not os.path.exists(system_path):
                os.makedirs(system_path)
        elif cap is not None:
            cap.delete()


    @staticmethod
    def create_password_hash(password_text):
        return bcrypt.hashpw(password_text.encode('utf-8'), bcrypt.gensalt(13)).decode('utf-8')


    def set_password_hash(self, password_text):
        self.password = self.create_password_hash(password_text)
        self.check_password_hash(password_text)
        return self.password


    def check_password_hash(self, password_text):
        return self.active and bcrypt.checkpw(password_text.encode('utf-8'), self.password.encode('utf-8'))
