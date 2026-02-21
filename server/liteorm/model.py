import sys
import sqlite3
import logging
from enum import Enum
from time import time
from typing import Optional, Union, Any, Iterator, Type, Self, Collection
from liteorm.query import Query
from liteorm.database import Database


ALL_REGISTRED_MODELS = []


class RecordNotFound(Exception):
    pass


class UpdateSchemaResult(Enum):
    ADDITIONAL_FKS = 0
    ADDITIONAL_FIELDS = 1
    OK = 2


class Model:
    
    id: int

    table_name: Optional[str] = None
    primary_key = 'id'
    not_null: list[str] = []
    multi_index: list[Union[str, Collection[str]]] = []
    unique_index: list[Union[str, Collection[str]]] = []
    default_values: dict[str, Any] = dict()

    database: Type[Database]
    skip_initialization = 0
    logger = logging.getLogger(__name__)
    cache_size = 256

    # private / for internal usage
    __primary_key_index = -1
    __cache: dict
    __not_null_set: set


    def __init_subclass__(cls):
        super().__init_subclass__()
        if cls.skip_initialization > 0:
            cls.skip_initialization -= 1
            return
        ALL_REGISTRED_MODELS.append(cls)
        cls.__annotations__[cls.primary_key] = int
        cls.__primary_key_index = next(i for i, v in enumerate(cls.__annotations__.keys()) if v == cls.primary_key)
        cls.__not_null_set = set(cls.not_null)
        cls.__cache = dict()
        cls.__update_table_name()
        cls.__update_annotations()
        cls.__update_defaults()
        cls.logger.info(f'Detected model {cls.__name__} with table name {cls.table_name}')


    def __init__(self, **kwargs):
        super().__init__()
        self.__subobjects = dict()
        self.__data = dict()
        self.__modified = True
        if len(kwargs) < len(self.__annotations__) and kwargs.get(self.primary_key, None) is not None:
            self.set_pk_val(kwargs.pop(self.primary_key))
            self.reload()
        self.fill(kwargs)


    @classmethod
    def __update_table_name(cls):
        if cls.table_name is not None:
            return cls.table_name
        result = ''
        for c in cls.__name__:
            if c >= 'A' and c <= 'Z':
                result += '_' + c.lower()
            else:
                result += c
        if result.startswith('_'):
            result = result[1:]
        cls.table_name = result
        return result

    
    @classmethod
    def __update_annotations(cls):
        keys = list(cls.__annotations__.keys())
        for key in keys:
            if isinstance(cls.__annotations__[key], type) and not issubclass(cls.__annotations__[key], (int, str, bool, float, bytes, Model)):
                del cls.__annotations__[key]
            if not isinstance(cls.__annotations__[key], str): continue
            types = cls.get_custom_types()
            data = key.rsplit('.', 1)
            if cls.__annotations__[key] == cls.__name__:
                cls.__annotations__[key] = cls
            elif key in types:
                cls.__annotations__[key] = types[key]
            elif len(data) == 2 and data[0] in sys.modules and issubclass(sys.modules[data[0]].__dict__[data[1]], Model):
                cls.__annotations__[key] = sys.modules[data[0]].__dict__[data[1]]
            else:
                cls.__annotations__[key] = int


    @classmethod
    def __update_defaults(cls):
        if cls == Model: return
        if 'default_values' not in cls.default_values or len(cls.default_values) == 0:
            cls.default_values = dict()
        reserved_names = set(Model.__dict__.keys())
        for column in cls.__annotations__.keys():
            if not column in cls.__dict__: continue
            if column.startswith('__'): continue
            if column in cls.default_values: continue
            cls.default_values[column] = cls.__dict__[column]
            delattr(cls, column)


    @classmethod
    def get_custom_types(cls) -> dict[str, type]:
        """
        This method should import other modules with types used in annotations
        and return it as a dictionary
        """
        return dict()


    @classmethod
    def get_columns(cls) -> list[str]:
        return list(cls.__annotations__.keys())


    @classmethod
    def query(cls) -> Query[Self]:
        return Query(cls)


    @classmethod
    def get_default_value(cls, column: str) -> Any:
        assert column in cls.__annotations__
        return cls.default_values.get(column, None)


    def fill(self, data: Union[dict, tuple]):
        if isinstance(data, dict):
            for col, val in data.items():
                if col in self.__annotations__:
                    self.set_value(col, val)
        else:
            assert len(self.__annotations__) == len(data)
            for col, val in zip(self.__annotations__.keys(), data):
                self.set_value(col, val)            
        return self


    def get_value(self, column: str, raw: bool = False) -> Any:
        assert column in self.__annotations__
        if (not raw) and issubclass(self.__annotations__[column], Model):
            if self.__subobjects.get(column, None) is None:
                if self.__data.get(column, None) is None: 
                    return None
                model_class = self.__annotations__[column]
                self.__subobjects[column] = model_class(**{model_class.primary_key: self.__data[column]})
            return self.__subobjects[column]
        return self.__data.get(column, None)
            

    def set_value(self, column: str, value: Any):
        assert column in self.__annotations__
        dtype = self.__annotations__[column]
        self.__modified = True
        if issubclass(dtype, Model):
            if isinstance(value, dtype):
                self.__data[column] = value.get_pk_val()
                self.__subobjects[column] = value
            else:
                self.__data[column] = None if value is None else int(value)
                self.__subobjects[column] = None
        else:
            self.__data[column] = None if value is None else dtype(value)


    def __getattr__(self, name: str) -> Any:
        if name in self.__annotations__:
            return self.get_value(name)
        assert False


    def __setattr__(self, name: str, value: Any):
        if name in self.__annotations__:
            return self.set_value(name, value)
        return super().__setattr__(name, value)


    def __getitem__(self, name: str) -> Any:
        return self.get_value(name)


    def __setitem__(self, name: str, value: Any):
        return self.set_value(name, value)
        

    def __str__(self):
        return self.__class__.__name__ + ':\n'+str().join(['\t'+col+': '+repr(self.__data[col])+'\n' for col in self.get_columns()])
        

    def __repr__(self):
        return self.__class__.__name__ + '('+', '.join([str(col)+'='+repr(self.__data.get(col, None)) for col in self.get_columns()])+')'


    def get_recursive_by(self, column: str, key_column: Union[str, None] = None, include_self : bool = True) -> Iterator[Self]:
        assert column in self.__annotations__
        assert self.__annotations__[column] == self.__class__
        if key_column is None: key_column = self.primary_key
        assert key_column in self.__annotations__
        assert key_column != column
        pk_val = self.get_pk_val()
        cursor = self.database.get_cursor()
        cursor.execute(f'''
            WITH RECURSIVE __temp_recursive_table__({key_column}, {column}) AS (
                SELECT {self.table_name}.{key_column}, {self.table_name}.{column} FROM {self.table_name} WHERE {self.table_name}.{key_column} = ?
                UNION
                SELECT {self.table_name}.{key_column}, {self.table_name}.{column} FROM __temp_recursive_table__ JOIN {self.table_name} ON ({self.table_name}.{key_column} = __temp_recursive_table__.{column})
            )
            SELECT __temp_recursive_table__.{key_column} FROM __temp_recursive_table__
        ''', [pk_val])
        return (self.__class__(**{self.primary_key: pk}) for pk, in cursor if include_self or pk != pk_val)


    @classmethod
    def add_cache(cls, record: tuple):
        assert isinstance(record, tuple)
        assert len(record) == len(cls.__annotations__)
        if cls.cache_size > 0:
            cls.__cache[int(record[cls.__primary_key_index])] = record
            if len(cls.__cache) > cls.cache_size:
                key, = (k for _, k in zip((0,), cls.__cache.keys()))
                cls.__cache.pop(key, None)
        return cls


    def reload(self, cursor=None):
        pk = self.get_pk_val()
        if pk is None: raise RecordNotFound(self.table_name, pk)
        record = self.__cache.get(pk, None)
        if record is None:
            cursor = self.database.get_cursor(cursor)
            columns_list = self.get_columns()
            columns_list_str = ', '.join(columns_list)
            cursor.execute(f'SELECT {columns_list_str} FROM {self.table_name} WHERE {self.primary_key} = ? LIMIT 1', [self.get_pk_val()])
            data = cursor.fetchall()
            if len(data):
                record = data[0]
                self.add_cache(record)
            else:
                raise RecordNotFound(self.table_name, pk)
        if record is not None:
            self.fill(record)
            self.__modified = False


    def get_pk_val(self) -> Optional[int]:
        return self.__data.get(self.primary_key, None)


    def set_pk_val(self, value: int):
        self.__data[self.primary_key] = int(value)


    def exists(self, cursor=None) -> bool:
        pk_val = self.get_pk_val()
        if pk_val is None:
            return False
        cursor = self.database.get_cursor(cursor)
        cursor.execute(f'SELECT 1 FROM {self.table_name} WHERE {self.primary_key} = ? LIMIT 1', [pk_val])
        return len(cursor.fetchall()) > 0


    def invalidate_cache(self):
        self.__cache.pop(self.get_pk_val(), None)

    
    @classmethod
    def invalidate_model_cache(cls):
        cls.__cache.clear()


    @staticmethod
    def invalidate_all_cache():
        for model in ALL_REGISTRED_MODELS:            
            model.__cache.clear()


    def delete(self, cursor=None):
        cursor = self.database.get_cursor(cursor)
        cursor.execute(f'DELETE FROM {self.table_name} WHERE {self.primary_key} = ?', self.get_pk_val())
        self.invalidate_cache()
        return connection


    def modified(self) -> bool:
        return self.__modified


    def persist(self, cursor = None, force: bool = False) -> None:
        if not (force or self.__modified): return
        cursor = self.database.get_cursor(cursor)
        self.before_persist()
        for col, obj in self.__subobjects.items():
            if obj is None: continue
            obj.persist(cursor)
            self.__data[col] = obj.get_pk_val()
        if self.get_pk_val() is None:
            self.before_insert()
            insert_columns = list(k for k, v in self.__data.items() if v is not None)
            if len(insert_columns) == 0:
                cursor.execute(f'INSERT INTO {self.table_name} ({self.primary_key}) SELECT MAX({self.primary_key})+1 FROM {self.table_name}')
            else:
                insert_columns_str = ', '.join(insert_columns)
                insert_columns_params_str = ', '.join(['?']*len(insert_columns))
                cursor.execute(                
                    f'INSERT INTO {self.table_name} ({insert_columns_str}) VALUES ({insert_columns_params_str})',
                    [self.__data.get(col, None) for col in insert_columns]
                )
            self.set_pk_val(cursor.lastrowid)
            self.invalidate_cache()
            self.reload(cursor)
            self.after_insert()
        else:
            self.before_update()
            columns_list_no_pk = [col for col in self.get_columns() if col != self.primary_key]
            update_list_str = ', '.join([col + ' = ?' for col in columns_list_no_pk])
            cursor.execute(
                f'UPDATE {self.table_name} SET {update_list_str} WHERE {self.primary_key} = ?',
                [self.__data.get(col, None) for col in columns_list_no_pk] + [self.get_pk_val()]
            )
            self.invalidate_cache()
            self.after_update()
        self.__modified = False
        self.after_persist()


    def before_persist_checks(self):
        pass


    def before_persist(self):
        pass


    def before_update(self):
        pass


    def before_insert(self):
        pass


    def after_persist(self):
        pass


    def after_update(self):
        pass


    def after_insert(self):
        pass

    
    @staticmethod
    def __simple_escape(val: Union[None, int, float, str, bool]) -> str:
        if val is None:
            return 'NULL'
        if isinstance(val, (float, int, bool)):
            return str(val)
        return '('+' || '.join(['char('+str(ord(c))+')' for c in val])+')'


    @classmethod
    def __create_field_sql(cls, name: str, dtype: type) -> str:
        TYPE_MAP = {
            'int': 'INTEGER',
            'float': 'FLOAT',
            'str': 'TEXT',
            'bytes': 'BYTES',
            'bool': 'BOOLEAN'
        }
        if name == cls.primary_key:
            return f'{name} INTEGER PRIMARY KEY AUTOINCREMENT'
        elif issubclass(dtype, Model):
            default_value = cls.__simple_escape(cls.get_default_value(name))
            default_sql = '' if default_value == 'NULL' else 'DEFAULT ' + default_value 
            not_null_sql = 'NOT NULL' if name in cls.__not_null_set else ''
            return f'{name} INTEGER {not_null_sql} {default_sql} REFERENCES {dtype.table_name}({dtype.primary_key})'
        else:
            return f'{name} {TYPE_MAP.get(dtype.__name__, dtype.__name__).upper()}'


    @classmethod
    def create_table_sql(cls) -> str:
        # requires PRAGMA foreign_keys = 0
        fields = []
        for name, dtype in cls.__annotations__.items():
            fields.append(cls.__create_field_sql(name, dtype))
        fields_sql = ','.join(fields)
        return f'CREATE TABLE {cls.table_name} ({fields_sql})'


    @classmethod
    def create_indexes_sql(cls) -> list[str]:
        assert cls.table_name is not None
        cmds = []
        uniques = set(cls.unique_index)
        for columns in cls.unique_index + cls.multi_index:
            is_uniq = columns in uniques
            uniq_sql = 'UNIQUE' if is_uniq else ''
            if isinstance(columns, str): columns = [columns]
            if not isinstance(columns, list): columns = list(columns)
            index_name = '_'.join([cls.table_name, 'UNIQ' if is_uniq else 'MULTI', 'INDEX'] + columns).upper()
            columns_sql = ', '.join(columns)
            cmds.append(f'CREATE {uniq_sql} INDEX IF NOT EXISTS {index_name} ON {cls.table_name}({columns_sql})')
        return cmds


    @classmethod
    def recreate_table(cls, cursor=None, copy_data: bool=True, clear_data: bool = True) -> None:
        """
        Recreates the table in the database. Requires foreign_keys=off.
        """
        if cls.table_name is None: return
        cls.logger.info(f'Recreating the table "{cls.table_name}"; copy: {copy_data}, clear: {clear_data}')
        PREFIX = '__old_table_%d_' % int(time()*1000)
        cursor = cls.database.get_cursor(cursor)
        cursor.execute('SELECT name FROM sqlite_master WHERE name = ?', [cls.table_name])
        table_exists = len(cursor.fetchall()) > 0
        old_table_name = PREFIX + cls.table_name      
        db_field_names = []
        if table_exists:  
            cursor.execute(f'PRAGMA table_info("{cls.table_name}")')
            db_field_names = [row[1] for row in cursor]
            cursor.execute(f'ALTER TABLE {cls.table_name} RENAME TO {old_table_name}')
        cursor.execute(cls.create_table_sql())
        if table_exists and copy_data:
            common_fields = list(set(cls.__annotations__.keys()).intersection(db_field_names))
            common_fields_sql = ', '.join(common_fields)
            cursor.execute(f'INSERT INTO {cls.table_name} ({common_fields_sql}) SELECT {common_fields_sql} FROM {old_table_name}')
        if table_exists and clear_data:
            cursor.execute(f'DROP TABLE {old_table_name}')
        for cmd in cls.create_indexes_sql():
            cursor.execute(cmd)
        cls.logger.info(f'Recreating the table "{cls.table_name}" finished')



    @classmethod
    def update_schema(cls, cursor = None) -> UpdateSchemaResult:
        """
        Updates database schema of the table. Requires foreign_keys=off.
        Returns UpdateSchemaResult.OK (2) if updating is ok.
        Returns UpdateSchemaResult.ADDITIONAL_FIELDS (1) if there are some additional fields.
        Returns UpdateSchemaResult.ADDITIONAL_FKS (0) if there are some additional foreign keys.
        SQLite has dynamic typing so invalid column type can be omitted.
        Only additional foreign keys might broke the application.
        """
        cls.logger.info(f'Updating the table schema: {cls.table_name}')
        cursor = cls.database.get_cursor(cursor)
        result = UpdateSchemaResult.OK
        cmds = []
        # cid|name|type|notnull|dflt_value|pk
        cursor.execute(f'PRAGMA table_info("{cls.table_name}")')
        db_data = cursor.fetchall()
        if len(db_data) == 0:
            cmds = [cls.create_table_sql()]
            cmds.extend(cls.create_indexes_sql())
            cls.logger.info(f'Created a missing table: {cls.table_name}')
        else:
            db_names = set(row[1] for row in db_data)
            for name, dtype in cls.__annotations__.items():
                if name in db_names:
                    db_names.remove(name)
                else:
                    cls.logger.info(f'Created a missing column: {cls.table_name}.{name}')
                    cmds.append(f'ALTER TABLE {cls.table_name} ADD COLUMN {cls.__create_field_sql(name, dtype)}')
            if len(db_names):
                result = UpdateSchemaResult.ADDITIONAL_FIELDS
                cls.logger.warning(f'Unused fields in the table "{cls.table_name}": {repr(db_names)}')
            # id|seq|table|from|to|on_update|on_delete|match
            cursor.execute(f'PRAGMA foreign_key_list("{cls.table_name}")')
            db_fks = cursor.fetchall()
            for row in db_fks:
                if row[3] not in cls.__annotations__ \
                or not issubclass(cls.__annotations__[row[3]], Model) \
                or cls.__annotations__[row[3]].table_name != row[2] \
                or cls.__annotations__[row[3]].primary_key != row[4]:                    
                    result = UpdateSchemaResult.ADDITIONAL_FKS
                    cls.logger.warning(f'Unused foreign keys in the table {cls.table_name}.{row[3]} -> {row[2]}.{row[4]}')

        cmds.extend(cls.create_indexes_sql())
        for cmd in cmds: 
            cursor.execute(cmd)
        cls.logger.info(f'Updating the table "{cls.table_name}" finished with result: {result.name}')
        return result


    @staticmethod
    def find_unregstred_tables(database: Database) -> list[str]:
        cursor = database.get_cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type = "table" AND name != "sqlite_sequence"')
        db_tables = set(v for v, in cursor.fetchall())
        for model in ALL_REGISTRED_MODELS:
            if model.database == database:
                db_tables.remove(model.table_name)
        return list(db_tables)


    @staticmethod
    def auto_update() -> None:
        Model.logger.info('Started auto updating')
        recreated = False
        for model in ALL_REGISTRED_MODELS:
            if model.update_schema() == 0:
                model.recreate_table()
                recreated = True
        databases = set(model.database for model in ALL_REGISTRED_MODELS)
        for database in databases:
            additional_tables = Model.find_unregstred_tables(database)
            if len(additional_tables) == 1:
                Model.logger.warning(f'There is one additional table in the {database.database_filename}: {additional_tables}')
            elif len(additional_tables) > 1:
                Model.logger.warning(f'There are {len(additional_tables)} additional tables in the {database.database_filename}: {additional_tables}')
        if not recreated: return
        bad_update = False
        for model in ALL_REGISTRED_MODELS:
            if model.update_schema() == 0:
                bad_update = True
                break
        if not bad_update: return
        Model.logger.warning('Recreating all tables')
        for model in ALL_REGISTRED_MODELS:
            model.recreate_table()

