from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import Data, SessionPage, Page
import requests
import mechanize
import http.cookiejar


TOO_MUCH_TIME = 8  # How many seconds of running is too much
login_pages = []  # List of (login URL, logged-in URL, the session)
already_printed = []  # List of printed Pages/SessionPages
already_checked = []  # List of checked Pages/SessionPages
troublesome = []  # List of troublesome URLs
logout = []  # List of logout URLs
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
        # Not open logout pages
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
                        print("lol")
                        # Redirected to another session page
                        troublesome.append(curr_url)  # No need to check
                        return
                    elif p.content == br.response().read().decode():
                        # It redirected to a non-session page, and have the same content
                        if "logout" in curr_url:
                            print(
                                f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                                f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}"
                            )
                            logout.append(curr_url)
                            logged_out = True
                        return
                    else:
                        break
            res = requests.get(br.geturl())
            if res.url == br.geturl() and "logout" in curr_url:
                # If the URL can be reachable from non-session point the session has logged out
                print(
                    f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                    f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}"
                )
                logged_out = True
                logout.append(curr_url)
                return
            page = SessionPage(
                br.geturl(),
                br.response().code,
                br.response().read().decode(),
                br.cookiejar,
            )
            color = COLOR_MANAGER.ORANGE
        except Exception as e:
            troublesome.append(curr_url)
            return
    else:
        # Non-Session page
        try:
            res = requests.get(curr_url)
            page = Page(res.url, res.status_code, res.content.decode())
            color = COLOR_MANAGER.BLUE
            br = None  # Not to confuse the function
        except Exception as e:
            # Couldn't open with the session
            troublesome.append(curr_url)
            return

    if page.url != curr_url:
        # If the current URL is redirecting to another URL
        troublesome.append(curr_url)

    try:
        # Creating a BeautifulSoup object
        soup = BeautifulSoup(page.content, "html.parser")
    except Exception as e:
        # Couldn't parse, might be non-html format, like pdf or docx
        troublesome.append(page.url)
        return

    if not any(
        page.url == printed_page.url and type(page) == type(printed_page)
        for printed_page in already_printed
    ):
        # Printing the page
        print(f"\t[{color}+{COLOR_MANAGER.ENDC}] {color}{page.url}{COLOR_MANAGER.ENDC}")
        already_printed.append(page)

    in_list = False
    for pages in data.pages:
        if pages.url == page.url and (
            pages.content == page.content or type(pages) == type(page)
        ):
            # Same URL and content or both session
            in_list = True
    if not in_list:
        # Adding to the page list
        data.pages.append(page)

    # Adding to the already-checked list
    already_checked.append(page)

    if recursive:
        # If the function is recursive
        # Getting every link in the page
        links = [
            urljoin(page.url, x.get("href")) for x in list(set(soup.find_all("a")))
        ]
        links.sort()
        for link in links:
            if len(data.pages) == data.max_pages:
                # We might reach the page limit while we check links, so we stop the for loop as well as individual recursions.
                return
            if logged_out:
                # More efficient to check every time
                return
            if str(link).startswith(
                f"{str(data.url).split(':')[0]}:{str(data.url).split(':')[1]}"
            ):
                # Only URLs that belongs to the website
                if all(link != page.url for page in data.pages) or br:
                    # If the page is not in the page list
                    if (
                        not any(
                            link == checked_page.url for checked_page in already_checked
                        )
                        and link not in troublesome
                    ):
                        # Page was not checked
                        get_pages(data, link, data.recursive, br)

    if not br:
        # If not session page
        br = mechanize.Browser()
        br.set_cookiejar(http.cookiejar.CookieJar())
        try:
            br.open(page.url)  # Opening the URL
            br.select_form(nr=0)  # Attempting to log in
            br.form["username"] = data.username
            br.form["password"] = data.password
            br.submit()
            new_url = br.geturl()
            content = br.response().read()
            if any(new_url == url for origin, url, br in login_pages):
                # The new url is already in the list
                return
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


def logic(data: Data):
    """
    Function gets the pages list
    """
    print(
        COLOR_MANAGER.BLUE
        + COLOR_MANAGER.HEADER
        + "Scraping pages:"
        + COLOR_MANAGER.ENDC
    )
    try:
        get_pages(data, data.url)
        global already_checked
        # We need to clear them in case of session pages
        already_checked.clear()
    except Exception as e:
        raise (
            "Unknown problem occurred.\n"
            "\tIn case of too many pages, try putting another URL"
        )

    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages")

    session_pages = 0
    if len(login_pages):
        # If there are specified username and password
        # login_pages = get_login_pages(data)
        global logged_out
        pages_backup = list(data.pages)
        for origin, url, br in login_pages:
            # Check every login page
            logged_out = True
            while logged_out:
                # Until it won't encounter a logout page
                logged_out = False
                get_pages(data, url, br=br)  # Attempting to achieve data from page
                if logged_out:
                    # If the session has encountered a logout page
                    already_checked.clear()  # The function needs to go through all the session pages
                    data.pages = list(pages_backup)  # Restoring the pages list

                    br = mechanize.Browser()  # Creating new session
                    br.set_cookiejar(http.cookiejar.CookieJar())
                    br.open(origin)  # Opening the origin of the current URL
                    br.select_form(nr=0)
                    br.form["username"] = data.username
                    br.form["password"] = data.password
                    br.submit()
                    # Making the loop all over again, without the logout page
            # If the session has not encountered a logout page
            pages_backup = list(data.pages)
        # Counting the session pages
        for page in data.pages:
            if type(page) is SessionPage:
                session_pages += 1

    if session_pages != 0:
        print(
            f"\n{COLOR_MANAGER.BLUE}Pages that does not require login authorization: {len(data.pages) - session_pages}"
        )
        print(
            f"{COLOR_MANAGER.ORANGE}Pages that requires login authorization: {session_pages}\n"
        )
    else:
        print(f"\n{COLOR_MANAGER.BLUE}Number of pages: {len(data.pages)}\n")
