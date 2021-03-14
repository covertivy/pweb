#!/usr/bin/python3
from threading import Lock
from queue import Queue
from seleniumwire import request as selenium_request


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
        self.aggressive = False
        self.cookies = None
        self.driver = None
        self.pages = list()  # The pages that were gathered from the website using PageManager.
        self.results = list()  # Results that were harvested by the plugins.
        self.mutex = Lock()  # Mutex
        # A queue for plugin printing tasks (useful for debugging or simple output).
        # Each value in the queue is a tuple containing the origin and the data to print (origin: str, data: str).
        self.print_queue = Queue(20) 

    def __str__(self):
        output_str = ""
        output_str += f"IP: {self.ip}\n" if self.ip else f"IP: Not Specified\n"
        output_str += f"PORT: {self.port}\n" if self.port else f"PORT: Not Specified\n"
        output_str += f"URL: {self.url}\n" if self.url else f"URL: Not Specified\n"
        output_str += f"MAXIMUM PAGES: {self.max_pages}\n" if self.max_pages else f"MAXIMUM PAGES: Not Specified\n"
        output_str += f"USERNAME: {self.username}\n" if self.username else f"USERNAME: Not Specified\n"
        output_str += f"PASSWORD: {self.password}\n" if self.password else f"PASSWORD: Not Specified\n"
        output_str += f"WHITELIST: {self.whitelist}\n" if self.whitelist else f"WHITELIST: Not Specified\n"
        output_str += f"BLACKLIST: {self.blacklist}\n" if self.blacklist else f"BLACKLIST: Not Specified\n"
        output_str += f"OUTPUT FILE: {self.output}\n" if self.output else f"OUTPUT FILE: Not Specified\n"
        output_str += f"COOKIES FILE: {self.cookies}\n" if self.cookies else f"COOKIES FILE: Not Specified\n"
        output_str += f"RECURSIVE: {self.recursive}\n"
        output_str += f"VERBOSE: {self.verbose}\n"
        output_str += f"AGGRESSIVE: {self.aggressive}"
        return output_str


class Page:
    def __init__(self, url: str, status: int, mime_type: str,
                 content: str, request: selenium_request, cookies: list, parent):
        self.url = url  # The URL of the page.
        self.status = status  # The status code of the response (200, 300, 400, etc).
        self.type = mime_type  # The MIME type of the page.
        self.content = content  # The HTML content of the page.
        self.request = request  # The request that fetched this page.
        self.cookies = cookies  # List of dictionaries that are cookies that the webdriver can use.
        self.parent = parent  # The parent page of this current page, If this is the base page this will be None.

    def __str__(self):
        return (
            f"URL: {self.url}\n"
            f"PARENT URL: {self.parent.url}\n"
            f"STATUS: {self.status}\n"
            f"COOKIES: {self.cookies}\n"
            f"CONTENT TYPE: {self.type}\n"
            f"CONTENT LENGTH: {len(self.content)}\n"
            f"CONTENT: {self.content}\n")


class SessionPage(Page):
    def __init__(self, url: str, status: int, mime_type: str,
                 content: str, cookies: list, login: set, request: selenium_request, parent):
        super(SessionPage, self).__init__(url, status, mime_type, content, request, cookies, parent)
        self.login = login  # A Set containing information about the session (The page which the session started from, It's Login form).


class PageResult(Page):
    def __init__(self, page: Page, problem: str, solution: str, text_chunk: str = None):
        super(PageResult, self).__init__(page.url, page.status, page.type,
                                         page.content, page.request, list(), page.parent)
        self.problem = problem  # String of problems that were found.
        self.solution = solution  # A solution in case of problems.
        self.text_chunk = text_chunk # If this is initialized the problem and solution will not be printed and instead this will be shown.


class CheckResults:
    def __init__(self, headline: str, color: str):
        self.headline = headline  # The name of the plugin (xss, rfi, etc..).
        self.color = color  # Used in the case of printing to the screen.
        self.page_results = list()  # A List of `PageResult` objects.
