import flask
from models import User
from html import escape
from typing import Union
from datetime import datetime

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
    message = flask.request.args.get('message', '')
    is_error = 'msg_error' in flask.request.args
    style = 'color: red;' if is_error else ''
    yield f'''
    <div style="{style}" class="filters-form-div">
        <p>{escape(message)}</p>
    </div>
    '''


def render_menu():

    user_id = flask.session.get('user_id', None)
    user = User(id=user_id) if user_id else None

    if user is not None:
        yield f'''
            <h3>Files</h3>
            <ul>
                <li><a href="/userfile/{escape(user.name)}">Browse files</a></li>
                <li><a href="/shared_by">Shared by me</a></li>
                <li><a href="/shared_with">Shared with me</a></li>
            </ul>
        '''
    
    if user and user.is_admin:
        yield '''
            <h3>Administration</h3>
            <ul>
                <li><a href="/users">Users</a></li>
                <li><a href="/shared_all">All shares</a></li>
            </ul>
        '''

    if user is None:
        yield f'''
            <h3>Account</h3>
            <ul>
                <li><a href='/login'>Login</a></li>
            </ul>
        '''
    else:
        yield f'''
            <h3>Account</h3>
            <ul>
                <li><a href='/user/{user.id}'>Edit</a></li>
                <li><a href='/logout'>Logut</a></li>
            </ul>
        '''


def render_page(content_factory):
    yield '''
    <!DOCTYPE HTML>
    <html>
        <head>
            <link rel="stylesheet" href="/styles.css" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <meta charset="UTF-8" />
        </head>
        <body>
    '''

    yield '<div class="container">'

    yield '<div class="cell logo-cell"><img src="/favicon.svg" alt="logo"/></div>'

    yield '<div class="cell">'
    for data in render_header():
        yield data
    yield '</div>'
    
    yield '<div class="cell">'
    for data in render_menu():
        yield data
    yield '</div>'

    yield '<div class="cell">'
    for data in content_factory:
        yield data
    yield '</div>'

    yield '</div>'

    yield '''
        </body>
    </html>
    '''