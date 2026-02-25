from liteorm import Model, RecordNotFound
from models.database import MainDatabase, MainDatabaseModel
from models.user import User
from models.capability import Capability

def auto_update():
    Model.auto_update()
