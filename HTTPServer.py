import socket
from HTTPRequest import HTTPRequest
import threading
import mimetypes
import psycopg2
# import os
# import requests

# to download file over a request (e.g. init.sh)
# import urllib.request
# import shutil
blank_line = b'\r\n'
INSERT = "INSERT INTO PI (PI_ID, CONFIG_VERSION, OBJ_DETECTED) VALUES ('{}', {}, {}) \
    ON CONFLICT (PI_ID) DO NOTHING;"
UPDATE = "UPDATE PI SET CONFIG_VERSION = {}, OBJ_DETECTED = {} WHERE PI_ID = '{}';"


class HTTPServer():

    headers = {
        'Server': 'RAP',
        'Content-Type': 'text/html',
    }

    status_codes = {
        200: 'OK',
        404: 'Not Found',
        501: 'Not Implemented',
    }

    def __init__(self, host='127.0.0.1', port=8888):
        db = psycopg2.connect(database="data", user="rap",
                              password="rap@iitj", host="127.0.0.1", port="5432")
        # todo: take username password from .env file
        self.host = host
        self.port = port
        self.db = db

    def start(self):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)

        print("Listening at", s.getsockname())

        threads = []

        try:
            while True:
                conn, addr = s.accept()
                print("Connected by", addr)

                t = threading.Thread(
                    target=self.handle_single_connection, args=(conn,), daemon=True)
                t.start()
                threads.append(conn)

        except KeyboardInterrupt:
            s.close()
            for conn in threads:
                conn.close()
            return

    def handle_single_connection(self, conn):
        while True:
            try:
                data = conn.recv(1024)
                request = HTTPRequest(data)
            except socket.error:
                conn.close()
                break

            response = self.handle_request(request)
            conn.sendall(response)

            if request.method == "GET":
                conn.close()

    def handle_request(self, request):
        try:

            handler = getattr(self, 'handle_%s' % request.method)
        except AttributeError:
            handler = self.HTTP_501_handler

        response = handler(request)
        return response

    def response_line(self, status_code):
        reason = self.status_codes[status_code]
        response_line = 'HTTP/1.1 %s %s\r\n' % (status_code, reason)

        return response_line.encode()  # convert from str to bytes

    def response_headers(self, extra_headers=None):

        headers_copy = self.headers.copy()  # make a local copy of headers

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ''

        for h in headers_copy:
            headers += '%s: %s\r\n' % (h, headers_copy[h])

        return headers.encode()  # convert str to bytes

    def handle_OPTIONS(self, request):
        """Handler for OPTIONS HTTP method"""

        response_line = self.response_line(200)

        extra_headers = {'Allow': 'OPTIONS, GET, PUT'}
        response_headers = self.response_headers(extra_headers)

        blank_line = b'\r\n'

        return b''.join([response_line, response_headers, blank_line])

    def handle_GET(self, request):

        path = request.uri.strip('/')  # remove slash from URI

        if not path:
            # If path is empty, that means user is at the homepage
            # so just serve index.html
            print(request)
            return self.serve_index()

        elif path.split('/')[0] == "init":
            return self.serve_init(request)

        elif path.split('/')[0] == "config":
            return self.serve_config(request)

        else:
            response_line = self.response_line(404)
            response_headers = self.response_headers()
            response_body = b'<h1>404 Not Found</h1>'

            response = b''.join([response_line, response_headers, blank_line, response_body])

            return response

    def handle_PUT(self, request):
        headers = request.headers
        config_version = headers["config_version"]
        PiID = headers["PI_ID"]
        data = request.body["data"]

        cur = self.db.cursor()
        cur.execute(INSERT.format(
            PiID, config_version, data))
        cur.execute(UPDATE.format(
            config_version, data, PiID))
        self.db.commit()

        return

    def serve_index(self):
        path = 'index.html'
        response_line = self.response_line(200)
        content_type = mimetypes.guess_type(path)[0] or 'text/html'
        extra_headers = {'Content-Type': content_type}
        response_headers = self.response_headers(extra_headers)
        with open(path, 'rb') as f:
            response_body = f.read()

        response = b''.join([response_line, response_headers, blank_line, response_body])

        return response

    def serve_init(self, request):
        path = 'PI/init.sh'
        response_line = self.response_line(200)
        content_type = mimetypes.guess_type(path)[0] or 'text/html'
        extra_headers = {'Content-Type': content_type}
        response_headers = self.response_headers(extra_headers)

        with open(path, 'rb') as f:
            response_body = f.read()

        response = b''.join([response_line, response_headers, blank_line, response_body])

        return response

    def serve_config(self, request):
        path = 'PI/config.json'
        with open(path, 'rb') as f:
            response_body = f.read()
        response_line = self.response_line(200)
        content_type = mimetypes.guess_type(path)[0] or 'application/json'
        extra_headers = {'Content-Type': content_type}
        response_headers = self.response_headers(extra_headers)

        response = b''.join([response_line, response_headers, blank_line, response_body])

        return response

    def HTTP_501_handler(self, request):

        response_line = self.response_line(status_code=501)
        response_headers = self.response_headers()

        blank_line = b'\r\n'

        response_body = b'<h1>501 Not Implemented</h1>'

        return b"".join([response_line, response_headers, blank_line, response_body])


if __name__ == '__main__':
    server = HTTPServer()
    server.start()
