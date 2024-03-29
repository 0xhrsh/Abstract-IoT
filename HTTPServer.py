from json.decoder import JSONDecodeError
import socket
from HTTPRequest import HTTPRequest
import threading
import mimetypes
import psycopg2
from dotenv import Dotenv
import json


blank_line = b'\r\n'
INSERT = "INSERT INTO PI (PI_ID, CONFIG_VERSION, SENSOR_PORT, SENSOR_NAME, SENSOR_DATA)\
     VALUES ('{}', {}, {}, '{}', {}) ON CONFLICT (PI_ID, SENSOR_PORT) DO NOTHING;"

UPDATE = "UPDATE PI SET CONFIG_VERSION = {}, SENSOR_NAME = '{}', SENSOR_DATA = {}\
     WHERE PI_ID = '{}' AND SENSOR_PORT = {};"
READ = "SELECT * FROM PI;"


class HTTPServer():

    headers = {
        'Server': 'RAP',
        'Content-Type': 'text/html',
    }

    status_codes = {
        200: 'OK',
        400: 'Bad Request',
        404: 'Not Found',
        501: 'Not Implemented',
    }

    def __init__(self, host='127.0.0.1', port=8888):
        creds = Dotenv('creds.env')

        db = psycopg2.connect(database="data", user=creds["USER"],
                              password=creds["PASSWORD"], host="127.0.0.1", port="5432")

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
        try:
            data = conn.recv(1024)
            request = HTTPRequest(data)
        except socket.error:
            conn.close()
            return

        response = self.handle_request(request, conn)
        conn.sendall(response)
        conn.close()
        return

    def handle_request(self, request, conn):
        try:

            handler = getattr(self, 'handle_%s' % request.method)
        except AttributeError:
            handler = self.HTTP_501_handler

        response = handler(request, conn)
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

    def handle_OPTIONS(self, request, conn):

        response_line = self.response_line(200)

        extra_headers = {'Allow': 'OPTIONS, GET, RAP'}
        response_headers = self.response_headers(extra_headers)

        blank_line = b'\r\n'

        return b''.join([response_line, response_headers, blank_line])

    def handle_GET(self, request, conn):

        path = request.uri.strip('/')  # remove slash from URI

        if not path:
            # If path is empty, that means user is at the homepage
            # so just serve index.html
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

    def handle_RAP(self, request, conn):
        conn.sendall(b"Handling RAP")
        headers = request.headers
        config_version = headers["config_version"]
        PiID = headers["PI_ID"]

        while True:
            try:
                data = conn.recv(1024)
            except socket.error:
                break

            try:
                body = json.loads(data.decode())
            except JSONDecodeError:
                break

            try:
                name = body["SENSOR_NAME"]
                port = body['SENSOR_PORT']
                data = body["SENSOR_DATA"]
            except KeyError:
                break

            cur = self.db.cursor()
            cur.execute(INSERT.format(
                PiID, config_version, port, name, data))
            cur.execute(UPDATE.format(
                config_version, name, data, PiID, port))
            self.db.commit()
            print(PiID, config_version, port, name, data)

            with open('PI/config.json') as f:
                data = json.load(f)
                print(data["version"])
                conn.sendall(str(data["version"]).encode('utf8'))

        response_line = self.response_line(status_code=400)
        response_headers = self.response_headers()
        response_body = b'Bad Request'
        response = b''.join([response_line, response_headers, blank_line, response_body])

        return response

    def serve_index(self):
        cur = self.db.cursor()
        cur.execute(READ)
        rows = cur.fetchall()
        device_list = ""
        for row in rows:
            device_list += str(row) + "<br>"

        path = 'index.html'
        response_line = self.response_line(200)
        content_type = mimetypes.guess_type(path)[0] or 'text/html'
        extra_headers = {'Content-Type': content_type}
        response_headers = self.response_headers(extra_headers)
        with open(path, 'rb') as f:

            response_body = f.read().decode('utf8')
            response_body = response_body.format(device_list=device_list)
            response_body = response_body.encode('utf8')

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

    def HTTP_501_handler(self, request, conn):

        response_line = self.response_line(status_code=501)
        response_headers = self.response_headers()
        response_body = b'<h1>501 Not Implemented</h1>'

        return b"".join([response_line, response_headers, blank_line, response_body])


if __name__ == '__main__':
    server = HTTPServer()
    server.start()
