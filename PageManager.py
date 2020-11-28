#!/usr/bin/python3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import Data, SessionPage, Page


def get_pages(data: Data, curr_url, session_page=False, non_recursive=False):
    """
    Function gets the lists of pages to the data object
    :param data: the data object of the program
    :param curr_url: the current URL the function checks
    :param session_page: True- if the current page is in a special session False- else
    """
    if len(data.pages) == data.max_pages:
        # In case of specified amount of pages, the function will stop
        return

    try:
        # Opening the current URL
        data.session.open(curr_url)
        # Creating a BeautifulSoup object
        soup = BeautifulSoup(data.session.response().read().decode(), "html.parser")
    except Exception as e:
        return

    # Adding the URL to the data list
    if all(data.session.geturl() != page.url for page in data.pages):
        # If the page is not in the page list
        if session_page:
            # Page requires a session
            color = COLOR_MANAGER.ORANGE
            page = SessionPage(data.session.geturl(), data.session.response().code,
                               data.session.response().read().decode(), data.cookies)
        else:
            # Page doesn't require a session
            color = COLOR_MANAGER.BLUE
            page = Page(data.session.geturl(), data.session.response().code,
                        data.session.response().read().decode())
    else:
        # The page is already in the page list
        return

    # Adding to the list
    print(f"\t[{color}+{COLOR_MANAGER.ENDC}] {color}{data.session.geturl()}{COLOR_MANAGER.ENDC}")
    data.pages.append(page)

    if not non_recursive:
        # If the function is recursive
        # Getting every link in the page
        for href in soup.find_all("a"):
            href = urljoin(curr_url, href.get("href"))  # Full URL
            if str(href).startswith(data.url):
                # Only URLs that belongs to the website
                if all(href != page.url for page in data.pages):
                    # If the page is not in the page list
                    get_pages(data, href, session_page, data.nr)

    if data.username and data.password:
        # If there are username and password
        try:
            # Trying to get the page with login details
            data.session.select_form(nr=0)
            data.session.form['username'] = data.username
            data.session.form['password'] = data.password
            data.session.submit()

            if all(data.session.geturl() != page.url for page in data.pages):
                # If the new URL was not in the page list try to get the page with the new login details
                get_pages(data, data.session.geturl(), True)
        except Exception:
            return


def logic(data: Data):
    """
    Function gets the pages list
    """
    print(COLOR_MANAGER.BLUE + COLOR_MANAGER.HEADER + "Scraping pages:" + COLOR_MANAGER.ENDC)
    get_pages(data, data.url)
    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages")
    print("\n", end="")
