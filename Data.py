#!/usr/bin/python3
import mechanize
import http.cookiejar


class Data:
    def __init__(self, url="127.0.0.1",
                 username=None, password=None,
                 max_pages=-1, port=80, folder=None):
        self.address = url
        self.port = port
        self.max_pages = max_pages
        self.folder = folder
        self.username = username
        self.password = password
        self.pages = list()
        self.session_pages = list()
        self.results = list()
        cookies = http.cookiejar.CookieJar()
        self.session = mechanize.Browser()
        self.session.set_cookiejar(cookies)
        self.session.open(self.address)
