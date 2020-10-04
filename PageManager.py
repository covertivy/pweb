#!/usr/bin/python3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import colors

COLOR_MANAGER = colors.Colors()


def get_pages(data, curr_url, session_page=False):
    """
    this function gets the lists of pages to the data object
    :param data: the data object of the program
    :param curr_url: the current url the function checks
    :param session_page: True- if the current page is in a special session False- else
    """
    if len(data.pages) + len(data.session_pages) == data.max_pages:
        # In case of mentioned amount of pages, the function will stop
        return
    # Opening the current url
    data.session.open(curr_url)
    # Adding the url to the data list
    if session_page:
        # Page requires a session
        if data.session.geturl() not in data.session_pages \
                and data.session.geturl() not in data.pages:
            print(
                "\t["
                + COLOR_MANAGER.ORANGE
                + "+"
                + COLOR_MANAGER.ENDC
                + "] "
                + COLOR_MANAGER.ORANGE
                + data.session.geturl()
                + COLOR_MANAGER.ENDC
            )
            data.session_pages.append(data.session.geturl())
        else:
            return
    else:
        # Page doesn't require a session
        if data.session.geturl() not in data.pages:
            print(
                "\t["
                + COLOR_MANAGER.CYAN
                + "+"
                + COLOR_MANAGER.ENDC
                + "] "
                + COLOR_MANAGER.CYAN
                + data.session.geturl()
                + COLOR_MANAGER.ENDC
            )
            data.pages.append(data.session.geturl())
        else:
            return
    # Creating a BeautifulSoup object
    soup = BeautifulSoup(data.session.response().read().decode(), "html.parser")
    # Getting every link in the page
    for href in soup.find_all("a"):
        href = urljoin(curr_url, href.get("href"))  # Full URL
        if str(href).startswith(data.address):
            # Only URLs that belongs to the website
            get_pages(data, href, session_page)

    if data.username and data.password:
        # If there are username and password
        try:
            # Trying to get the page with login details
            data.session.select_form(nr=0)
            data.session.form['username'] = data.username
            data.session.form['password'] = data.password
            data.session.submit()
            # Trying to get the page with the new login details
            get_pages(data, data.session.geturl(), True)
        except Exception:
            return
