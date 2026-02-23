import models
import http_utils
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
        http_utils.redirect('/login?fail=true')
    http_utils.get_session()['user_id'] = user.id
    if user.is_admin:
        if installation.requires_installation_of_admin_capabilities(user):
            installation.install_admin_capabilities()
    http_utils.redirect('/')


def is_logged_in():
    return http_utils.get_session().get('user_id', None) is not None


def require_login(fun):

    @wraps(fun)
    def decorator(*args, **kwargs):
        if is_logged_in():
            return fun(*args, **kwargs)
        else:
            http_utils.redirect('/login')

    return decorator


def require_admin(fun):

    @wraps(fun)
    def decorator(*args, **kwargs):
        try:
            user_id = http_utils.get_session().get('user_id', None)
            if user_id is None: http_utils.redirect('/login')
            user = models.User(id=user_id)
            if not user.is_admin: http_utils.redirect('/login')
        except models.RecordNotFound:
            http_utils.redirect('/login')
        return fun(*args, **kwargs)

    return decorator


def logout():
    http_utils.get_session().clear()
    http_utils.redirect('/login')


def handle(*args, **kwargs):
    if is_logged_in():
        http_utils.redirect('/')
    if 'username' and 'password' in kwargs:
        return login(kwargs['username'], kwargs['password'])
    return render_loginpage('fail' in kwargs)


