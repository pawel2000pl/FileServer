import sqlite3
from threading import current_thread

class Database:

    database_filename = ':memory:'
    autocommit = True


    @classmethod
    def get_connection(cls):
        thread = current_thread()
        if 'db_connections' not in thread.__dict__:
            thread.__dict__['db_connections'] = dict()
        if cls.database_filename not in thread.db_connections:
            thread.db_connections[cls.database_filename] = sqlite3.connect(cls.database_filename)
            thread.db_connections[cls.database_filename].autocommit = cls.autocommit
        return thread.db_connections[cls.database_filename]


    @classmethod
    def get_cursor(cls, cursor=None):
        if cursor is None:
            return cls.get_connection().cursor()
        thread_connection = cls.get_connection()
        if thread_connection == cursor.connection:
            return cursor
        return thread_connection.cursor()


    @classmethod
    def commit(cls):
        cls.get_connection().commit()


    @classmethod
    def rollback(cls):
        cls.get_connection().rollback()
