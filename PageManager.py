from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import Data, SessionPage, Page
import requests
import mechanize
import http.cookiejar

pages_block_list = []
already_printed = []
finished = True


def get_pages(data: Data, curr_url, session_page=False, recursive=True):
    """
    Function gets the lists of pages to the data object
    :param data: the data object of the program
    :param curr_url: the current URL the function checks
    :param session_page: True- if the current page is in a special session False- else
    :param recursive: True- check all website pages, False- only the first reachable one
    """
    global finished
    if not finished:
        return

    if len(data.pages) == data.max_pages:
        # In case of specified amount of pages, the function will stop
        return

    try:
        # Opening the current URL
        data.session.open(curr_url)

        if data.session.geturl() != curr_url and session_page:
            # Changed the URL, redirected
            for page in data.pages:
                if type(page) is not SessionPage and page.url == data.session.geturl():
                    finished = False
                    print(f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}")
                    pages_block_list.append(curr_url)
            return
        # Creating a BeautifulSoup object
        soup = BeautifulSoup(data.session.response().read().decode(), "html.parser")
    except Exception as e:
        return

    curr_url = data.session.geturl()

    # Adding the URL to the data list
    if check_url(data, session_page):
        # If the page is not in the page list
        if session_page:
            # Page requires a session
            color = COLOR_MANAGER.ORANGE
            page = SessionPage(curr_url, data.session.response().code,
                               data.session.response().read().decode(), data.cookies)
        else:
            # Page doesn't require a session
            color = COLOR_MANAGER.BLUE
            page = Page(curr_url, data.session.response().code,
                        data.session.response().read().decode())
    else:
        # The page is already in the page list
        return

    # Adding to the list
    if all(curr_url != page.url for page in already_printed):
        print(f"\t[{color}+{COLOR_MANAGER.ENDC}] {color}{curr_url}{COLOR_MANAGER.ENDC}")
        already_printed.append(page)

    data.pages.append(page)

    if recursive:
        # If the function is recursive
        # Getting every link in the page
        for href in soup.find_all("a"):
            href = urljoin(curr_url, href.get("href"))  # Full URL
            if str(href).startswith(f"{str(data.url).split(':')[0]}:{str(data.url).split(':')[1]}"):
                # Only URLs that belongs to the website
                if all(href != page.url for page in data.pages):
                    # If the page is not in the page list
                    if href not in pages_block_list:
                        # Page isn't redirecting
                        get_pages(data, href, session_page, data.recursive)

    if data.username and data.password:
        # If there are username and password
        if any(username in page.content for username in ['name="username"', 'name=username']) and \
                any(password in page.content for password in ['name="password"', 'name=password']):
            try:
                data.session.open(curr_url)
                data.session.select_form(nr=0)
                data.session.form['username'] = data.username
                data.session.form['password'] = data.password
                data.session.submit()
                data.session.reload()
                new_url = data.session.geturl()
                if check_url(data, True):
                    # If the new URL was not in the page list try to get the page with the new login details
                    get_pages(data, new_url, True, recursive)
            except Exception as e:
                return False


def check_url(data: Data, session_page: bool) -> bool:
    for page in data.pages:
        if data.session.geturl() == page.url:
            if not session_page or type(page) is SessionPage:
                return False
            content = requests.get(page.url).content
            if data.session.response().read().decode() == content.decode():
                return False
    return True


def logic(data: Data):
    """
    Function gets the pages list
    """
    print(COLOR_MANAGER.BLUE + COLOR_MANAGER.HEADER + "Scraping pages:" + COLOR_MANAGER.ENDC)
    try:
        global finished
        while True:
            get_pages(data, data.url)
            if finished:
                break
            else:
                # Refreshing the session
                data.pages = list()
                data.session = mechanize.Browser()
                data.cookies = http.cookiejar.CookieJar()  # Session cookies
                data.session.set_cookiejar(data.cookies)  # Setting the cookies
                finished = True
    except Exception as e:
        raise Exception(str(e) + "Unknown problem occurred.\n"
                        "\tIn case of too many pages, try not using (-r) or putting another URL")
    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages")
    session_pages = 0
    for page in data.pages:
        if type(page) is SessionPage:
            session_pages += 1
    print(f"\n{COLOR_MANAGER.BLUE}Pages that does not require login authorization: {len(data.pages) - session_pages}")
    print(f"{COLOR_MANAGER.ORANGE}Pages that requires login authorization: {session_pages}\n")
