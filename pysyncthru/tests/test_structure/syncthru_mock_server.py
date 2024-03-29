import os
import urllib.parse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, HTTPServer
import posixpath
from pathlib import Path
from socket import socket
from typing import Optional, Tuple, Union

SERVER_DIR = (Path(__file__).parent or Path(".")) / "state1"


class SyncThruServer(HTTPServer):
    blocked = False
    server_dir = SERVER_DIR

    def set_blocked(self) -> None:
        self.blocked = True

    def unset_blocked(self) -> None:
        self.blocked = False


class SyncThruRequestHandler(SimpleHTTPRequestHandler):
    def __init__(
        self,
        request: Union[socket, Tuple[bytes, socket]],
        client_address: Tuple[str, int],
        server: SyncThruServer,
    ) -> None:
        self.server = server  # type: SyncThruServer
        super().__init__(request, client_address, server)

    def do_GET(self) -> None:
        if self.server.blocked:
            self.send_error(403, "Access denied because server blocked")
        else:
            super(SyncThruRequestHandler, self).do_GET()

    def translate_path(self, path: str) -> str:
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        only slightly changed method of the standard library
        """
        # abandon query parameters
        path = path.split("?", 1)[0]
        path = path.split("#", 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith("/")
        try:
            path = urllib.parse.unquote(path, errors="surrogatepass")
        except UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        path = posixpath.normpath(path)
        words = filter(None, path.split("/"))
        path = str(self.server.server_dir.absolute())
        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += "/"
        return path

    def send_error(
        self, code: int, message: Optional[str] = None, explain: Optional[str] = None
    ) -> None:
        """
        Send syncthru error page
        :param code:
        :param message:
        :param explain:
        :return:
        """
        self.log_error("code %d, message %s", code, message)
        self.send_response(code, message)
        self.send_header("Connection", "close")

        # Message body is omitted for cases described in:
        #  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
        #  - RFC7231: 6.3.6. 205(Reset Content)
        body = None
        if code >= 200 and code not in (
            HTTPStatus.NO_CONTENT,
            HTTPStatus.RESET_CONTENT,
            HTTPStatus.NOT_MODIFIED,
        ):
            # HTML encode to prevent Cross Site Scripting attacks
            # (see bug #1100201)
            # Specialized error method for fronius
            with self.server.server_dir.joinpath(".error.html").open("rb") as file:
                body = file.read()
            self.send_header("Content-Type", self.error_content_type)
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        if self.command != "HEAD" and body:
            self.wfile.write(body)
