#!/usr/bin/python3
import mechanize
import http.cookiejar
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import Data
import colors

COLOR_MANAGER = colors.Colors()


def get_pages(data, curr_url, session_page=False):
    # Opening the current url
    data.session.open(curr_url)
    # Adding the url to the data list
    if session_page:
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
        if data.session.geturl() not in data.pages:
            print(
                "\t["
                + COLOR_MANAGER.BRIGHT_BLUE
                + "+"
                + COLOR_MANAGER.ENDC
                + "] "
                + COLOR_MANAGER.BRIGHT_BLUE
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

    if len(data.username) != 0 and len(data.password) != 0:
        try:
            data.session.select_form(nr=0)
            data.session.form['username'] = data.username
            data.session.form['password'] = data.password
            data.session.submit()

            get_pages(data, data.session.geturl(), True)
        except Exception as e:
            pass


print(
        COLOR_MANAGER.ORANGE
        + COLOR_MANAGER.UNDERLINE
        + COLOR_MANAGER.BOLD
        + "Website pages:"
        + COLOR_MANAGER.ENDC
        )
data = Data.Data(url="http://192.168.56.102/dvwa/", username="admin", password="admin")
get_pages(data, data.address)
print("Pages with no login: " + str(len(data.pages)))
print("Pages with login: " + str(len(data.session_pages)))
data.session.open("http://192.168.56.102/dvwa/vulnerabilities/xss_r/")
print(data.session.response().read().decode())