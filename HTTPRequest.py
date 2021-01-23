import json


class HTTPRequest:

    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = '1.1'
        self.headers = {}
        self.body = {}

        # call self.parse method to parse the request data
        self.parse(data)

    def parse(self, data):
        lines = data.split(b'\r\n')

        request_line = lines[0]  # request line is the first line of the data
        # request_headers = lines[6]
        request_headers = lines[6:-2]

        self.body = json.loads(lines[-1].decode())

        for header in request_headers:
            dheader = header.decode()
            self.headers[dheader.split(": ")[0]] = dheader.split(": ")[1]

        # split request line into seperate words
        words = request_line.split(b' ')

        # call decode to convert bytes to string
        self.method = words[0].decode()
        # self.headers = request_headers.decode()

        if len(words) > 1:
            # we put this in if block because sometimes browsers
            # don't send URI with the request for homepage
            # call decode to convert bytes to string
            self.uri = words[1].decode()

        if len(words) > 2:
            # we put this in if block because sometimes browsers
            # don't send HTTP version
            self.http_version = words[2]
