import flask
import liteorm
import logging
import traceback
from functools import wraps
from itertools import chain
from dataclasses import dataclass
from typing import Iterator, Union, Any, Optional


logger = logging.getLogger(__name__)


class HTTPRedirect(Exception):
    def __init__(self, url: str):
        super().__init__()
        self.url = url


class HTTPError(Exception):
    def __init__(self, code: int, reason: Optional[str]):
        super().__init__()
        self.code = code
        self.reason = reason


@dataclass
class ResponseHeader:
    name: str
    value: Any


@dataclass
class ResponseCode:
    code: int


ResponseStreamValue = Union[str, bytes, ResponseHeader, ResponseCode, None]
ResponseStream = Iterator[ResponseStreamValue]


def to_bytes(value: ResponseStreamValue) -> bytes:
    if isinstance(value, bytes):
        return value    
    if isinstance(value, str):
        return value.encode('utf-8')
    assert False




def consume_response(rs: ResponseStream) -> flask.Response:
    response = flask.Response()
    try:
        while True:
            value = next(rs)
            if isinstance(value, ResponseHeader):
                response.headers[value.name] = str(value.value)
            elif isinstance(value, ResponseCode):
                response.status_code = value.code
            elif isinstance(value, Exception):
                raise value
            elif isinstance(value, (bytes, str)):
                response.response = map(to_bytes, chain([value], rs))
                break
        return response
    except StopIteration:
        return response
    except HTTPRedirect as r:
        response = flask.Response(status=303)
        response.headers['Location'] = r.url
        return response
    except HTTPError as e:
        response.status_code = e.code
        response.response = e.reason if e.reason is not None else ''
        logger.error(repr(e)+"\n" +traceback.format_exc())
        return response
    except PermissionError:
        logger.error(traceback.format_exc())
        return flask.Response(status=403, response='Forbidden')
    except FileNotFoundError:
        logger.error(traceback.format_exc())
        return flask.Response(status=404, response='Not found')
    except liteorm.RecordNotFound:
        logger.error(traceback.format_exc())
        return flask.Response(status=404, response='Not found')
    except Exception as err:
        logger.error(traceback.format_exc())
        return flask.Response(status=500, response='')

        
def http_response(fun):

    @wraps(fun)
    @flask.stream_with_context
    def decorator(*args, **kwargs):
        def generator():
            yield None
            for v in fun(*args, **kwargs): yield v
        return consume_response(generator())
        
    return decorator
