import flask
import models
from html import escape
from typing import Optional
from controllers.common import render_page


def render_users_table():
    yield '''
    <div class="section-div userslist-div">
        <table class="content-table dynamic-table user-table">
            <thead>
                <tr>
                    <th class="dynamic">id</th>
                    <th class="main-column dynamic">Name</th>
                    <th class="dynamic">is admin</th>
                </tr>
            </thead>
            <tbody>
    '''

    for user in models.User.query().get():
        yield f'''
            <tr>
                <td>{user.id}</td>
                <td class="main-column"><a href="/user/{user.id}">{escape(user.name)}</a></td>
                <td>{user.is_admin}</td>
            </tr>
        '''

    yield '''
            </tbody>
        </table>
    </div>
    <p>
        <a href="/user">Create a new user</a>
    </p>
    '''



def render_user_edit(user_id: Optional[int]):
    user = models.User(name='new_user') if user_id is None else models.User(id=user_id)
    logged_id = flask.session.get('user_id', None)
    if logged_id is None: raise PermissionError()
    logged_user = models.User(id=logged_id)
    if not logged_user.is_admin and logged_user.id != user.id:
        raise PermissionError()

    if logged_user.is_admin:
        yield '<p><a href="/users">Back to users list</a></p>'

    error_msg = ''
    try:
        if 'save-changes' in flask.request.form:
            if 'name' in flask.request.form:
                user.name = flask.request.form['name']
            if 'password' in flask.request.form and flask.request.form['password'] != '':
                user.set_password_hash(flask.request.form['password'])
            if logged_user.is_admin:
                if 'is_admin' in flask.request.form:
                    user.is_admin = True
                else:
                    user.is_admin = False
            user.persist()
    except ValueError as err:
        error_msg = 'Cannot save changes. Invalid password (8-72 characters).'
    except Exception as err:
        error_msg = 'Cannot save changes. Duplicate of user\'s name.'


    only_admin = '' if logged_user.is_admin else 'disabled="disabled"'
    user_path_id = '' if user_id is None else '/'+str(user.id)
    checked_admin = 'checked="checked"' if user.is_admin else ''

    yield f'''
    <form method="POST" action="/user{user_path_id}">
        <table class="content-table">
            <tr>
                <td>ID</td>
                <td>{user.id}</td>
            </tr>
            <tr>
                <td>Username</td>
                <td><input name="name" value="{escape(user.name)}"/></td>
            </tr>
            <tr>
                <td>Password</td>
                <td><input name="password" type="password" value=""/></td>
            </tr>
            <tr>
                <td><label for="is-admin-chkbsk">Is admin</label></td>
                <td><input id="is-admin-chkbsk" type="checkbox" {only_admin} {checked_admin} name="is_admin"/></td>
            </tr>
        </table>
        <p><input type="submit" name="save-changes" value="Save"/></p>
    </form>
    <p>{escape(error_msg)}</p>
    '''


def render_users():
    return render_page(render_users_table())


def render_user(user_id: Optional[int]):
    return render_page(render_user_edit(user_id))