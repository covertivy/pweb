from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colors import COLOR_MANAGER
from Classes import Data, Manager, Page, Browser
import Methods
import requests
from seleniumwire import webdriver
import sys
import os
import io
import zipfile


class PageManager(Manager):
    def __init__(self):
        # ----------------------------- Variables -----------------------------
        self.__type_colors = {
            "HTML": COLOR_MANAGER.BLUE,  # The session is the one that decides
            COLOR_MANAGER.ORANGE + "HTML": COLOR_MANAGER.ORANGE,
            "Javascript": COLOR_MANAGER.GREEN,
            "CSS": COLOR_MANAGER.PINK,
            "XML": COLOR_MANAGER.YELLOW,
            "Other": COLOR_MANAGER.PURPLE}  # Dictionary of the mime-types and their color.
        # Pages lists
        self.__already_printed = list()  # List of printed Pages/SessionPages.
        self.__already_checked = list()  # List of checked Pages/SessionPages.
        self.__troublesome = list()  # List of troublesome URLs.
        # Session variables
        self.__non_session_browser = list()  # [0] is None or browser.
        # It is a list because it can be None or browser.
        self.__logout_list = list()  # List of logout URLs.
        self.__logged_out = False  # Logout flag.
        self.__logged_in = False  # If set, we made a login act.
        # Word lists
        self.__black_list = list()  # List of words that the user do not want to check.
        self.__white_list = list()  # List of words that the user only wants to check.
        # ----------------------------- Constants -----------------------------
        self.__PADDING = 4  # Spaces.

    @staticmethod
    def __get_links(links: list, url: str):
        """
        This function returns a filtered list of links that not equal to the current URL but have same domain.

        @param links: The list of every link in the page
        @type links: list
        @param url: The current URL
        @type url: str
        @return: List of valid links
        @rtype: list
        """
        valid_links = list()
        for link in [urljoin(url, link) for link in links]:
            clean_link = link.replace(urlparse(link).scheme, '')
            clean_url = url.replace(urlparse(url).scheme, '')
            if urlparse(link).hostname == urlparse(url).hostname and clean_link != clean_url:
                # Only URLs that belongs to the website and not equal to the parent URL
                valid_links.append(link)
        valid_links = list(set(valid_links))
        valid_links.sort()  # Links list sorted in alphabetic order
        return valid_links

    @staticmethod
    def __get_login_form(data: Data, forms: list):
        """
        This function gets the login form of the page.

        @param data: The data object of the program
        @type data: Classes.Data
        @param forms: The list of the forms of the page
        @type forms: list
        @return: Dictionary of the form details
        @rtype: dict
        """
        for form in forms:
            inputs = form["inputs"]
            login_input = [False, False]  # Check if the form is login form
            for input_tag in inputs:
                if "name" in input_tag.keys():
                    # If there is an input name
                    if input_tag["name"].lower() == "username":
                        # Username input
                        value = data.username
                        login_input[0] = True
                    elif input_tag["name"].lower() == "password":
                        # Password input
                        value = data.password
                        login_input[1] = True
                    else:
                        # At least one of the 2 text input is not valid
                        break
                    input_tag["value"] = value
            if login_input[0] and login_input[1]:
                # There both username and password in the form
                return form
        return dict()

    @staticmethod
    def __is_session_alive(data: Data, browser: Browser):
        """
        This function checks if the session of the browser is still alive.

        @param data: The data object of the program
        @type data: Classes.Data
        @param browser: Chrome driver object
        @type browser: webdriver.Chrome
        @return: True - session still alive, False - session has logged out
        @rtype: bool
        """
        same_content = 0
        different_content = 0
        for session_page in [page for page in data.pages if page.is_session]:
            if session_page.cookies != browser.get_cookies():
                # Does not have the same cookies of the other session pages
                return False
            browser.get(session_page.url)
            browser.refresh()
            if Methods.remove_forms(browser.page_source) != Methods.remove_forms(session_page.content):
                # Does not have the same content
                different_content += 1
            else:
                # Have the same content
                same_content += 1
        # If there are more same-content pages than different-content pages
        return different_content <= same_content

    @staticmethod
    def __set_chromedriver(data: Data):
        """
        This function sets a browser web driver object for the first time,
        and downloads chromedriver file in case of first time running the program.

        @param data: The data object of the program
        @type data: Classes.Data
        @return: None
        """
        driver_file = "chromedriver"
        pl = sys.platform
        # Get OS
        if pl == "linux" or pl == "linux2":
            operating_system = "linux64"
        elif pl == "darwin":
            operating_system = "mac64"
        else:
            operating_system = "win32"
            driver_file += ".exe"
        if driver_file not in os.listdir("."):  # There is no chromedriver in the folder
            # Getting zip file
            print(f"\t[{COLOR_MANAGER.YELLOW}?{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.YELLOW}"
                  f"Downloading Chromedriver...{COLOR_MANAGER.ENDC}")
            try:
                # Get latest version
                version = requests.get("http://chromedriver.storage.googleapis.com/LATEST_RELEASE").text
                # Get zip link
                link = f"https://chromedriver.storage.googleapis.com/" \
                       f"{version}/chromedriver_{operating_system}.zip"
                zip_content = io.BytesIO(
                    requests.get(link).content)
                with zipfile.ZipFile(zip_content) as zip_ref:
                    # Extracting the executable file
                    zip_ref.extractall(".")
            except Exception:
                raise Exception("Download failed, please check your internet connection.")
        # There is a chromedriver in the folder
        data.driver = os.getcwd() + "\\" + driver_file  # Full path
        try:
            print(f"\t[{COLOR_MANAGER.YELLOW}?{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.YELLOW}"
                  f"Setting up the Chromedriver...{COLOR_MANAGER.ENDC}")
        except Exception:
            raise Exception("Setting up the web driver failed, please try again.")

    def __valid_in_list(self, page: Page):
        """
        This function checks if a page is valid by the black and white lists.

        @param page: A page object
        @type page: Classes.Page
        @return: True - valid page, False - otherwise
        @rtype: bool
        """
        # If there is a white list and the URL does not have any of the words
        # Or there is a black list and the URL have one of the words
        return not ((self.__white_list and all(word not in page.url for word in self.__white_list)) or
                    (self.__black_list and any(word in page.url for word in self.__black_list)))

    def __get_pages(self, data: Data, curr_url: str, browser: Browser,
                    previous: Page = None, recursive: bool = True):
        """
        This function gets the list of pages to the data object.

        @param data: The data object of the program
        @type data: Classes.Data
        @param curr_url: The current URL the function checks
        @type curr_url: str
        @param browser: The web driver that gets the rendered content
        @type browser: Browser
        @param previous: The previous page
        @type previous: bool
        @param recursive: True - check all website pages, False - only the first reachable one
        @type recursive: bool
        @return: None
        """
        if len(data.pages) == data.max_pages:
            # In case of specified amount of pages, the function will stop
            return

        if curr_url in self.__logout_list:
            # Do not open logout pages
            return

        if self.__logged_out:
            # If the session already logged out
            if self.__non_session_browser[0]:
                # Remove non session browser
                self.__non_session_browser[0].quit()
                self.__non_session_browser[0] = None
            if self.__logged_in:
                # If we logged in (-L) we need to return
                # If we used cookies (-c) we can keep going
                return
        try:
            # Trying to get the current URL
            browser.get(curr_url)
            request = None
            for req in browser.requests[::-1]:
                if req.url == curr_url or req.url == browser.current_url:
                    # If we found the right URL
                    request = req
                    if req.response.headers.get("Content-Type"):
                        # Only if the page has content type
                        break
            if not request or request.response.status_code != 200:
                # Did not find the request
                raise Exception()  # The request is not found
        except Exception:
            self.__troublesome.append(curr_url)
            return

        page = Page(
            browser.current_url,
            request.response.status_code,
            request.response.headers.get("Content-Type").split(";")[0],
            browser.page_source,
            request,
            browser.get_cookies(),
            previous)
        color = COLOR_MANAGER.BLUE

        if self.__non_session_browser[0]:
            # Session page
            try:
                same_content = False
                same_url = False
                a_page = None
                for a_page in data.pages:
                    if not self.__get_links([a_page.url], browser.current_url):
                        # Have the same URL
                        same_url = True
                    if "html" in a_page.type and \
                            Methods.remove_forms(a_page.content) == Methods.remove_forms(browser.page_source):
                        # Have the same content of another page
                        same_content = True
                    if same_url or same_content:
                        # Already found what we were looking for
                        break
                if "logout" in curr_url.lower() or same_content:
                    if not self.__is_session_alive(data, browser):
                        # It redirected to a non-session page, and have the same content or logout in name
                        print(f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                              f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}")
                        self.__logout_list.append(curr_url)
                        self.__logged_out = True
                        if not self.__logged_in:
                            # In case of cookies (-c), the logout action makes the cookies invalid
                            removed_list = list()
                            for page in data.pages:
                                if not page.is_session:
                                    removed_list.append(page)
                            data.pages = removed_list
                            print(f"\t[{COLOR_MANAGER.RED}!{COLOR_MANAGER.ENDC}]"
                                  f" {COLOR_MANAGER.RED}Cookies are invalid anymore,"
                                  f" all session pages were removed.{COLOR_MANAGER.ENDC}")
                        return
                    else:
                        browser.get(request.url)
                if same_content and same_url and a_page.is_session:
                    # Redirected to another session page with the same URL or content
                    self.__troublesome.append(curr_url)  # No need to check
                    return
                self.__non_session_browser[0].get(browser.current_url)
                if self.__non_session_browser[0].current_url != browser.current_url or \
                        Methods.remove_forms(self.__non_session_browser[0].page_source) !=\
                        Methods.remove_forms(browser.page_source):
                    # If the URL can be reachable from non-session point the session has logged out
                    # Session page
                    page.is_session = True
                    color = COLOR_MANAGER.ORANGE
            except Exception:
                self.__troublesome.append(curr_url)
                return

        soup = None
        if "html" in page.type:
            # Only if the page is html
            try:
                # Creating a BeautifulSoup object
                soup = BeautifulSoup(page.content, "html.parser")
            except Exception:
                # Couldn't parse, might be non-html format, like pdf or docx
                self.__troublesome.append(page.url)
                return
        if page.url != curr_url:
            # If the current URL is redirecting to another URL
            self.__troublesome.append(curr_url)
            if previous and not self.__get_links([previous.url], page.url):
                # The Redirected link is out of the website
                return

        # Checking if the page was already printed
        in_list = False
        for printed_page in self.__already_printed:
            if not self.__get_links([printed_page.url], page.url) and\
                    (printed_page.content == page.content or printed_page.is_session == page.is_session):
                # Same URL (without the http://) and content or both are session
                in_list = True
        if not in_list:
            # If the page was not printed
            if not soup:
                # If it is a non-html page
                color = self.__type_colors["Other"]
                for key in self.__type_colors.keys():
                    if str(key).lower() in page.type:
                        color = self.__type_colors[key]
                        break
            # Printing the page
            sign = "+"
            if not self.__valid_in_list(page):
                sign = "-"  # Sign of not checking
            print(f"\t[{color}{sign}{COLOR_MANAGER.ENDC}] {color}{page.url}{COLOR_MANAGER.ENDC}")
            self.__already_printed.append(page)

        # Checking if the page was already checked
        in_list = False
        for a_page in data.pages:
            if not self.__get_links([a_page.url], page.url) and\
                    (a_page.content == page.content or a_page.is_session == page.is_session):
                # Same URL (without the http://) and (content or both are session)
                in_list = True
        if not in_list:
            # Adding to the page list
            data.pages.append(page)

        # Adding to the already-checked list.
        self.__already_checked.append(page)

        if not soup:
            # There is no reason check non-html page.
            return

        # Getting every application script in the page.
        links = self.__get_links([script.get("src") for script in soup.find_all("script")], page.url)

        # Getting every css style in the page.
        links.extend(self.__get_links([script.get("href") for script in soup.find_all(type="text/css")], page.url))

        for link in links:
            # Checking only scripts and style file
            for req in browser.requests:
                if link == req.url:
                    # Were already requested with the current page
                    self.__get_pages(data, link, browser, page, data.recursive)
                    links.remove(link)
                    break

        del browser.requests  # We do not need the previous requests anymore

        if recursive:
            # If the function is recursive.
            # Getting every link in the page.
            links.extend(self.__get_links([link.get("href") for link in soup.find_all("a")], page.url))

        for link in links:
            if (self.__logged_out and self.__logged_in) or len(data.pages) == data.max_pages:
                # More efficient to check every time.
                # If the session logged out or the pages amount is at its maximum.
                return
            if all(link != page.url for page in data.pages) or self.__non_session_browser[0]:
                # If the page is not in the page list
                if (not any(link == checked_page.url for checked_page in self.__already_checked)
                        and link not in self.__troublesome):
                    # Page was not checked, it is not troublesome or in the black list
                    self.__get_pages(data, link, browser, page, data.recursive)

    def __get_session_pages(self, data: Data, browser: Browser):
        """
        This function looking for login forms and scraping session pages through them.

        @param data: The data object of the program
        @type data: Classes.Data
        @param browser: The webdriver browser
        @type browser: Browser
        @return: None
        """
        if not (data.username and data.password):
            # If there are no username or password
            return
        if not self.__non_session_browser[0]:
            # If the instance is not already set, set up a new one
            self.__non_session_browser[0] = Methods.new_browser(data)
        
        non_session_pages = list(data.pages)
        pages_backup = list(data.pages)
        login_pages = list()
    
        for page in non_session_pages:
            if "html" not in page.type:
                continue
            # Checking if the page has a login form
            if not self.__get_login_form(data, Methods.get_forms(page.content)):
                continue
            # Setting browser for current page
            browser.get(page.url)
            # Getting updated form
            form_details = self.__get_login_form(data, Methods.get_forms(browser.page_source))
            try:
                Methods.submit_form(data, browser, form_details["inputs"])
            except Exception:
                continue
            new_url = browser.current_url
            content = browser.page_source
            if new_url in login_pages:
                # The new url is already in the list
                continue
            login_pages.append(new_url)
            login = True
            for p in data.pages:
                if new_url == p.url:
                    # Have the same URL
                    if Methods.remove_forms(content) == Methods.remove_forms(p.content):
                        # Same URL and content
                        login = False  
                    break  # We do not need to check anymore
            if not login:
                # Login attempt failed.
                continue
    
            # Setting login flags
            self.__logged_out = True
            self.__logged_in = True
    
            while self.__logged_out:
                # Until it won't encounter a logout page
                self.__logged_out = False
                # Attempting to achieve data from page
                self.__get_pages(data, new_url, browser, page)
                if self.__logged_out:
                    # If the session has encountered a logout page
                    self.__already_checked.clear()  # The function needs to go through all the session pages
                    for checked_page in data.pages:
                        if "html" not in checked_page.type and checked_page not in pages_backup:
                            pages_backup.append(checked_page)
                            self.__already_checked.append(checked_page)
                    data.pages = list(pages_backup)  # Restoring the pages list
                    # Updating the session
                    browser.delete_all_cookies()
                    browser.get(page.url)
                    Methods.enter_cookies(data, browser, page.url)
                    Methods.submit_form(data, browser, form_details["inputs"])
                    # Doing the loop all over again, without the logout page
            break
        # Closing the non session browser
        self.__non_session_browser[0].quit()
        if len(data.pages) == len(non_session_pages):
            # Session never append
            if login_pages:
                # Found at least one login page
                raise Exception("The login attempt failed, your username or password might be invalid.\n", "\n\t")
            else:
                # No login pages were found.
                raise Exception("The program did not find any login form in the listed pages.\n", "\n\t")

    def __set_lists(self, data: Data):
        """
        This function sets the black and white lists.

        @param data: The data object of the program
        @type data: Classes.Data
        @return: None
        """
        def set_list(file: str, black: bool):
            """
            Inner function to set a list by it's file path.

            @param file: The file path of the list
            @type file: str
            @param black: True - black list, False - white list
            @type black: bool
            @return: None
            """
            if not file:
                # No file was specified
                return
            if os.path.exists(file):
                # If the file exists
                with open(file, "r") as f:
                    current_list = f.read()
            else:
                # The file does not exists
                COLOR_MANAGER.print_error(f"The file {file} was not found", "\t")
                return
            current_list = current_list.replace("\n", "").replace(" ", "")  # Removing "\n"s and spaces
            current_list = [word for word in current_list.split(",") if len(word)]  # List of words
            if current_list:
                # Everything is fine
                COLOR_MANAGER.print_success(f"The file {file} has been"
                                            f" added to the filtering process.", "\t")
                if black:
                    self.__black_list = current_list
                else:
                    self.__white_list = current_list
            else:
                # Empty file
                COLOR_MANAGER.print_error(f"The file {file} is not in the"
                                          f" format of <word1>, <word2>.", "\t")
        set_list(data.blacklist, True)  # Setting black list
        set_list(data.whitelist, False)  # Setting white list
        if self.__white_list and self.__black_list:
            # The user specified valid data for both
            COLOR_MANAGER.print_warning("The process will filter"
                                        " the pages only by the white list.", "\t")
        print(COLOR_MANAGER.ENDC)

    def __set_cookies(self, data: Data, browser: Browser):
        """
        This function sets the specified cookies to the browser.

        @param data: The data object of the program
        @type data: Classes.Data
        @param browser: The webdriver browser
        @type browser: Browser
        @return: None
        """
        if data.cookies:
            # If user specified cookies
            if Methods.enter_cookies(data, browser, data.url):
                # Success
                self.__non_session_browser[0] = Methods.new_browser(data)  # setting up secondary browser object
                print(f"\t[{COLOR_MANAGER.YELLOW}!{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.YELLOW}"
                      f"Cookies were added to the session.{COLOR_MANAGER.ENDC}")
            else:
                # Failure
                print(f"\t[{COLOR_MANAGER.YELLOW}!{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.YELLOW}"
                      f"Invalid cookies, check your syntax and try again. {COLOR_MANAGER.ENDC}")
                data.cookies = None  # There is no need to use them again

    def logic(self, data: Data):
        """
        This function gets the page list of the specified website.

        @param data: The data object of the program
        @type data: Classes.Data
        @return: None
        """
        print(f"{COLOR_MANAGER.BLUE + COLOR_MANAGER.HEADER}Scraping pages:{COLOR_MANAGER.ENDC}")
        # Setting environment
        self.__non_session_browser.append(None)
        try:
            self.__set_lists(data)  # Setting white and black list
            self.__set_chromedriver(data)  # Setting web browser driver
            browser = Methods.new_browser(data)  # Setting up browser object
            self.__set_cookies(data, browser)  # Setting up specified cookies
            print(COLOR_MANAGER.ENDC)
        except Exception as e:
            raise Exception(e, "\t")
        try:
            # Getting the pages
            self.__get_pages(data, data.url, browser, None)
            # We need to clear them in case of session pages
            self.__already_checked.clear()
        except Exception:
            raise Exception("Unknown problem occurred.", "\t")
        # In case of empty website
        if len(data.pages) == 0:
            raise Exception("Your website doesn't have any valid web pages.", "\t")
        if len(data.pages) != data.max_pages:
            # Getting the session pages.
            self.__get_session_pages(data, browser)
        # Printing the results
        self.__print_result(data)
        # Transferring only the valid pages
        data.pages = [page for page in data.pages if self.__valid_in_list(page)]
        browser.quit()
        # In case of empty website
        if len(data.pages) == 0:
            raise Exception("Your website doesn't have any web pages that fit your requirements.\n", "\t")

    def __print_result(self, data: Data):
        """
        This function prints the result of the web scraper.

        @param data: The data object of the program
        @type data: Classes.Data
        @return: None
        """
        def print_type(pages: list, sign: str):
            type_count = dict()
            for key in self.__type_colors.keys():
                type_count[key] = 0  # Initiating the dictionary {"mime type": count}
            for page in pages:
                found = False
                for key in type_count.keys():
                    if str(key).lower() in page.type:
                        if key == "HTML" and page.is_session:
                            type_count[COLOR_MANAGER.ORANGE + "HTML"] += 1
                        else:
                            type_count[key] += 1
                        found = True
                if not found:
                    type_count["Other"] += 1
            for key in type_count:
                if type_count[key]:
                    padding = " " * (self.__PADDING - len(str(type_count[key])))
                    print(f"\t\t[{self.__type_colors[key]}{sign}{COLOR_MANAGER.ENDC}]"
                          f"{self.__type_colors[key]} {type_count[key]}{padding}{key} pages{COLOR_MANAGER.ENDC}")

        print("")
        non_session_pages = [page for page in data.pages
                             if self.__valid_in_list(page) and not page.is_session]
        if non_session_pages:
            print(f"\t{COLOR_MANAGER.BLUE}Pages that does not require login authorization:{COLOR_MANAGER.ENDC}")
            print_type(non_session_pages, "+")
        session_pages = [page for page in data.pages
                         if self.__valid_in_list(page) and page.is_session]
        if session_pages:
            # If there are session pages
            print(f"\t{COLOR_MANAGER.ORANGE}Pages that requires login authorization:{COLOR_MANAGER.ENDC}")
            print_type(session_pages, "+")
        not_included = [page for page in data.pages if not self.__valid_in_list(page)]
        if not_included:
            print(f"\t{COLOR_MANAGER.RED}Pages that are blocked from being checked:{COLOR_MANAGER.ENDC}")
            print_type(not_included, "-")
        print(COLOR_MANAGER.ENDC)
