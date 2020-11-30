from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import Data, SessionPage, Page
import requests
import mechanize
import http.cookiejar

block_list = []
logout_pages = []
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
        if session_page:
            # It was in a session
            # Opening the current URL
            new_url = data.session.open(curr_url).geturl()
            if new_url != curr_url:
                # If the current URL is redirecting to another URL
                res = requests.get(new_url)
                if res.url == new_url:
                    # The new URL isn't session
                    if not check_url(new_url, data.session.response().read().decode(), data, False) \
                            or "logout" in curr_url:
                        # The new URL is already in the list
                        logout_pages.append(curr_url)
                        finished = False
                        print(f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                              f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}")
                        return
                    else:
                        # The new URL isn't session
                        session_page = False
                        curr_url = new_url
                else:
                    # The new URL is still session page
                    curr_url = new_url
            content = data.session.response().read().decode()
            res = data.session.response()
        else:
            # It wasn't in a session
            res = requests.get(curr_url)
            if res.url != curr_url:
                # If the current URL is redirecting to another URL
                block_list.append(curr_url)
            elif not check_url(res.url, res.content.decode(), data, False):
                # The new URL is already in the list
                block_list.append(curr_url)
                return
            content = res.content.decode()
            curr_url = res.url

        # Creating a BeautifulSoup object
        soup = BeautifulSoup(content, "html.parser")
    except Exception as e:
        # Couldn't open with the session
        block_list.append(curr_url)
        return

    # Adding the URL to the data list
    if check_url(curr_url, content, data, session_page):
        # If the page is not in the page list
        if session_page:
            # Page requires a session
            color = COLOR_MANAGER.ORANGE
            page = SessionPage(curr_url, res.code,
                               content, data.cookies)
        else:
            # Page doesn't require a session
            color = COLOR_MANAGER.BLUE
            page = Page(curr_url, res.status_code,
                        content)
    else:
        # The page is already in the page list
        return

    # Adding to the list
    if not any(page.url == printed_page.url and
               type(page) == type(printed_page) for printed_page in already_printed):
        print(f"\t[{color}+{COLOR_MANAGER.ENDC}] {color}{curr_url}{COLOR_MANAGER.ENDC}")
        already_printed.append(page)

    data.pages.append(page)

    if recursive:
        # If the function is recursive
        # Getting every link in the page
        links = [urljoin(curr_url, x.get("href")) for x in list(set(soup.find_all("a")))]
        links.sort()
        for link in links:
            if str(link).startswith(f"{str(data.url).split(':')[0]}:{str(data.url).split(':')[1]}"):
                # Only URLs that belongs to the website
                if all(link != page.url for page in data.pages):
                    # If the page is not in the page list
                    if link not in block_list:
                        # Page isn't redirecting
                        get_pages(data, link, session_page, data.recursive)

    if data.username and data.password:
        # If there are username and password
        if any(username in page.content for username in ['name="username"', 'name=username']) and \
                any(password in page.content for password in ['name="password"', 'name=password']):
            try:
                br = mechanize.Browser()
                br.set_cookiejar(http.cookiejar.CookieJar())
                br.open(curr_url)
                br.select_form(nr=0)
                br.form['username'] = data.username
                br.form['password'] = data.password
                br.submit()
                new_url = br.geturl()
                if check_url(new_url, br.response().read().decode(), data, True):
                    # If the new URL was not in the page list try to get the page with the new login details
                    data.session = br
                    data.cookies = br.cookiejar
                    data.session.set_cookiejar(data.cookies)
                    get_pages(data, new_url, True, recursive)
            except Exception as e:
                return False


def check_url(url: str, content: str, data: Data, session_page: bool) -> bool:
    for page in data.pages:
        if url == page.url:
            if not session_page:
                return False
            if type(page) is SessionPage:
                return False
            if content == requests.get(page.url).content.decode():
                return False
    return True


def logic(data: Data):
    """
    Function gets the pages list
    """
    print(COLOR_MANAGER.BLUE + COLOR_MANAGER.HEADER + "Scraping pages:" + COLOR_MANAGER.ENDC)
    try:
        global finished
        global block_list
        while True:
            finished = True
            get_pages(data, data.url)
            if finished:
                break
            else:
                # Refreshing the session
                block_list = logout_pages
                data.pages = list()
                data.session = mechanize.Browser()
                data.cookies = http.cookiejar.CookieJar()  # Session cookies
                data.session.set_cookiejar(data.cookies)  # Setting the cookies
    except Exception as e:
        raise Exception(str(e) + "Unknown problem occurred.\n"
                        "\tIn case of too many pages, try not using (-r) or putting another URL")
    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages")
    session_pages = 0
    index = 0
    for page in data.pages:
        if type(page) is SessionPage:
            session_pages += 1
        index += 1
    if session_pages != 0:
        print(f"\n{COLOR_MANAGER.BLUE}Pages that does not require login authorization: {len(data.pages) - session_pages}")
        print(f"{COLOR_MANAGER.ORANGE}Pages that requires login authorization: {session_pages}\n")
    else:
        print(f"\n{COLOR_MANAGER.BLUE}Number of pages: {len(data.pages)}\n")

