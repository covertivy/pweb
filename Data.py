#!/usr/bin/python3
from threading import Lock
import requests


class Data:
    def __init__(self):
        self.ip = None
        self.url = None
        self.port = None
        self.max_pages = None
        self.output = None
        self.username = None
        self.password = None
        self.recursive = False
        self.verbose = True
        self.blacklist = None
        self.whitelist = None
        self.agreement = False
        self.pages = list()  # Pages
        self.results = list()  # Vulnerabilities results
        self.mutex = Lock()  # Mutex

    def __str__(self):
        output_str = ""
        if self.ip is None:
            output_str += f"IP: Not Specified.\n"
        else:
            output_str += f"IP: {self.ip}\n"
        if self.ip is None:
            output_str += f"PORT: Not Specified.\n"
        else:
            output_str += f"PORT: {self.port}\n"
        if self.url is None:
            output_str += f"URL: Not Specified.\n"
        else:
            output_str += f"URL: {self.url}\n"
        if self.max_pages is None:
            output_str += f"MAXIMUM PAGES: Unlimited.\n"
        else:
            output_str += f"MAXIMUM PAGES: {self.max_pages}\n"
        if self.output is None:
            output_str += f"OUTPUT FILE: Not Specified.\n"
        else:
            output_str += f"OUTPUT FILE: {self.output}\n"            
        if self.username is None:
            output_str += f"USERNAME: Not Specified.\n"
        else:
            output_str += f"USERNAME: {self.username}\n"
        if self.password is None:
            output_str += f"PASSWORD: Not Specified.\n"
        else:
            output_str += f"PASSWORD: {self.password}\n"
        if self.blacklist is None:
            f"BLACKLIST: Not Specified.\n"
        else:
            f"BLACKLIST: {self.blacklist}\n"
        f self.whitelist is None:
            f"WHITELIST: Not Specified.\n"
        else:
            f"WHITELIST: {self.whitelist}\n"
        output_str += f"RECURSIVE: {self.recursive}\n"  
        output_str += f"VERBOSE: {self.verbose}\n"
        output_str += f"AGREEMENT: {self.agreement}\n"

        return output_str


class Page:
    def __init__(
        self, url: str, status: int, mime_type: str, content: str, response: requests.Response, parent
    ):
        self.url = url
        self.status = status
        self.type = mime_type
        self.content = content
        self.http_response = response
        self.parent = parent

    def __str__(self):
        return (
            f"URL: {self.url}\n"
            f"STATUS: {self.status}\n"
            f"CONTENT-TYPE: {self.type}\n"
            f"CONTENT: {self.content}\n"
            f"PARENT URL: {self.parent.url}\n"
        )


class SessionPage(Page):
    def __init__(
        self,
        url: str,
        status: int,
        mime_type: str,
        content: str,
        cookies,
        login: set,
        response: requests.Response,
        parent,
    ):
        super(SessionPage, self).__init__(url, status, mime_type, content, response, parent)
        self.cookies = cookies
        self.login = login  # The page which the session started from


class PageResult(Page):
    def __init__(self, page: Page, problem: str, solution: str):
        super(PageResult, self).__init__(
            page.url, page.status, page.type, page.content, page.http_response, page.parent
        )
        self.problem = problem  # String of problems that were found
        self.solution = solution  # A solution in case of problems


class CheckResults:
    def __init__(self, headline: str, color: str):
        self.headline = headline  # The name of the plugin (xss, rfi, etc..)
        self.color = color  # In case of printing to the screen
        self.page_results = list()  # List of page results
