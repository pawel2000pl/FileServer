import os
import models
import cherrypy
import configuration
import controllers
import urllib.parse

class Server:

    @cherrypy.expose()
    @controllers.login.require_login
    def index(self):
        user_id = cherrypy.session.get('user_id')
        user = models.User(id=user_id)
        raise cherrypy.HTTPRedirect('/userfile/'+urllib.parse.quote(user.name))


    @cherrypy.expose(alias='styles.css')
    def styles(self):        
        cherrypy.response.headers['Content-Type'] = 'text/css'
        return open(configuration.STATIC_PATH+'styles.css').read()


    @cherrypy.expose(alias='.env')
    def env(self, *args, **kwargs):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return open(configuration.STATIC_PATH+'env.txt')


    @cherrypy.expose()
    def login(self, *args, **kwargs):
        return controllers.login.handle(*args, **kwargs)


    @cherrypy.expose()
    def logout(self):
        return controllers.login.logout()


    @cherrypy.expose(alias='userfile')
    @controllers.login.require_login
    def userfile(self, *path, **kwargs):
        path = list(path)
        if len(path) < 1: raise cherrypy.HTTPError(400, 'Bad request: path too short')
        if '..' in path or '.' in path: raise cherrypy.HTTPError(400, 'Bad request: invalid path elements')
        if any(map(lambda s: '/' in s or '\\' in s or s == '', path)): raise cherrypy.HTTPError(400, 'Bad request: invalid path elements')
        try:
            return controllers.files.render_for_user(['userfile'] + path, **kwargs)
        except PermissionError:
            raise cherrypy.HTTPError(403, 'Forbidden')
        except FileNotFoundError:
            raise cherrypy.NotFound
        except models.RecordNotFound:
            raise cherrypy.NotFound


    @cherrypy.expose(alias='tokenfile')
    def tokenfile(self, *path, **kwargs):
        path = list(path)
        if len(path) < 1: raise cherrypy.HTTPError(400, 'Bad request: path too short')
        if '..' in path or '.' in path: raise cherrypy.HTTPError(400, 'Bad request: invalid path elements')
        if any(map(lambda s: '/' in s or '\\' in s or s == '', path)): raise cherrypy.HTTPError(400, 'Bad request: invalid path elements')
        try:
            return controllers.files.render_for_token(['tokenfile'] + path, **kwargs)
        except (PermissionError, NotImplementedError):
            raise cherrypy.HTTPError(403)
        except (FileNotFoundError, models.RecordNotFound):
            raise cherrypy.NotFound()


    @cherrypy.expose(alias='users')
    @controllers.login.require_admin
    def users(self, *args, **kwargs):
        return controllers.users.render_users(*args, **kwargs)


    @cherrypy.expose(alias='user')
    @controllers.login.require_login
    def user(self, user_id=None, **kwargs):
        if isinstance(user_id, str): user_id = int(user_id)
        return controllers.users.render_user(user_id, **kwargs)


    @cherrypy.expose(alias='shared_with')
    @controllers.login.require_login
    def shared_with(self, **kwargs):
        return controllers.shares.render_shares(True, False, **kwargs)


    @cherrypy.expose(alias='shared_by')
    @controllers.login.require_login
    def shared_by(self, **kwargs):
        return controllers.shares.render_shares(False, True, **kwargs)


    @cherrypy.expose(alias='shared_all')
    @controllers.login.require_admin
    def shared_all(self, **kwargs):
        return controllers.shares.render_shares(False, False, **kwargs)

