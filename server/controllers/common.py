import json
import flask
import base64
from time import time
from models import User
from html import escape
from threading import Lock
from datetime import datetime
from collections import defaultdict, deque
from typing import Union, Iterable, Optional
from configuration import STATIC_PATH, INCLUDE_STATIC, HOME_CAP_NAME
from configuration import NOTIFICATIONS_TIMEOUT, MAX_NOTIFICATIONS_PER_USER, MAX_NOTIFICATIONS

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


notifications_lock = Lock()
notifications: defaultdict[int, deque[tuple[str, float]]] = defaultdict(deque)
notifications_count = 0


def remove_user_notifications(user_id: int):
    global notifications, notifications_lock, notifications_count
    with notifications_lock:
        if not user_id in notifications: return
        notifications_count -= len(notifications.pop(user_id))


def clear_oldest_notifications():
    global notifications, notifications_lock, notifications_count
    with notifications_lock:
        for k in list(notifications.keys()):
            l = len(notifications[k])
            if l > 0:
                notifications[k].popleft()
            if l <= 1:
                notifications.pop(k)
        notifications_count = sum(map(len, notifications.values()))
            

def clear_old_notifications():
    global notifications, notifications_lock, notifications_count
    now = time()
    with notifications_lock:
        for k in list(notifications.keys()):
            new_list = deque(filter(lambda x: x[1] > now, notifications[k]))
            if len(new_list):
                notifications[k] = new_list
            else:
                notifications.pop(k)
        notifications_count = sum(map(len, notifications.values()))


def add_notification(message: str, user_id: Optional[int]):
    if user_id is None: return
    global notifications, notifications_lock, notifications_count
    with notifications_lock:
        if notifications_count >= MAX_NOTIFICATIONS:
            clear_old_notifications()
        if notifications_count >= MAX_NOTIFICATIONS:
            clear_oldest_notifications()
        notifications_count += 1
        notifications[user_id].append((message, time() + NOTIFICATIONS_TIMEOUT))
        if len(notifications[user_id]) > MAX_NOTIFICATIONS_PER_USER:
            notifications[user_id].popleft()
            notifications_count -= 1


def render_notifications(user_id: int) -> Iterable[str]:
    global notifications, notifications_lock
    LIMIT = 64
    with notifications_lock:
        if not user_id in notifications or len(notifications[user_id]) == 0:
            yield ''
            return
        yield '<script>var tmp_notification = "";</script>'
        for content, timestamp in notifications[user_id]:            
            dumped_date = json.dumps(escape('[%s] ' % format_datetime(timestamp)))
            dumped_content = json.dumps(escape(content))
            end_dots = '"..."' if len(content) > LIMIT else '""'
            yield f'''
            <script>
                tmp_notification = {dumped_content};
                notifications_list.innerHTML = {dumped_date} + tmp_notification + '<br/>' + notifications_list.innerHTML;
                last_notification.innerHTML = tmp_notification.substr(0,{LIMIT}) + {end_dots};
            </script>
            '''
    

def render_header() -> Iterable[str]:
    user_id = flask.session.get('user_id', None)
    user = User(id=user_id) if user_id else None
    user_name = escape('Logged as: '+user.name) if user is not None else '<a href="/login">Login</a>'
    server_time = " ".join(format_date_and_time(time()))
    yield f'''
    <div class="notifications-div">
        <details>
            <summary id="last_notification">
                <span style="opacity:0.5;">No more notifications</span>
            </summary>
            <div id="notifications_panel">
                <div id="notifications_list">
                </div>
                <br/>
                <span class="link-like-button" onclick="
                    fetch('/clear_notifications');
                    notifications_list.innerHTML = '';
                    last_notification.innerHTML = last_notification_default_html;
                    ">Clear all notifications
                </span>
            </div>
        </details>
        <script>
            const last_notification_default_html = last_notification.innerHTML;
        </script>
        <div style="float: right;">
            <span style="opacity:50%;">{server_time}</span>
            <span style="">{user_name}</span>
        </div>
    </div>
    '''


def render_menu(user_id: Optional[int]) -> Iterable[str]:

    user = User(id=user_id) if user_id else None

    if user is not None:
        home_display = '' if user.use_home and user.has_home() else 'style="display: none;"'
        yield '''
        <span class="menu-header" onclick="
            menuVisibility[menuVisibilityMode] = !menuVisibility[menuVisibilityMode];
            recalculateMenuVisibility();
            ">Menu</span>
        <script>
            var menuVisibility = { true: true, false: false };
            var menuVisibilityMode = null;
            const recalculateMenuVisibility = () => {
                const currentVisibility = menuVisibility[menuVisibilityMode];
                Array.from(document.getElementsByClassName('menu-section')).forEach((element) => {                
                    element.style.display = currentVisibility ? 'table' : 'none';
                });
                if (menuVisibilityMode) {
                    main_container.style.gridTemplateColumns = currentVisibility ? '20% 1fr' : 'min-content 1fr';
                    page_title.style.display = currentVisibility ? '' : 'none';
                } else {
                    main_container.style.gridTemplateColumns = '1fr';
                    page_title.style.display = '';
                }
            };
            const resizeMenu = () => {
                if (menuVisibilityMode === null) menuVisibilityMode = document.body.clientWidth >= 768;
                else if (menuVisibilityMode && document.body.clientWidth < 768) menuVisibilityMode = false;
                else if (!menuVisibilityMode && document.body.clientWidth >= 768) menuVisibilityMode = true;                
                else return;
                recalculateMenuVisibility();
            };
            window.addEventListener('load', resizeMenu);
            window.addEventListener('resize', resizeMenu);
        </script>
        '''
        yield f'''<table class="content-table menu-section">
            <thead><tr><th>Files</th></tr></thead>
            <tbody>
                <tr {home_display}><td><a href="/userfile/{escape(user.name)}/{escape(HOME_CAP_NAME)}">Home</a></td></tr>
                <tr><td><a href="/userfile/{escape(user.name)}">Browse files</a></td></tr>
                <tr><td><a href="/shared_with">Shared with me</a></td></tr>
                <tr><td><a href="/shared_by">Shared by me</a></td></tr>
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


def render_page(content_factory) -> Iterable[str]:

    user_id = flask.session.get('user_id', None)
    header_generator = render_header()
    menu_generator = render_menu(user_id)

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

    yield '<div id="main_container" class="container">'

    yield f'''
        <div class="cell logo-cell">
            <img src="{LOGO_SRC}" alt="logo"/>
            <span id="page_title">File server</span>
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

    if user_id is not None:
        for data in render_notifications(user_id):
            yield data

    yield f'''
        </body>
    </html>
    '''

