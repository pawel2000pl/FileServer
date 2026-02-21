import liteorm
from configuration import DATABASE_FILENAME

class MainDatabase(liteorm.Database):

    database_filename = DATABASE_FILENAME
    autocommit = True


class MainDatabaseModel(liteorm.Model):

    database = MainDatabase
    skip_initialization = 1
