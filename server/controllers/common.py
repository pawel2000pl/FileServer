import flask
import base64
from models import User
from html import escape
from typing import Union
from datetime import datetime
from configuration import STATIC_PATH, INCLUDE_STATIC, HOME_CAP_NAME

STYLES_CONTENT = ''
STYLES_COLORS_CONTENT = ''
TABLES_UTILS_CONTENT = ''
LOGO_SRC = '/static/favicon.svg'


if INCLUDE_STATIC:
    STYLES_CONTENT = open(STATIC_PATH + 'styles.css').read() + ''
    STYLES_COLORS_CONTENT = open(STATIC_PATH + 'colors.css').read()
    TABLES_UTILS_CONTENT = open(STATIC_PATH + 'table_utils.js').read()
    LOGO_SRC = 'data:image/svg+xml;base64,'+base64.b64encode(open(STATIC_PATH + 'favicon.svg', 'rb').read()).decode('utf-8')


def format_date_and_time(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    date = dt.strftime('%Y-%m-%d')
    time = dt.strftime('%H:%M:%S')
    return date, time


def format_size(size: int) -> str:
    units = ['%dB', '%.2fKiB', '%.2fMiB', '%.2fGiB', '%.2fTiB', '%.2fPiB', '%.2fEiB', '%.2fZiB', '%.2fYiB']
    for i, unit in enumerate(units):
        if size < 1024**(i+1.03) or unit == units[-1]:
            return unit%(size/1024**i)
    return '-'


def format_datetime(timestamp):
    date, time = format_date_and_time(timestamp)
    return date + ' ' + time


def render_header():
    user_id = flask.session.get('user_id', None)
    user = User(id=user_id) if user_id else None
    user_name = escape('Logged as: '+user.name) if user is not None else '<a href="/login">Login</a>'
    message = flask.request.args.get('message', '')
    is_error = 'msg_error' in flask.request.args
    style = 'color: red;' if is_error else ''
    yield f'''
    <div style="{style}" class="filters-form-div">
        <span style="float:left;">{escape(message)}</span>
        <span style="float:right;">{user_name}</span>
    </div>
    '''


def render_menu():

    user_id = flask.session.get('user_id', None)
    user = User(id=user_id) if user_id else None

    if user is not None:
        home_display = '' if user.use_home else 'style="display: none;"'
        yield f'''
        <table class="content-table menu-section">
            <thead><tr><th>Files</th></tr></thead>
            <tbody>
                <tr {home_display}><td><a href="/userfile/{escape(user.name)}/{escape(HOME_CAP_NAME)}">Home</a></td></tr>
                <tr><td><a href="/userfile/{escape(user.name)}">Browse files</a></td></tr>
                <tr><td><a href="/shared_by">Shared by me</a></td></tr>
                <tr><td><a href="/shared_with">Shared with me</a></td></tr>
            </tbody>
        </table>
        '''

    if user and user.is_admin:
        yield '''
        <table class="content-table menu-section">
            <thead><tr><th>Administration</th></tr>
            <tbody>
                <tr><td><a href="/users">Users</a></td></tr>
                <tr><td><a href="/shared_all">All shares</a></td></tr>
            </tbody>
        </table>
        '''

    if user is None:
        yield f'''
        <table class="content-table menu-section">
            <thead><tr><th>Account</th></tr>
            <tbody>
                <tr><td><a href='/login'>Login</a></td></tr>
            </tbody>
        </table>
        '''
    else:
        yield f'''
        <table class="content-table menu-section">
            <thead><tr><th>Account</th></tr>
            <tbody>
                <tr><td><a href='/user/{user.id}'>Edit</a></td></tr>
                <tr><td><a href='/logout'>Logut</a></td></tr>
            </tbody>
        </table>
        '''


def render_page(content_factory):

    header_generator = render_header()
    menu_generator = render_menu()

    yield '''
    <!DOCTYPE HTML>
    <html>
        <head>
    '''

    if INCLUDE_STATIC:
        yield '<style>'
        yield STYLES_CONTENT
        yield STYLES_COLORS_CONTENT
        yield '</style>'
    else:
        yield '<link rel="stylesheet" href="/static/styles.css" />'
        yield '<link rel="stylesheet" href="/static/colors.css" />'

    yield '''
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <meta charset="UTF-8" />
        </head>
        <body>
    '''

    yield '<div class="container">'

    yield f'''
        <div class="cell logo-cell">
            <img src="{LOGO_SRC}" alt="logo"/>
            <span>File server</span>
        </div>
        '''

    yield '<div class="cell header-cell">'
    for data in header_generator:
        yield data
    yield '</div>'

    yield '<div class="cell menu-cell">'
    for data in menu_generator:
        yield data
    yield '</div>'

    yield '<div class="cell content-cell">'
    for data in content_factory:
        yield data
    yield '</div>'

    yield '</div>'

    if INCLUDE_STATIC:
        yield '<script>'
        yield TABLES_UTILS_CONTENT
        yield '</script>'
    else:
        yield '<script src="/static/table_utils.js" defer></script>'

    yield f'''
        </body>
    </html>
    '''

