import os
import models
import logging

from configuration import DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_PASSWORD, STORAGE_PATH

logger = logging.getLogger(__name__)


def requires_installation_of_admin_capabilities(user: models.User) -> bool:
    assert user.is_admin
    for entry in os.scandir(STORAGE_PATH):
        query = models.Capability.query()
        query.where('user', user)
        query.where('storage_path', entry.name)
        query.where('write')
        if query.get_one() is not None:
            return True
    return False


def install_admin_capabilities():
    admin_query = models.User.query().where('is_admin', True)
    for entry in os.scandir(STORAGE_PATH):
        for admin in admin_query.get():
            query = models.Capability.query()
            query.where('user', admin)
            query.where('storage_path', entry.name)
            query.where('write')
            if query.get_one() is not None: continue
            models.Capability(user=admin, write=True, storage_path=entry.name, name=entry.name).persist()
            logger.warning(f'Added rw capabilities for user {admin.name} for file {entry.name}')


def install_admin():
    admin = models.User.query().where('name', DEFAULT_ADMIN_NAME).get_one()
    if admin is None:
        admin = models.User(name=DEFAULT_ADMIN_NAME, is_admin=True)
        admin.set_password_hash(DEFAULT_ADMIN_PASSWORD)
        logger.warning(f'Created a new user "{DEFAULT_ADMIN_NAME}" with the default password "{DEFAULT_ADMIN_PASSWORD}" - change it ASAP!')
    elif admin.check_password_hash(DEFAULT_ADMIN_PASSWORD):
        logger.warning(f'The default user "{DEFAULT_ADMIN_NAME}" has still the default password "{DEFAULT_ADMIN_PASSWORD}" - change it ASAP!')
    if not admin.is_admin:
        admin.is_admin = True
        logger.warning(f'The default user "{DEFAULT_ADMIN_NAME}" has not been marked as admin')
    admin.persist()
    install_admin_capabilities()
