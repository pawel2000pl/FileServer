import models
import cherrypy
from html import escape
from urllib.parse import quote
from controllers.common import render_page


def render_shared_table(only_shared_with_me: bool, only_shared_by_me: bool):
    user_id = cherrypy.session.get('user_id')
    if user_id is None: raise PermissionError()
    user = models.User(id=user_id)
    if not only_shared_with_me and not only_shared_by_me and not user.is_admin: raise PermissionError()
    query = models.Capability.query()
    if only_shared_with_me:
        query.where('user', user)
    if only_shared_by_me:
        query.where_in_query('depends_on', models.Capability.query().where('user', user))

    yield '''
    <div class="section-div sharedlist-div">
        <table class="content-table shared-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Shared by</th>
                    <th>Shared with user / token</th>
                    <th>Share method</th>
                    <th>Write</th>
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
            
        yield f'''
            <tr>
                <td><input type="checkbox" name="share[]" value="{capability.id}"</td>
                <td><a href="{escape(url)}">{escape(capability.name)}</a></td>
                <td>{escape(shared_by)}</td>
                <td>{escape(shared_with)}</td>
                <td>{shared_method}</td>
                <td>{capability.write}</td>
            </tr>
        '''

    yield '''
            </tbody>
        </table>
    </div>
    '''


def render_shares(only_shared_with_me: bool, only_shared_by_me: bool, **kwargs):
    return render_page(render_shared_table(only_shared_with_me, only_shared_by_me))

