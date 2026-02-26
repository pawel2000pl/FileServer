import os
import flask
import base64
import models
import response_stream
from html import escape
from urllib.parse import quote
from typing import Optional, Iterator
from controllers.common import render_page
from libraries.storage import StorageEntry
from configuration import MINIMUM_TOKEN_LENGTH


def render_shared_table(only_shared_with_me: bool, require_depends_on: bool, only_shared_by_me: bool, only_id: Optional[int] = None) -> Iterator[str]:
    user_id = flask.session.get('user_id')
    if user_id is None: raise PermissionError()
    user = models.User(id=user_id)
    if not only_shared_with_me and not only_shared_by_me and not user.is_admin: raise PermissionError()
    query = models.Capability.query()
    if only_shared_with_me:
        query.where('user', user)
    if only_shared_by_me:
        query.where_in_query('depends_on', models.Capability.query().where('user', user))
    if only_id is not None:
        query.where('id', only_id)
    if require_depends_on:
        query.where_not_null('depends_on')

    yield '''
    <p class="share-manual">
        You can copy an access link to every share by clicking on "Name" or "Shared with user / token" column with the right mouse button and using the "Copy link" option.
    </p>
    '''

    yield '''
    <div class="section-div sharedlist-div">
        <table id="shares-table" class="content-table dynamic-table shared-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th class="dynamic">Name</th>
                    <th class="dynamic">Shared by</th>
                    <th class="dynamic">Shared with user / token</th>
                    <th class="dynamic">Share method</th>
                    <th class="dynamic">Write</th>
                </tr>
            </thead>
            <tbody>
    '''

    for capability in query.get():
        shared_by = '' if capability.depends_on is None else capability.depends_on.user.name
        shared_method: str
        shared_with: str
        url = ''
        if capability.token is None:
            shared_method = 'for user'
            shared_with = capability.user.name
            url = '/userfile/'+quote(shared_with)+'/'+quote(capability.name)
        else:
            shared_method = 'token'
            shared_with = capability.token
            url = '/tokenfile/'+quote(shared_with)
        if capability.name is None: capability.name = 'Unnamed'
        yield f'''
            <tr>
                <td><input type="checkbox" name="share[]" value="{capability.id}"</td>
                <td><a href="{escape(url)}">{escape(capability.name)}</a></td>
                <td>{escape(shared_by)}</td>
                <td><a href="{escape(url)}">{escape(shared_with)}</a></td>
                <td>{shared_method}</td>
                <td>{capability.write}</td>
            </tr>
        '''

    yield '''
            </tbody>
        </table>
    </div>
    '''


def render_create_share_for(storage_entry: StorageEntry) -> Iterator[str]:
    user_id = flask.session.get('user_id', None)
    if not storage_entry.can_be_shared() or user_id is None:
        return
    user = models.User(id=user_id)
    write_disabled = '' if storage_entry.write else 'disabled="disabled" style="display: hidden;"'
    storage_path = storage_entry.get_storage_path()
    splitted_path = storage_path.split('/')
    allowed_paths = ['/'.join(splitted_path[:i+1]) for i in range(len(splitted_path))]
    capability = models.Capability.query().where('user', user).where_in('storage_path', allowed_paths).order('write', 'DESC').get_one()
    assert capability is not None
    entry_name = storage_entry.get_name() if storage_entry.has_name() else 'Unnamed'
    rest_of_path = storage_path[len(capability.storage_path)+1:]
    users_on_list = models.User.query().where('show_in_share_list').where_not('id', user_id).get()
    yield '<datalist id="users-datalist">'
    for s_user in users_on_list:
        yield f'<option value="{escape(s_user.name)}">'
    yield '</datalist>'
    yield f'''
    <span onclick="share_panel.showModal()" class="share-button">Share</span>
    <dialog id="share_panel" class="share-panel">
        <form action="/create_share" method="post">
            <span class="close-share-btn" onclick="share_panel.close()">Close</span>
            <p>
                <span>Share name</span><br>
                <input name="share-name" value="{escape(entry_name)}"/>
            </p>
            <p>
                <span>Username</span><br>
                <input name="username" list="users-datalist" placeholder="ignore for token"/>
            </p>
            <p>
                <input id="share_with_writing" type="checkbox" {write_disabled}/>
                <label for="share_with_writing" {write_disabled}>Allow for writing</label>
            </p>
            <input type="hidden" name="referer" value="{escape(storage_entry.generate_url())}"/>
            <input type="hidden" name="capability_id" value="{capability.id}"/>
            <input type="hidden" name="rest_of_path" value="{escape(rest_of_path)}"/>
            <input type="submit" name="share_user" value="Share with user"/>
            <input type="submit" name="share_token" value="Share with token"/>
        </form>
    </dialog>
    '''


def create_share() -> Iterator[str]:
    user_id = flask.session.get('user_id', None)
    if user_id is None:
        raise PermissionError()
    try:
        user = models.User(id=user_id)
        referer = flask.request.form['referer']
        rest_of_path = flask.request.form['rest_of_path']
        for part in rest_of_path.split(os.sep):
            if len({'/', '\\', '~', ':'}.intersection(part)): raise PermissionError()
            if part in {'..', '.', '~'}: raise PermissionError()
        capability_id = int(flask.request.form['capability_id'])
        username = flask.request.form.get('username', '')
        share_name = flask.request.form.get('share-name', '')
        share_with_writing = bool(flask.request.form.get('share_with_writing', False))
        share_user = flask.request.form.get('share_user', False)
        share_token = flask.request.form.get('share_token', False)
        if share_token == share_user: raise ValueError()

        return_a = f'<a href="{escape(referer)}">Back</a>'

        capability = models.Capability(id=capability_id)
        if capability.user.id != user.id: raise PermissionError()
        if not capability.write and share_with_writing: raise PermissionError()

        user2 = models.User.query().where('name', username).get_one()
        if share_user and user2 is None:
            yield '<p>User not found</p>'
            yield return_a
            return

        new_capability = models.Capability()
        new_capability.storage_path = os.sep.join([capability.storage_path, rest_of_path])
        new_capability.depends_on = capability
        new_capability.write = share_with_writing
        new_capability.name = share_name if len(share_name) else  new_capability.storage_path.split(os.sep)[-1]
        if share_user:
            assert user2 is not None
            new_capability.user = user2
        if share_token:
            buflen = MINIMUM_TOKEN_LENGTH
            rand = open('/dev/urandom', 'rb')
            while buflen < 64:
                token_str = base64.b64encode(rand.read(buflen)).decode('utf-8').replace('/', '').replace('+', '').replace('=', '')
                if len(token_str) >= MINIMUM_TOKEN_LENGTH and models.Capability.query().where('token', token_str).get_one() is None:
                    new_capability.token = token_str
                    break
                buflen += 1

        similar = new_capability.find_similar()
        if similar is None:
            new_capability.persist()
        else:
            new_capability = similar
            yield '<p>This share has already exist</p>'

        for s in render_shared_table(False, False, True, new_capability.id):
            yield s
        yield return_a

    except (ValueError, KeyError):
        raise response_stream.HTTPError(400, 'Bad request')


def render_create_share() -> Iterator[str]:
    return render_page(create_share())


def render_shares(only_shared_with_me: bool, require_depends_on: bool, only_shared_by_me: bool) -> Iterator[str]:
    return render_page(render_shared_table(only_shared_with_me, require_depends_on, only_shared_by_me))

