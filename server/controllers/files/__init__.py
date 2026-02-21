import models
import cherrypy
from libraries.access import StorageEntry
from typing import Iterator, Optional, Union
from controllers.common import render_page
from controllers.files.file import render_file
from controllers.files.directory import render_directory
from controllers.files.download import download_partial


def content_factory(storage_entry: Optional[StorageEntry], url: str):
    if storage_entry is None:
        return render_directory(None, url)
    if not storage_entry.read:
        raise PermissionError()
    if not storage_entry.entry.exists():
        raise cherrypy.NotFound()
    if storage_entry.entry.is_dir():
        return render_directory(storage_entry, url)
    return render_file(storage_entry, url)


def render_for_token(token: str, url_path: list[str], url: str, **kwargs) -> Iterator[Union[str, bytes]]:
    storage_entry = StorageEntry.from_token(token, url_path)
    if 'download' in kwargs:
        if not storage_entry.entry.is_file():
            raise cherrypy.HTTPError(400, 'Bad request: only files allowed.')
        return download_partial(storage_entry, kwargs.get('save', False))
    return render_page(content_factory(storage_entry, url))
    

def render_for_user(username: str, url_path: list[str], url: str, **kwargs) -> Iterator[Union[str, bytes]]:
    user_id = cherrypy.session.get('user_id', None)
    if user_id is None: raise cherrypy.HTTPRedirect('/login')
    path_user = models.User.query().where('name', username).get_one()
    if path_user is None: raise cherrypy.NotFound
    storage_entry = StorageEntry.from_user(user_id, url_path) if len(url_path) else None
    if 'download' in kwargs:
        if storage_entry is None:
            raise cherrypy.HTTPError(400, 'Bad request: Downloading a home directory is not allowed.')
        if not storage_entry.entry.is_file():
            raise cherrypy.HTTPError(400, 'Bad request: only files allowed.')
        return download_partial(storage_entry, kwargs.get('save', False))
    return render_page(content_factory(storage_entry, url))
    
