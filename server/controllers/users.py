import models
import cherrypy
from html import escape
from typing import Optional
from controllers.common import render_page

def render_users_table():
    yield '''
    <div class="section-div userslist-div">
        <table class="content-table user-table">
            <thead>
                <tr>
                    <th>id</th>
                    <th class="main-column">Name</th>
                    <th>is admin</th>
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



def render_user_edit(user_id: Optional[int], **kwargs):
    user = models.User(name='new_user') if user_id is None else models.User(id=user_id)
    logged_id = cherrypy.session.get('user_id', None)
    if logged_id is None: raise PermissionError()
    logged_user = models.User(id=logged_id)
    if not logged_user.is_admin and logged_user.id != user.id:
        raise PermissionError()

    if logged_user.is_admin:
        yield '<p><a href="/users">Back to users list</a></p>'

    error_msg = ''
    try:
        if 'save-changes' in kwargs:
            if 'name' in kwargs:
                user.name = kwargs['name']
            if 'password' in kwargs and kwargs['password'] != '':
                user.set_password_hash(kwargs['password'])
            if 'is_admin' in kwargs and logged_user.is_admin:
                user.is_admin = True
            else:
                user.is_admin = False
            user.persist()
    except Exception as err:
        error_msg = 'Cannot save changes. Duplicate of user\'s name.'
        raise err

    only_admin = '' if logged_user.is_admin else 'disabled="disabled"'
    user_path_id = '' if user_id is None else user.id

    yield f'''
    <form method="POST" action="/user/{user_path_id}">
        <table>
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
                <td><input id="is-admin-chkbsk" type="checkbox" {only_admin} name="is_admin"/></td>
            </tr>
        </table>
        <p><input type="submit" name="save-changes" value="Save"/></p>
    </form>
    <p>{escape(error_msg)}</p>
    '''


def render_users(*args, **kwargs):
    return render_page(render_users_table())


def render_user(user_id: Optional[int], **kwargs):
    return render_page(render_user_edit(user_id, **kwargs))