import cherrypy
import mimetypes
import base64
import urllib.parse
import tempfile

from typing import Union
from dataclasses import dataclass
from functools import wraps


class CustomPart(cherrypy._cpreqbody.Part):
    """
    Custom entity part that it will alway create a named
    temporary file for the entities.
    """
    maxrambytes = 1024*1024*64

    def make_file(self):
        return tempfile.NamedTemporaryFile()

