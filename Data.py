import mechanize
import http.cookiejar


class Data:
    def __init__(self, url, username="", password="", pages=-1):
        self.address = url
        self.port = 80
        self.max_pages = pages
        self.pages = list()
        self.session_pages = list()
        self.folder = ""
        self.username = username
        self.password = password
        self.results = list()
        cookies = http.cookiejar.CookieJar()
        self.session = mechanize.Browser()
        self.session.set_cookiejar(cookies)
        self.session.open(self.address)
