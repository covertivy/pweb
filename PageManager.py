from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import Data, SessionPage, Page
import requests
import mechanize
import http.cookiejar

already_printed = []
already_checked = []
troublesome = []
logout = []
logged_out = False


def get_pages(data: Data, curr_url: str, recursive=True, br: mechanize.Browser = None):
    """
    Function gets the lists of pages to the data object
    :param data: the data object of the program
    :param curr_url: the current URL the function checks
    :param recursive: True- check all website pages, False- only the first reachable one
    :param br: In case of session page, the br is important for the connection
    """
    if len(data.pages) == data.max_pages:
        # In case of specified amount of pages, the function will stop
        return

    global logged_out
    if logged_out or curr_url in logout:
        return

    if br:
        # Session page
        try:
            br.open(curr_url)
            br.reload()
            for p in data.pages:
                if p.url == br.geturl():
                    # Have the same URL
                    if type(p) is SessionPage:
                        # Redirected to another session page
                        already_checked.append(curr_url)  # No need to check
                        return
                    elif p.content == br.response().read().decode():
                        # It redirected to a non-session page, and have the same content
                        print(f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                              f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}")
                        logout.append(curr_url)
                        logged_out = True
                        return
                    else:
                        break
        except Exception as e:
            troublesome.append(curr_url)
            return
        page = SessionPage(br.geturl(), br.response().code, br.response().read().decode(), br.cookiejar)
        color = COLOR_MANAGER.ORANGE
    else:
        # Non-Session page
        try:
            res = requests.get(curr_url)
            # Creating a BeautifulSoup object
            page = Page(res.url, res.status_code, res.content.decode())
            color = COLOR_MANAGER.BLUE
            br = None  # Not to confuse the function
        except Exception as e:
            # Couldn't open with the session
            troublesome.append(curr_url)
            return

    if page.url != curr_url:
        # If the current URL is redirecting to another URL
        already_checked.append(curr_url)
        if br:
            # If session page
            res = requests.get(page.url)
            if res.url == page.url and "logout" in curr_url:
                # The session logged out
                print(f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                      f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}")
                logged_out = True
                logout.append(curr_url)
    """
    if not all(p.url != page.url for p in data.pages):
        # The new URL is already in the list
        if curr_url == "http://192.168.56.102:80/peruggia/index.php":
            print("aaa")
        already_checked.append(curr_url)
        return
"""
    try:
        # Beautiful soup
        soup = BeautifulSoup(page.content, "html.parser")
    except Exception as e:
        # Couldn't parse, might be non-html format, like pdf or docx
        troublesome.append(page.url)
        return

    if not any(page.url == printed_page.url and
               type(page) == type(printed_page) for printed_page in already_printed):
        # Printing the page
        print(f"\t[{color}+{COLOR_MANAGER.ENDC}] {color}{page.url}{COLOR_MANAGER.ENDC}")
        already_printed.append(page)
    # Adding to the page list
    data.pages.append(page)
    # Adding to the already-checked list
    already_checked.append(page.url)

    if recursive:
        # If the function is recursive
        # Getting every link in the page
        links = [urljoin(page.url, x.get("href")) for x in list(set(soup.find_all("a")))]
        links.sort()
        for link in links:
            if str(link).startswith(f"{str(data.url).split(':')[0]}:{str(data.url).split(':')[1]}"):
                # Only URLs that belongs to the website
                if all(link != page.url for page in data.pages):
                    # If the page is not in the page list
                    if link not in already_checked and link not in troublesome:
                        # Page was not checked
                        get_pages(data, link, data.recursive, br)


def get_login_pages(data: Data) -> list:
    login_pages = list()
    for page in data.pages:
        br = mechanize.Browser()
        br.set_cookiejar(http.cookiejar.CookieJar())
        try:
            br.open(page.url)  # Opening the URL
            br.select_form(nr=0)  # Attempting to log in
            br.form['username'] = data.username
            br.form['password'] = data.password
            br.submit()
            new_url = br.geturl()
            content = br.response().read()
            if all(new_url != p.url for p in data.pages):
                # If the new URL is not in list
                # It is also redirecting
                login_pages.append((page.url, new_url, br))
            else:
                # If the new URL is in the list
                for p in data.pages:
                    if new_url == p.url:
                        # Have the same URL
                        if content != p.content:
                            # Different content
                            login_pages.append((page.url, new_url, br))
                        break
        except Exception as e:
            pass
    return login_pages


def logic(data: Data):
    """
    Function gets the pages list
    """
    print(COLOR_MANAGER.BLUE + COLOR_MANAGER.HEADER + "Scraping pages:" + COLOR_MANAGER.ENDC)
    try:
        get_pages(data, data.url)
        global troublesome
        global already_checked
        # We need to clear them in case of session pages
        troublesome.clear()
        already_checked.clear()
    except Exception as e:
        raise ("Unknown problem occurred.\n"
              "\tIn case of too many pages, try putting another URL")

    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages")

    session_pages = 0
    if data.password and data.username:
        # If there are specified username and password
        login_pages = get_login_pages(data)
        global logged_out
        before_login_pages = list(data.pages)
        for origin, url, br in login_pages:
            # Attempting to log into every page
            while True:
                # Attempting to achieve data from page
                get_pages(data, url, br=br)
                if not logged_out:
                    # If the session has not encountered a logout page
                    break
                else:
                    # If the session has encountered a logout page
                    already_checked.clear()
                    data.pages = list(before_login_pages)  # Restoring the pages list
                    logged_out = False

                    br = mechanize.Browser()
                    br.set_cookiejar(http.cookiejar.CookieJar())
                    br.open(origin)  # Opening the origin of the current URL
                    br.select_form(nr=0)
                    br.form['username'] = data.username
                    br.form['password'] = data.password
                    br.submit()
        for page in data.pages:
            if type(page) is SessionPage:
                session_pages += 1

    if session_pages != 0:
        print(f"\n{COLOR_MANAGER.BLUE}Pages that does not require login authorization: {len(data.pages) - session_pages}")
        print(f"{COLOR_MANAGER.ORANGE}Pages that requires login authorization: {session_pages}\n")
    else:
        print(f"\n{COLOR_MANAGER.BLUE}Number of pages: {len(data.pages)}\n")
