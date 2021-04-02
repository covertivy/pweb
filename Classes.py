#!/usr/bin/python3
from threading import Lock, Event
from queue import Queue
from seleniumwire import webdriver, request as selenium_request


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
        self.mutex = Lock()  # Mutex.
        self.all_threads_done_event = Event()  # Event indicating when all the threads have finished their run.
        self.results_queue = Queue(20)  # A queue for the check results.

    def __str__(self):
        """
        Function makes a string representation of the Data instance.
        
        @return: The object string.
        @rtype: str
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
    def __init__(self, url: str, status: int = 200, mime_type: str = "html/text",
                 content: str = "", request: selenium_request.Request = None,
                 cookies: list = None, parent=None, is_session: bool = False):
        """
        Constructor of the Page class.

        @param url: The URL of the page.
        @type url: str
        @param status: The status code of the response (200, 300, 400, etc).
        @type status: int
        @param mime_type: The MIME type of the page.
        @type mime_type: str
        @param content: The HTML content of the page.
        @type content: str
        @param request: The request that fetched this page.
        @type request: selenium_request.Request
        @param cookies: List of dictionaries that represent cookies that the webdriver can use.
        @type cookies: list
        @param parent: The parent page of this current page, If has no parent this will be None.
        @type parent: Page
        @param is_session: If the page requires a session.
        @type is_session: bool
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

        @return: The string representation of the page object.
        @rtype: str
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
    def __init__(self, page: Page, description: str = ""):
        """
        Constructor of the PageResult Class.
        This is the simplest result class,
        this will usually be appended to the `page_results` list within the `CheckResult` class.

        @param page: The problematic page that yielded a result.
        @type page: Page
        @param description: A description of the problem on the current page.
        @type description: str
        """
        super(PageResult, self).__init__(page.url)
        self.description = description


class CheckResult:
    def __init__(self, problem: str, solution: str, explanation: str):
        """
        Constructor of the CheckResult Class.
        Would usually be used to specify a sub-problem of a CheckResults object.
        
        @param problem: Description of the problem that was found.
        @type problem: str
        @param solution: A solution in case of problems.
        @type solution: str
        @param explanation: An explanation of the algorithm that was used in order to find this problem.
        @type explanation: str
        """
        self.problem = problem
        self.solution = solution
        self.explanation = explanation
        self.page_results = list()  # A List of `PageResult` objects.

    def add_page_result(self, page_result: PageResult, separator: str = ""):
        """
        This function appends a new page result to the list and checks if it is already in the list.

        @param page_result: The page result to be appended to our `page_results` list.
        @type page_result: PageResult
        @param separator: Specify a separator which would be used to separate between the different descriptions.
        @type separator: str
        @return: None.
        """
        for page in self.page_results:
            if page.url == page_result.url:
                page.description += separator + page_result.description
                return
        self.page_results.append(page_result)


class CheckResults:
    def __init__(self, headline: str, color: str):
        """
        Constructor of the CheckResults Class.

        @param headline: The name of the vulnerability (Will be used in output folder as well).
        @type headline: str
        @param color: The color of the message.
        @type color: str
        """
        self.headline = headline
        self.color = color  # Used in the case of printing to the screen.
        self.results = list()  # A List of `CheckResult` objects.
        self.conclusion = str()
        self.error = str()
        self.warning = str()
        self.success = str()


class Manager:
    def logic(self, data: Data):
        """
        Abstract function, every manager must override this logic function.
        
        @param data: The data object of the program.
        @type data: Classes.Data
        @return: None
        """
        pass


class Browser(webdriver.Chrome):
    def __init__(self, executable_path: str, options: webdriver.ChromeOptions, remove_alerts: bool = True):
        """
        This class is a subclass of the webdriver.Chrome class,
        it was created to allow alert removal with ease to avoid errors.

        @param executable_path: The path of the browser executable.
        @type executable_path: str
        @param options: Options to be passed to the webdriver.
        @type options: webdriver.ChromeOptions
        @param remove_alerts: This boolean indicates whether or not
        we should dump all alerts on `get` and `refresh` methods.
        @type remove_alerts: bool
        @return: None
        """
        super(Browser, self).__init__(executable_path=executable_path, options=options)
        self.__remove_alerts = remove_alerts

    def dump_alerts(self, count: int = -1):
        """
        This function clears alerts on a given browser.
        This is used to avoid unexpected exceptions when getting a page or to 
        reach a specific alert after a given amount of previous alerts.

        @param count: This specifies how many alerts we should remove from the current session, defaults to -1
        (any number that is not positive will result in the removal of all alerts from the current page).
        @type count: int
        @return: The amount of exceptions successfully dumped.
        @rtype: int
        """
        dumped = 0
        while count:
            try:
                # Check for alert on page.
                alert = self.switch_to.alert
                alert.accept()  # Clear current alert.
                count -= 1
                dumped += 1
            except Exception:
                # No more alerts on page.
                break
        return dumped

    def get(self, url: str):
        """
        This function overrides the default get() method of the Chrome class,
        The differance between the functions is the ability to remove alerts automatically.

        @param url: The URL we are getting.
        @type url: str
        @return: None
        """
        super(Browser, self).get(url)
        if self.__remove_alerts:
            self.dump_alerts()

    def refresh(self):
        """
        This function overrides the default refresh() method of the Chrome class,
        The differance between the functions is the ability to remove alerts automatically.

        @return: None
        """
        self.dump_alerts()
        super(Browser, self).refresh()
        if self.__remove_alerts:
            self.dump_alerts()
