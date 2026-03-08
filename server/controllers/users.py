import flask
import models
from html import escape
from typing import Optional
from controllers.common import render_page


def render_users_table():
    logged_id = flask.session.get('user_id', None)
    if logged_id is None: raise PermissionError()
    logged_user = models.User(id=logged_id)
    if not logged_user.is_admin: raise PermissionError()

    if flask.request.method == 'POST' and 'confirm-delete' in flask.request.form and 'user-delete-id' in flask.request.form and 'delete-btn' in flask.request.form:
        try:
            delete_user_id = int(flask.request.form['user-delete-id'])
            delete_user = models.User(id=delete_user_id)
            if not delete_user.exists(): raise ValueError()
            delete_user.delete()
        except ValueError:
            yield '<p>Incorrect user id or the user had been deleted.</p>'

    yield '''
    <div class="section-div userslist-div">
        <table id="users-table" class="content-table dynamic-table user-table">
            <thead>
                <tr>
                    <th class="dynamic">id</th>
                    <th class="main-column dynamic last-on-mobile">Name</th>
                    <th class="dynamic only-pc">show in share list</th>
                    <th class="dynamic only-pc">active</th>
                    <th class="dynamic only-pc">is admin</th>
                </tr>
            </thead>
            <tbody>
    '''

    for user in models.User.query().get():
        yield f'''
            <tr>
                <td>{user.id}</td>
                <td class="main-column last-on-mobile"><a href="/user/{user.id}">{escape(user.name)}</a></td>
                <td class="only-pc">{user.show_in_share_list}</td>
                <td class="only-pc">{user.active}</td>
                <td class="only-pc">{user.is_admin}</td>
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
            user.show_in_share_list = 'show_in_share_list' in flask.request.form
            if logged_user.is_admin:
                user.is_admin = 'is_admin' in flask.request.form
                user.active = 'active' in flask.request.form
            user.persist()
    except ValueError as err:
        error_msg = 'Cannot save changes. Invalid password (8-72 characters).'
    except Exception as err:
        error_msg = 'Cannot save changes. Duplicate of user\'s name.'


    only_admin = '' if logged_user.is_admin else 'disabled="disabled"'
    user_path_id = '' if user_id is None else '/'+str(user.id)
    checked_admin = 'checked="checked"' if user.is_admin else ''
    checked_show_in_share_list = 'checked="checked"' if user.show_in_share_list else ''
    checked_active = 'checked="checked"' if user.active else ''

    yield f'''
    <div class="user-edit" style="width: max-content;">
        <form method="POST" action="/user{user_path_id}">
            <table class="content-table">
                <tr class="header">
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
                    <td><label for="show-in-share-list-chkbsk">Show in share list</label></td>
                    <td><input id="show-in-share-list-chkbsk" type="checkbox" {checked_show_in_share_list} name="show_in_share_list"/></td>
                </tr>
                <tr>
                    <td><label for="active-chkbsk">Active</label></td>
                    <td><input id="active-chkbsk" type="checkbox" {checked_active} name="active"/></td>
                </tr>
                <tr>
                    <td><label for="is-admin-chkbsk">Is admin</label></td>
                    <td><input id="is-admin-chkbsk" type="checkbox" {only_admin} {checked_admin} name="is_admin"/></td>
                </tr>
            </table>
            <p><input type="submit" name="save-changes" value="Save"/></p>
        </form>
    </div>
    <p>{escape(error_msg)}</p>
    '''

    if user.id is not None and logged_user.is_admin:
        yield f'''
        <form action="/users" method="POST">
            <input type="checkbox" id="confirm-delete" name="confirm-delete" required/>
            <label for="confirm-delete">Confirm delete</label>
            <br/>
            <input type="hidden" name="user-delete-id" value="{user.id}"/>
            <input type="submit" name="delete-btn" value="Delete"/>
        </form>
        '''


def render_users():
    return render_page(render_users_table())


def render_user(user_id: Optional[int]):
    return render_page(render_user_edit(user_id))