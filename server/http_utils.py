import cherrypy
from typing import Never, Optional, Any


def get_session():
    return cherrypy.session


def redirect(url: str) -> Never:
    raise cherrypy.HTTPRedirect(url)


def error(code: int, reason: Optional[str] = None) -> Never:
    raise cherrypy.HTTPError(code, reason)


def enable_custom_content_type():
    headers = cherrypy.response.headers
    original_encode = headers.encode
    def new_encode(*args, **kwargs):
        if 'Custom-Content-Type' in headers:
            headers['Content-Type'] = headers['Custom-Content-Type']
            headers.pop('Custom-Content-Type')
        return original_encode(*args, **kwargs)
    headers.encode = new_encode


def enable_stream():
    cherrypy.response.stream = True


def get_request_header(header: str, default: Any) -> Any:
    return cherrypy.request.headers.get(header, default)


def set_response_header(header: str, value: Optional[str]) -> None:
    if value is None:
        if header in cherrypy.response.headers:
            cherrypy.response.headers.pop(value)
    else:
        cherrypy.response.headers[header] = value


def set_status_code(code: int):
    cherrypy.response.status = code


def get_request_method() -> str:
    return cherrypy.request.method

