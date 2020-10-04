#!/usr/bin/python3
import mechanize
import http.cookiejar


class Data:
    def __init__(self, address="127.0.0.1",
                 username=None, password=None,
                 max_pages=-1, port=80, output_folder=None):
        """
        :param address: the address of the target
        :param username: the user's username
        :param password: the user's password
        :param max_pages: the maximum pages amount
        :param port: the port of the target
        :param output_folder: the folder of the output files
        """
        self.address = address
        self.port = port
        self.max_pages = max_pages
        self.folder = output_folder
        self.username = username
        self.password = password
        self.pages = list()  # normal pages
        self.session_pages = list()  # session pages
        self.results = list()  # vulnerabilities results
        self.cookies = http.cookiejar.CookieJar()  # Session cookies
        self.session = mechanize.Browser()  # Session object
        self.session.set_cookiejar(self.cookies)  # Setting the cookies
