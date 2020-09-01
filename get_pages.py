#!/usr/bin/python
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import colors

COLOR_MANAGER = colors.Colors()


class Pages:
    __VALID_WEB_FILES = ("aspx", "html", "php")

    def __init__(self, url, username="admin", password="admin", pages=-1):
        """
        function creates an object that stores the main three elements we use
        :param url: the main url of the checked website (must end with '/')
        :param username: most case use admin but optional for the user
        :param password: most case use admin but optional for the user
        :param max: the number of pages the user wants
        """
        # Public variables
        self.pages = list()  # List of the pages and their sessions in the website
        self.username = username  # The username to the website
        self.password = password  # The password to the website
        self.session = requests.session()  # To keep the conversation we need a session
        self.url = url  # Just in case we will need it in the future
        self.__max = pages  # More convenient to store it that way
        print(COLOR_MANAGER.ORANGE + COLOR_MANAGER.UNDERLINE + COLOR_MANAGER.BOLD + "Website pages:" + COLOR_MANAGER.ENDC)
        self.__get_all_pages(url)

    def __get_all_pages(self, current_page):
        """
        Function gets all the pages of the website by recursion
        :param current_page: The current page the session is talking to
        :return: none
        """
        # Check if there are enough pages
        if len(self.pages) == self.__max:
            return

        # Getting the current page
        page = self.session.get(current_page)
        if page.url not in self.pages:
            # Appending the url to the list
            print("\t[" + COLOR_MANAGER.ORANGE + "+" + COLOR_MANAGER.ENDC + "] " +
                  COLOR_MANAGER.ORANGE + page.url + COLOR_MANAGER.ENDC)
            self.pages.append(page.url)
        else:
            # If the url is in the list,
            # it's more efficient to attempt the login at this stage
            # For example: login.php can turn to index.php after the login attempt
            self.__login(page.url)
            return

        # Creating a BeautifulSoup object
        soup = BeautifulSoup(page.text, 'html.parser')

        # Getting every link in the page
        for href in soup.find_all('a'):
            href = urljoin(current_page, href.get("href"))  # Full URL
            if self.__check_href(current_page, href):
                self.__get_all_pages(href)

        # There is a chance that it's a login page so we need to check just in case
        self.__login(page.url)

    def __login(self, current_page):
        """
        Function attempts to login if the current page is a login page
        :param current_page: The page we are checking
        :return: none
        """
        # Attempting to log into the page
        after_login = self.session.post(current_page,
                        data={"username": self.username, "password": self.password, "Login": "Login"}).url
        if after_login != current_page:
            # The login worked
            # Appending this page to the list and checking it:
            self.__get_all_pages(after_login)

    def __check_href(self, current_page, href):
        """
        Function check if a href is a valid href that we need to check
        :param current_page: The page we are currently checking
        :param href: The href we found in the current page
        :return: False - invalid href, True - valid href
        """
        if len(href.split("/")[-1].split(".")) == 2:
            # Only urls with .file (/login.php, /index.php...)
            if not href.split("/")[-1].split(".")[1].startswith(self.__VALID_WEB_FILES):
                # For example: ".php?#%@" is valid, ".pdf" is not valid
                return False
        if str(href).startswith(self.url):
            # Only URLs that belongs to the website
            href = self.session.get(href).url
            # Prevent urls that redirect you to an already checked page
            # for example: logout.php redirects to login.php and creates infinite loop
            if href not in self.pages:
                return True
        return False
