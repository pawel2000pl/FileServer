import os
import flask
import models
import datetime
import controllers
import urllib.parse
import configuration
import flask_session
import response_stream
from libraries.mime import get_mimetype

application = flask.Flask(__name__)
application.config["SESSION_PERMANENT"] = True
application.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(seconds=configuration.SESSION_EXPIRES)
application.config["SESSION_TYPE"] = "filesystem"
application.config["SESSION_FILE_DIR"] = configuration.SESSION_DIR
application.config["SESSION_COOKIE_HTTPONLY"] = True
application.config["SESSION_COOKIE_SAMESITE"] = 'Lax'
application.config["SESSION_ID_LENGTH"] = 64
application.config["MAX_FORM_PARTS"] = 16384


# Initialize Flask-Session
flask_session.Session(application)


STATIC_FILES: dict[str, os.DirEntry] = dict()
for entry in os.scandir(configuration.STATIC_PATH):
    STATIC_FILES[entry.name] = entry


@application.route('/')
@response_stream.http_response
@controllers.login.require_login
def index():
    user_id = flask.session.get('user_id')
    user = models.User(id=user_id)
    raise response_stream.HTTPRedirect('/userfile/'+urllib.parse.quote(user.name))


@application.route('/favicon.ico')
@response_stream.http_response
def favicon_ico():
    yield response_stream.ResponseHeader('Content-Type', 'image/svg+xml')
    yield open(configuration.STATIC_PATH+'favicon.svg', 'rb').read()


@application.route('/.env')
@response_stream.http_response
def env():
    yield response_stream.ResponseHeader('Content-Type', 'text/plain; charset=utf-8')
    yield open(configuration.STATIC_PATH+'env.txt', 'rb').read()


@application.route('/static/<string:filename>')
@response_stream.http_response
def styles(filename):
    if filename not in STATIC_FILES:
        raise response_stream.FileNotFoundError()
    mime = get_mimetype(filename.split('.')[-1])
    if mime.startswith('text/'):
        mime += '; charet=utf-8'
    yield response_stream.ResponseHeader('Content-Type', mime)
    with open(STATIC_FILES[filename].__fspath__()) as f:
        yield f.read()


@application.route('/login', methods=['GET', 'POST'])
@response_stream.http_response
def login():
    return controllers.login.handle()


@application.route('/logout')
@response_stream.http_response
def logout():
    return controllers.login.logout()


@application.route('/userfile/<path:path>', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_login
def userfile(path):
    path = list(filter(lambda s: len(s), path.split('/')))
    if len(path) < 1: raise response_stream.HTTPError(400, 'Bad request: path too short')
    if '..' in path or '.' in path: raise response_stream.HTTPError(400, 'Bad request: invalid path elements')
    if any(map(lambda s: '/' in s or '\\' in s or s == '', path)): raise response_stream.HTTPError(400, 'Bad request: invalid path elements')
    return controllers.files.make_request(['userfile'] + path)



@application.route('/tokenfile/<path:path>', methods=['GET', 'POST'])
@response_stream.http_response
def tokenfile(path):
    path = list(filter(lambda s: len(s), path.split('/')))
    if len(path) < 1: raise response_stream.HTTPError(400, 'Bad request: path too short')
    if '..' in path or '.' in path: raise response_stream.HTTPError(400, 'Bad request: invalid path elements')
    if any(map(lambda s: '/' in s or '\\' in s or s == '', path)): raise response_stream.HTTPError(400, 'Bad request: invalid path elements')
    return controllers.files.make_request(['tokenfile'] + path)



@application.route('/users', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_admin
def users():
    return controllers.users.render_users()


@application.route('/user/<int:user_id>', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_login
def user(user_id=None):
    if isinstance(user_id, str): user_id = int(user_id)
    return controllers.users.render_user(user_id)


@application.route('/user', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_login
def new_user():
    return controllers.users.render_user(None)


@application.route('/shared_with', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_login
def shared_with():
    return controllers.shares.render_shares(True, True, False)


@application.route('/shared_by', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_login
def shared_by():
    return controllers.shares.render_shares(False, False, True)


@application.route('/shared_all', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_admin
def shared_all():
    return controllers.shares.render_shares(False, False, False)


@application.route('/create_share', methods=['GET', 'POST'])
@response_stream.http_response
@controllers.login.require_login
def create_share():
    return controllers.shares.render_create_share()
