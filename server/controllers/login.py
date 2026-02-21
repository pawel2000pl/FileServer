import cherrypy
import models
import installation
from time import time, sleep
from html import escape
from functools import wraps
from configuration import FAIL_LOGIN_DELAY_TIME


def render_loginpage(fail):
    if fail:
        yield "<div>Incorrect login data<div>"
    yield """
        <div>
            <form action="/login" method="POST">
                <input type="text" name="username"/>
                <input type="password" name="password"/>
                <input type="submit" name="login" value="login"/>
            </form>
        </div>
    """


def login(username, password):
    t0 = time()
    user = models.User.query().where('name', username).get_one()
    if user is None or not user.check_password_hash(password): 
        sleep(FAIL_LOGIN_DELAY_TIME - (time() - t0))
        raise cherrypy.HTTPRedirect('/login?fail=true')
    cherrypy.session['user_id'] = user.id
    if user.is_admin:
        if installation.requires_installation_of_admin_capabilities(user):
            installation.install_admin_capabilities()
    raise cherrypy.HTTPRedirect('/')


def is_logged_in():
    return cherrypy.session.get('user_id') is not None


def require_login(fun):

    @wraps(fun)
    def decorator(*args, **kwargs):
        if is_logged_in():
            return fun(*args, **kwargs)
        else:
            raise cherrypy.HTTPRedirect('/login')

    return decorator


def logout():
    cherrypy.session.clear()
    raise cherrypy.HTTPRedirect('/login')


def handle(*args, **kwargs):
    if is_logged_in():
        raise cherrypy.HTTPRedirect('/')
    if 'username' and 'password' in kwargs:
        return login(kwargs['username'], kwargs['password'])
    return render_loginpage('fail' in kwargs)


