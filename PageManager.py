from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colors import COLOR_MANAGER
import Classes
import Methods
import requests
from seleniumwire import webdriver
import sys
import os
import io
import zipfile

# -------------------------- Global variables ---------------------------+
type_colors = dict()  # Dictionary of the mime-types and their color.    |
# See values in the logic() function.                                    |
# -------------- Pages lists ----------------------------------+---------+
already_printed = list()  # List of printed Pages/SessionPages.|         |
already_checked = list()  # List of checked Pages/SessionPages.|         |
troublesome = list()  # List of troublesome URLs.              |         |
# -------------- Session variables -----------------------+----+         |
non_session_browser = list()  # [0] is None or browser.   |              |
# It is a list because it can be None or browser.         |              |
logout_list = list()  # List of logout URLs.              |              |
logged_out = False  # Logout flag.                        |              |
logged_in = False  # If set, we made a login act          |              |
current_login_page = set()  # Where the session started.  |              |
# --------------- Word lists -----------------------------+--------------+
black_list = list()  # List of words that the user do not want to check. |
white_list = list()  # List of words that the user only wants to check.  |
# -----------------------------------------------------------------------+

# ------ Consts ---------+
PADDING = 4  # Spaces.   |
# -----------------------+


def get_links(links: list, url: str) -> list:
    """
    Function returns a filtered list of links that not equal to the current URL but have same domain.
    @param links: The list of every link in the page
    @param url: The current URL
    @return: List of valid links
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


def get_login_form(data: Classes.Data, forms: list) -> dict:
    """
    Function gets the login form of the page
    @param data: The data object of the program
    @param forms: The list of the forms of the page
    @return: Dictionary of the form details
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


def valid_in_list(page: Classes.Page) -> bool:
    """
    Function checks if a page is valid by the black and white lists
    @param page: A page object
    @return: True - valid page, False - otherwise
    """
    # If there is a white list and the URL does not have any of the words
    # Or there is a black list and the URL have one of the words
    return not ((white_list and all(word not in page.url for word in white_list)) or
                (black_list and any(word in page.url for word in black_list)))


def is_session_alive(data: Classes.Data, browser: webdriver.Chrome) -> bool:
    """
    Function checks if the session of the browser is still alive
    @param data: The data object of the program
    @param browser: Chrome driver object
    @return: True - session still alive, False - session has logged out
    """
    same_content = 0
    different_content = 0
    for session_page in [page for page in data.pages if type(page) is Classes.SessionPage]:
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


def get_pages(data: Classes.Data, curr_url: str, browser: webdriver.Chrome,
              previous, recursive=True):
    """
    Function gets the list of pages to the data object
    @param data: The data object of the program
    @param curr_url: The current URL the function checks
    @param browser: The web driver that gets the rendered content
    @param previous: The previous page
    @param recursive: True - check all website pages, False - only the first reachable one
    @return: None
    """
    if len(data.pages) == data.max_pages:
        # In case of specified amount of pages, the function will stop
        return

    if curr_url in logout_list:
        # Do not open logout pages
        return

    global logged_out
    global logged_in
    global non_session_browser
    if logged_out:
        # If the session already logged out
        if non_session_browser[0]:
            # Remove non session browser
            non_session_browser[0].quit()
            non_session_browser[0] = None
        if logged_in:
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
        browser.refresh()
    except Exception:
        troublesome.append(curr_url)
        return

    page = Classes.Page(
        browser.current_url,
        request.response.status_code,
        request.response.headers.get("Content-Type").split(";")[0],
        browser.page_source,
        request,
        previous)
    color = COLOR_MANAGER.BLUE

    if non_session_browser[0]:
        # Session page
        try:
            same_content = False
            same_url = False
            a_page = None
            for a_page in data.pages:
                if not get_links([a_page.url], browser.current_url):
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
                if not is_session_alive(data, browser):
                    # It redirected to a non-session page, and have the same content or logout in name
                    print(f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                          f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}")
                    logout_list.append(curr_url)
                    logged_out = True
                    if not logged_in:
                        # In case of cookies (-c), the logout action makes the cookies invalid
                        removed_list = list()
                        for page in data.pages:
                            if type(page) is not Classes.SessionPage:
                                removed_list.append(page)
                        data.pages = removed_list
                        print(f"\t[{COLOR_MANAGER.RED}!{COLOR_MANAGER.ENDC}]"
                              f" {COLOR_MANAGER.RED}Cookies are invalid anymore,"
                              f" all session pages were removed.{COLOR_MANAGER.ENDC}")
                        browser.delete_all_cookies()
                    return
                else:
                    browser.get(request.url)
            if same_content and same_url and type(a_page) is Classes.SessionPage:
                # Redirected to another session page with the same URL or content
                troublesome.append(curr_url)  # No need to check
                return
            non_session_browser[0].get(browser.current_url)
            if non_session_browser[0].current_url != browser.current_url or \
                    Methods.remove_forms(non_session_browser[0].page_source) !=\
                    Methods.remove_forms(browser.page_source):
                # If the URL can be reachable from non-session point the session has logged out
                # Session page
                page = Classes.SessionPage(
                    browser.current_url,
                    request.response.status_code,
                    request.response.headers.get("Content-Type").split(";")[0],
                    browser.page_source,
                    browser.get_cookies(),
                    current_login_page,
                    request,
                    previous)
                color = COLOR_MANAGER.ORANGE
        except Exception:
            troublesome.append(curr_url)
            return

    soup = None
    if "html" in page.type:
        # Only if the page is html
        try:
            # Creating a BeautifulSoup object
            soup = BeautifulSoup(page.content, "html.parser")
        except Exception as e:
            # Couldn't parse, might be non-html format, like pdf or docx
            troublesome.append(page.url)
            return
    if page.url != curr_url:
        # If the current URL is redirecting to another URL
        troublesome.append(curr_url)
        if previous and not get_links([previous.url], page.url):
            # The Redirected link is out of the website
            return

    # Checking if the page was already printed
    in_list = False
    for printed_page in already_printed:
        if not get_links([printed_page.url], page.url) and\
                (printed_page.content == page.content or type(printed_page) == type(page)):
            # Same URL (without the http://) and content or both are session
            in_list = True
    if not in_list:
        # If the page was not printed
        if not soup:
            # If it is a non-html page
            color = type_colors["Other"]
            for key in type_colors.keys():
                if str(key).lower() in page.type:
                    color = type_colors[key]
                    break
        # Printing the page
        sign = "+"
        if not valid_in_list(page):
            sign = "-"  # Sign of not checking
        print(f"\t[{color}{sign}{COLOR_MANAGER.ENDC}] {color}{page.url}{COLOR_MANAGER.ENDC}")
        already_printed.append(page)

    # Checking if the page was already checked
    in_list = False
    for a_page in data.pages:
        if not get_links([a_page.url], page.url) and\
                (a_page.content == page.content or type(a_page) == type(page)):
            # Same URL (without the http://) and (content or both are session)
            in_list = True
    if not in_list:
        # Adding to the page list
        data.pages.append(page)

    # Adding to the already-checked list.
    already_checked.append(page)

    if not soup:
        # There is no reason check non-html page.
        return

    # Getting every application script in the page.
    links = get_links([script.get("src") for script in soup.find_all("script")], page.url)

    # Getting every css style in the page.
    links.extend(get_links([script.get("href") for script in soup.find_all(type="text/css")], page.url))

    for link in links:
        # Checking only scripts and style file
        for req in browser.requests:
            if link == req.url:
                # Were already requested with the current page
                get_pages(data, link, browser, page,
                          recursive=data.recursive)
                links.remove(link)
                break

    del browser.requests  # We do not need the previous requests anymore

    if recursive:
        # If the function is recursive.
        # Getting every link in the page.
        links.extend(get_links([link.get("href") for link in soup.find_all("a")], page.url))

    for link in links:
        if (logged_out and logged_in) or len(data.pages) == data.max_pages:
            # More efficient to check every time.
            # If the session logged out or the pages amount is at its maximum.
            return
        if all(link != page.url for page in data.pages) or non_session_browser[0]:
            # If the page is not in the page list
            if (not any(link == checked_page.url for checked_page in already_checked)
                    and link not in troublesome):
                # Page was not checked, it is not troublesome or in the black list
                get_pages(data, link, browser, page, recursive=data.recursive)


def get_session_pages(data: Classes.Data, browser: webdriver.Chrome):
    """
    Function looking for login forms and scraping session pages through them
    @param data: The data object of the program
    @param browser: The webdriver browser
    @return: None
    """
    if not (data.username and data.password):
        # If there are no username or password
        return
    global non_session_browser
    if not non_session_browser[0]:
        # If the instance is not already set, set up a new one
        non_session_browser[0] = Methods.new_browser(data)

    non_session_pages = list(data.pages)
    pages_backup = list(data.pages)
    login_pages = list()

    for page in non_session_pages:
        if "html" not in page.type:
            continue
        # Checking if the page has a login form
        if not get_login_form(data, Methods.get_forms(page.content)):
            continue
        # Setting browser for current page
        browser.get(page.url)
        # Getting updated form
        form_details = get_login_form(data, Methods.get_forms(browser.page_source))
        try:
            Methods.submit_form(form_details["inputs"], browser, data)
        except Exception:
            continue
        new_url = browser.current_url
        content = browser.page_source
        if any(new_url == url for origin, url, form in login_pages):
            # The new url is already in the list
            continue
        login = True
        for p in data.pages:
            if new_url == p.url:
                # Have the same URL
                if Methods.remove_forms(content) != Methods.remove_forms(p.content):
                    # Different content
                    login_pages.append((page.url, new_url, form_details))
                else:
                    login = False  # Same URL and content
                break  # We do not need to check anymore
        if not login:
            continue

        # Setting login flags
        global logged_out
        global logged_in
        logged_out = True
        logged_in = True

        global current_login_page
        current_login_page = (page.url, form_details)
        while logged_out:
            # Until it won't encounter a logout page
            logged_out = False
            # Attempting to achieve data from page
            get_pages(data, new_url, browser, page)
            if logged_out:
                # If the session has encountered a logout page
                already_checked.clear()  # The function needs to go through all the session pages
                for checked_page in data.pages:
                    if "html" not in checked_page.type and checked_page not in pages_backup:
                        pages_backup.append(checked_page)
                        already_checked.append(checked_page)
                data.pages = list(pages_backup)  # Restoring the pages list
                # Updating the session
                browser.delete_all_cookies()
                browser.get(page.url)
                Methods.enter_cookies(data, browser, page.url)
                Methods.submit_form(form_details["inputs"], browser, data)
                # Doing the loop all over again, without the logout page
        break
    # Closing the non session browser
    non_session_browser[0].quit()


def set_chromedriver(data: Classes.Data):
    """
    Function sets a browser web driver object
    @param data: The data object of the program
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


def set_lists(data: Classes.Data):
    """
    Function sets the black and white lists
    @param data: The data object of the program
    @return: None
    """
    def set_list(file: str, black: bool):
        global white_list  # Required pages
        global black_list  # Block pages
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
                black_list = current_list
            else:
                white_list = current_list
        else:
            # Empty file
            COLOR_MANAGER.print_error(f"The file {file} is not in the"
                                      f" format of <word1>, <word2>.", "\t")
    set_list(data.blacklist, True)  # Setting black list
    set_list(data.whitelist, False)  # Setting white list
    global white_list  # Required pages
    global black_list  # Block pages
    if white_list and black_list:
        # The user specified valid data for both
        COLOR_MANAGER.print_warning("The process will filter"
                                    " the pages only by the white list.", "\t")
        black_list = list()  # Setting the black list to default
    print(COLOR_MANAGER.ENDC)


def set_cookies(data: Classes.Data, browser: webdriver.Chrome):
    """
    Function sets the specified cookies
    @param data: The data object of the program
    @param browser: The webdriver browser
    @return: None
    """
    if data.cookies:
        # If user specified cookies
        if Methods.enter_cookies(data, browser, data.url):
            # Success
            non_session_browser[0] = Methods.new_browser(data)  # setting up secondary browser object
            print(f"\t[{COLOR_MANAGER.YELLOW}!{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.YELLOW}"
                  f"Cookies were added to the session.{COLOR_MANAGER.ENDC}")
        else:
            # Failure
            print(f"\t[{COLOR_MANAGER.YELLOW}!{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.YELLOW}"
                  f"Invalid cookies, check your syntax and try again. {COLOR_MANAGER.ENDC}")
            data.cookies = None  # There is no need to use them again


def logic(data: Classes.Data):
    """
    Function gets the page list
    @param data: The data object of the program
    @return: None
    """
    global type_colors
    type_colors = {
        "HTML": None,  # The session is the one that decides
        "Javascript": COLOR_MANAGER.GREEN,
        "CSS": COLOR_MANAGER.PINK,
        "XML": COLOR_MANAGER.YELLOW,
        "Other": COLOR_MANAGER.PURPLE}  # Dictionary of the mime-types and their color
    print(f"{COLOR_MANAGER.BLUE + COLOR_MANAGER.HEADER}Scraping pages:{COLOR_MANAGER.ENDC}")
    # Setting environment
    global non_session_browser
    non_session_browser = list()
    non_session_browser.append(None)
    try:
        set_lists(data)  # Setting white and black list
        set_chromedriver(data)  # Setting web browser driver
        browser = Methods.new_browser(data)  # Setting up browser object
        set_cookies(data, browser)  # Setting up specified cookies
        print(COLOR_MANAGER.ENDC)
    except Exception as e:
        raise Exception(e, "\t")
    try:
        # Getting the pages
        get_pages(data, data.url, browser, None)
        # We need to clear them in case of session pages
        global already_checked
        already_checked.clear()
    except Exception as e:
        raise Exception("Unknown problem occurred.", "\t")
    # In case of empty website
    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages", "\t")
    # Getting the session pages
    get_session_pages(data, browser)
    # Printing the results
    print_result(data)
    # Transferring only the valid pages
    data.pages = [page for page in data.pages if valid_in_list(page)]
    browser.quit()


def print_result(data: Classes.Data):
    """
    Function prints the result of the web scraper
    @param data: The data object of the program
    @return: None
    """
    def print_type(pages: list, sign: str):
        type_count = dict()
        for key in type_colors.keys():
            type_count[key] = 0  # Initiating the dictionary {"mime type": count}
        for page in pages:
            found = False
            for key in type_count.keys():
                if str(key).lower() in page.type:
                    type_count[key] += 1
                    found = True
            if not found:
                type_count["Other"] += 1
        for key in type_count:
            if type_count[key]:
                padding = " " * (PADDING - len(str(type_count[key])))
                print(f"\t\t[{type_colors[key]}{sign}{COLOR_MANAGER.ENDC}]"
                      f"{type_colors[key]} {type_count[key]}{padding}{key} pages{COLOR_MANAGER.ENDC}")

    global type_colors
    print("")
    non_session_pages = [page for page in data.pages
                         if valid_in_list(page) and type(page) != Classes.SessionPage]
    if non_session_pages:
        print(f"\t{COLOR_MANAGER.BLUE}Pages that does not require login authorization:{COLOR_MANAGER.ENDC}")
        type_colors["HTML"] = COLOR_MANAGER.BLUE
        print_type(non_session_pages, "+")
    session_pages = [page for page in data.pages
                     if valid_in_list(page) and type(page) == Classes.SessionPage]
    if session_pages:
        # If there are session pages
        print(f"\t{COLOR_MANAGER.ORANGE}Pages that requires login authorization:{COLOR_MANAGER.ENDC}")
        type_colors["HTML"] = COLOR_MANAGER.ORANGE
        print_type(session_pages, "+")
    not_included = [page for page in data.pages if not valid_in_list(page)]
    if not_included:
        print(f"\t{COLOR_MANAGER.RED}Pages that are blocked from being checked:{COLOR_MANAGER.ENDC}")
        print_type(not_included, "-")
    print(COLOR_MANAGER.ENDC)
