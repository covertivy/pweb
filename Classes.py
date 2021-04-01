#!/usr/bin/python3
from threading import Lock, Event
from queue import Queue
from seleniumwire import webdriver, request as selenium_request


class Manager:
    def logic(self, data):
        """
        Abstract function, every manager must have a logic function
        @type data: Classes.Data
        @param data: The data object of the program
        @return: None
        """
        pass


class Browser(webdriver.Chrome):
    def __init__(self, executable_path, options, remove_alerts=True):
        super(Browser, self).__init__(executable_path=executable_path, options=options)
        self.__remove_alerts = remove_alerts

    def dump_alerts(self, count=-1):
        """
        This function makes sure no alerts are on a page to avoid exceptions.
        @return: None.
        """
        dumped = 0
        while count == -1 or count:
            try:
                # Check for alert on page.
                alert = self.switch_to.alert
                alert.accept()
                count -= 1
                dumped += 1
            except Exception:
                # No more alerts on page.
                break
        return dumped

    def get(self, url):
        super(Browser, self).get(url)
        if self.__remove_alerts:
            self.dump_alerts()

    def refresh(self):
        self.dump_alerts()
        super(Browser, self).refresh()
        if self.__remove_alerts:
            self.dump_alerts()



class Data:
    def __init__(self):
        """
        Constructor of the Data class.
        Responsible of storing each process information.
        """
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
        self.mutex = Lock()  # Mutex
        self.all_threads_done_event = Event()  # When all the threads have finished their run
        self.results_queue = Queue(20)  # A queue for the check results

    def __str__(self):
        """
        Function makes a string of the Data instance
        @rtype: str
        @return: The object string
        """
        output_str = f"IP: {self.ip}\n" if self.ip else f"IP: Not Specified\n"
        output_str += f"PORT: {self.port}\n" if self.port else f"PORT: Not Specified\n"
        output_str += f"URL: {self.url}\n" if self.url else f"URL: Not Specified\n"
        output_str += f"MAXIMUM PAGES: {self.max_pages}\n" if self.max_pages else f"MAXIMUM PAGES: Not Specified\n"
        output_str += f"USERNAME: {self.username}\n" if self.username else f"USERNAME: Not Specified\n"
        output_str += f"PASSWORD: {self.password}\n" if self.password else f"PASSWORD: Not Specified\n"
        output_str += f"WHITELIST: {self.whitelist}\n" if self.whitelist else f"WHITELIST: Not Specified\n"
        output_str += f"BLACKLIST: {self.blacklist}\n" if self.blacklist else f"BLACKLIST: Not Specified\n"
        output_str += f"OUTPUT FOLDER: {self.output}\n" if self.output else f"OUTPUT FOLDER: Not Specified\n"
        output_str += f"COOKIES FILE: {self.cookies}\n" if self.cookies else f"COOKIES FILE: Not Specified\n"
        output_str += f"RECURSIVE: {self.recursive}\n"
        output_str += f"VERBOSE: {self.verbose}\n"
        output_str += f"AGGRESSIVE: {self.aggressive}"
        return output_str


class Page:
    def __init__(self, url, status=200, mime_type="html/text",
                 content="", request=None, cookies=None, parent=None, is_session=False):
        """
        Constructor of the Page class.
        @type url: str
        @param url: The URL of the page.
        @type status: int
        @param status: The status code of the response (200, 300, 400, etc).
        @type mime_type: str
        @param mime_type: The MIME type of the page.
        @type content: str
        @param content: The HTML content of the page.
        @type request: selenium_request.Request
        @param request: The request that fetched this page.
        @type cookies: list
        @param cookies: List of dictionaries that are cookies that the webdriver can use.
        @type parent: Page
        @param parent: The parent page of this current page, If this is the base page this will be None.
        @type is_session: bool
        @param is_session: If the page is inside of a session.
        """
        self.url = url
        self.status = status
        self.type = mime_type
        self.content = content
        self.request = request
        self.cookies = cookies
        self.parent = parent
        self.is_session = is_session

    def __str__(self):
        """
        Function makes a string of the Page instance
        @rtype: str
        @return: The object string
        """
        string = f"URL: {self.url}\n"
        if self.parent:
            string += f"PARENT URL: {self.parent.url}\n"
        string += f"STATUS: {self.status}\n" \
                  f"COOKIES: {self.cookies}\n" \
                  f"CONTENT TYPE: {self.type}\n" \
                  f"CONTENT LENGTH: {len(self.content)}"
        return string


class PageResult(Page):
    def __init__(self, page, description=""):
        """
        Constructor of the PageResult Class.
        @type page: Page
        @param page: The problematic page.
        @type description: str
        @param description: A specific message of the current page.
        """
        super(PageResult, self).__init__(page.url)
        self.description = description


class CheckResult:
    def __init__(self, problem, solution, explanation):
        """
        Constructor of the CheckResult Class.
        @type problem: str
        @param problem: String of problems that were found.
        @type solution: str
        @param solution: A solution in case of problems.
        @type explanation: str
        @param explanation: An explanation of the used algorithm.
        """
        self.problem = problem
        self.solution = solution
        self.explanation = explanation
        self.page_results = list()  # A List of `PageResult` objects.

    def add_page_result(self, page_result, separator=str()):
        """
        Function appends a new page result to the list and checks if it is already in the list.
        @type page_result: PageResult
        @param page_result: The page result the function appending.
        @type separator: str
        @param separator: Separates between the different descriptions.
        @return: None
        """
        for page in self.page_results:
            if page.url == page_result.url:
                page.description += separator + page_result.description
                return
        self.page_results.append(page_result)


class CheckResults:
    def __init__(self, headline, color):
        """
        Constructor of the CheckResults Class.
        @type headline: str
        @param headline: The name of the vulnerability.
        @type color: str
        @param color: The color of the message.
        """
        self.headline = headline
        self.color = color  # Used in the case of printing to the screen.
        self.results = list()  # A List of `CheckResult` objects.
        self.conclusion = str()
        self.error = str()
        self.warning = str()
        self.success = str()
