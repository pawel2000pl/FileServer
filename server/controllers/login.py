import flask
import models
import installation
import response_stream
from html import escape
from functools import wraps
from time import time, sleep
from typing import Iterator, Optional
from controllers.common import render_page
from configuration import FAIL_LOGIN_DELAY_TIME, SESSION_CLEANUP_INTERVAL


LAST_CLEANUP: Optional[float] = None


def check_cleanup():
    global LAST_CLEANUP
    now = time()
    if LAST_CLEANUP is None or now - LAST_CLEANUP > SESSION_CLEANUP_INTERVAL:
        installation.delete_expired_sessions()
        LAST_CLEANUP = now


def render_loginpage(fail) -> Iterator[str]:
    if fail:
        yield "<div>Incorrect login data<div>"
    yield """
        <div class="login-panel">
            <form action="/login" method="POST">
                <table class="content-table">
                    <tr class="header">
                        <td>Username</td>
                        <td><input type="text" name="username"/></td>
                    </tr>
                    <tr>
                        <td>Password</td>
                        <td><input type="password" name="password"/></td>
                    </tr>
                    <tr>
                        <td></td>
                        <td><input type="submit" name="login" value="Login"/></td>
                    </tr>
                </table>
            </form>
        </div>
    """


def login(username, password) -> Iterator[str]:
    t0 = time()
    user = models.User.query().where('name', username).get_one()
    if user is None or not user.check_password_hash(password):
        sleep(FAIL_LOGIN_DELAY_TIME - (time() - t0))
        raise response_stream.HTTPRedirect('/login?fail=true')
    flask.session['user_id'] = user.id
    if user.is_admin:
        if installation.requires_installation_of_admin_capabilities(user):
            installation.install_admin_capabilities()
    raise response_stream.HTTPRedirect('/')


def is_logged_in() -> bool:
    check_cleanup()
    user_id = flask.session.get('user_id', None)
    return models.User.static_exists(user_id)


def require_login(fun):

    @wraps(fun)
    def decorator(*args, **kwargs):
        if is_logged_in():
            return fun(*args, **kwargs)
        else:
            raise response_stream.HTTPRedirect('/login')

    return decorator


def require_admin(fun):

    @wraps(fun)
    def decorator(*args, **kwargs):
        try:
            check_cleanup()
            user_id = flask.session.get('user_id', None)
            if user_id is None: raise response_stream.HTTPRedirect('/login')
            user = models.User(id=user_id)
            if not user.is_admin: raise response_stream.HTTPRedirect('/login')
        except models.RecordNotFound:
            raise response_stream.HTTPRedirect('/login')
        return fun(*args, **kwargs)

    return decorator


def logout():
    flask.session.clear()
    raise response_stream.HTTPRedirect('/login')


def handle() -> response_stream.ResponseStream:
    if is_logged_in():
        raise response_stream.HTTPRedirect('/')
    if 'username' in flask.request.form and 'password' in flask.request.form:
        return login(flask.request.form['username'], flask.request.form['password'])
    return render_page(render_loginpage('fail' in flask.request.args))


