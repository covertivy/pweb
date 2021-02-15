from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import *
import requests
from seleniumwire import webdriver
import sys
import os
import io
import zipfile

# Global variables
# Dictionary of the mime-types and their color (find values in the logic function)
type_colors = dict()
already_printed = []  # List of printed Pages/SessionPages
already_checked = []  # List of checked Pages/SessionPages
troublesome = []  # List of troublesome URLs
logout = []  # List of logout URLs
logged_out = False  # Logout flag
current_login_page = set()  # Where the session started
black_list = list()  # List of words that the user do not want to check
white_list = list()  # List of words that the user only wants to check

# Consts:
PADDING = 4


def get_links(links: list, url: str) -> list:
    """
    Function filters the links list
    @param links: The list of every link in the page
    @param url: The current URL
    @return: List of valid links
    """
    valid_links = list()
    for link in [urljoin(url, link) for link in links]:
        if str(link).replace("http://", "").replace("https://", "").startswith(
                f"{str(url).replace('http://', '').replace('https://', '').split(':')[0].split('/')[0]}"):
            # Only URLs that belongs to the website
            valid_links.append(link)
    valid_links = list(set(valid_links))
    valid_links.sort()  # Links list sorted in alphabetic order
    return valid_links


def get_login_form(data: Data, content: str) -> [dict]:
    """
    Function gets the login form of the page
    @param data: The data object of the program
    @param content: The current page content
    @return: Dictionary of the form details
    """
    forms = BeautifulSoup(content, "html.parser").find_all("form")  # Getting page forms
    for form in forms:
        try:
            # Get the form action (requested URL)
            action = form.attrs.get("action").lower()
            # Get the form method (POST, GET, DELETE, etc)
            # If not specified, GET is the default in HTML
            method = form.attrs.get("method", "get").lower()
            # Get all form inputs
            inputs = []
            login_input = [False, False]  # Check if the form is login form
            for input_tag in form.find_all("input"):
                # Get type of input form control
                input_type = input_tag.attrs.get("type", "text")
                # Get name attribute
                input_name = input_tag.attrs.get("name")
                value = ""  # The default value of the input
                if input_name:
                    # If there is an input name
                    if input_name.lower() == "username":
                        # Username input
                        value = data.username
                        login_input[0] = True
                    elif input_name.lower() == "password":
                        # Password input
                        value = data.password
                        login_input[1] = True
                # Get the default value of that input tag
                input_value = input_tag.attrs.get("value", value)
                # Add everything to that list
                input_dict = dict()
                if input_type:
                    input_dict["type"] = input_type
                if input_name:
                    input_dict["name"] = input_name
                input_dict["value"] = input_value
                inputs.append(input_dict)
            if login_input[0] and login_input[1]:
                # There both username and password in the form
                form_details = dict()
                form_details["action"] = action
                form_details["method"] = method
                form_details["inputs"] = inputs
                return form_details
        except Exception:
            continue
    return None


def valid_in_list(page: Page) -> bool:
    """
    Function checks if a page is valid by the black and white lists
    @param page: A page object
    @return: True - valid page, False - otherwise
    """
    # If there is a whitelist and the URL does not have any of the words
    # Or there is a black list and the URL have one of the words
    return not ((white_list and all(word not in page.url for word in white_list)) or
                (black_list and any(word in page.url for word in black_list)))


def get_pages(data: Data, curr_url: str, browser: webdriver.Chrome, previous: str,
              recursive=True, non_session_browser: webdriver.Chrome = None):
    """
    Function gets the list of pages to the data object
    @param data: The data object of the program
    @param curr_url: The current URL the function checks
    @param browser: The web driver that gets the rendered content
    @param previous: The previous page
    @param recursive: True- check all website pages, False- only the first reachable one
    @param non_session_browser: In case of session, we need another browser to tell us if it is indeed a session
    @return: None
    """
    if len(data.pages) == data.max_pages:
        # In case of specified amount of pages, the function will stop
        return

    global logged_out
    if logged_out or curr_url in logout:
        # Not open logout pages
        return

    try:
        # Trying to get the current URL
        browser.get(curr_url)
        request = None
        for req in browser.requests[::-1]:
            if req.url == browser.current_url:
                # If we found the right URL
                request = req
                if req.response.headers.get("Content-Type"):
                    # Only if the page has content type
                    break
        if not request:
            # Did not find the request
            raise Exception()  # The request is not found
        browser.refresh()
    except Exception:
        troublesome.append(curr_url)
        return

    if non_session_browser:
        # Session page
        try:
            same_content = False
            same_url = False
            for p in data.pages:
                if p.url.replace("https://", "http://") == \
                        browser.current_url.replace("https://", "http://"):
                    # Have the same URL (without the http://)
                    if type(p) is SessionPage:
                        # Redirected to another session page
                        troublesome.append(curr_url)  # No need to check
                        return
                    same_url = True
                if "html" in p.type and p.content == browser.page_source:
                    # Have the same content of another page
                    if type(p) is SessionPage:
                        # Redirected to another session page
                        troublesome.append(curr_url)  # No need to check
                        return
                    same_content = True
                if same_url or same_content:
                    # Already found what we were looking for
                    break
            if "logout" in curr_url.lower() or same_content:
                if not is_session_alive(data, browser):
                    # It redirected to a non-session page, and have the same content or logout in name
                    print(f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                          f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}")
                    logout.append(curr_url)
                    logged_out = True
                    return
                else:
                    browser.get(request.url)
            non_session_browser.get(browser.current_url)
            if non_session_browser.current_url == browser.current_url and \
                    non_session_browser.page_source == browser.page_source:
                # If the URL can be reachable from non-session point the session has logged out
                # Non-Session page
                page = Page(
                    browser.current_url,
                    request.response.status_code,
                    request.response.headers.get("Content-Type").split(";")[0],
                    browser.page_source,
                    request,
                    previous)
                color = COLOR_MANAGER.BLUE
            else:
                page = SessionPage(
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
    else:
        # Non-Session page
        page = Page(
            browser.current_url,
            request.response.status_code,
            request.response.headers.get("Content-Type").split(";")[0],
            browser.page_source,
            request,
            previous)
        color = COLOR_MANAGER.BLUE

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
        if not get_links([curr_url], page.url):
            # The Redirected link is out of the website
            return

    # Checking if the page was already printed
    in_list = False
    for printed_page in already_printed:
        if printed_page.url.replace("https://", "http://") == page.url.replace("https://", "http://") and\
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
    for pages in data.pages:
        if pages.url.replace("https://", "http://") == page.url.replace("https://", "http://") and\
                (pages.content == page.content or type(pages) == type(page)):
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

    if recursive:
        # If the function is recursive.
        # Getting every link in the page.
        links.extend(get_links([link.get("href") for link in soup.find_all("a")], page.url))

    for link in links:
        if logged_out or len(data.pages) == data.max_pages:
            # More efficient to check every time.
            # If the session logged out or the pages amount is at its maximum.
            return
        if all(link != page.url for page in data.pages) or non_session_browser:
            # If the page is not in the page list
            if (not any(link == checked_page.url for checked_page in already_checked)
                    and link not in troublesome):
                # Page was not checked, it is not troublesome or in the black list
                get_pages(data, link, browser, page.url,
                          recursive=data.recursive, non_session_browser=non_session_browser)


def get_session_pages(data: Data, browser: webdriver.Chrome):
    """
    Function looking for login forms and scraping session pages through them
    @param data: The data object of the program
    @param browser: The webdriver browser
    @return: None
    """
    if not (data.username and data.password):
        # If there are no username or password
        return
    non_session_pages = list(data.pages)
    non_session_browser = new_browser(data)  # New session for non-session page
    pages_backup = list(data.pages)
    login_pages = list()
    global logged_out
    for page in non_session_pages:
        if "html" not in page.type:
            continue
        # Setting browser for current page
        browser.get(page.url)
        form_details = get_login_form(data, browser.page_source)
        if not form_details:
            # The page doesn't have valid login form
            continue
        try:
            response = data.submit_form(form_details["inputs"], browser).response
            if not response:
                # Something went wrong in the form
                continue
        except Exception:
            continue
        new_url = browser.current_url
        content = browser.page_source
        if any(new_url == url for origin, url, form in login_pages):
            # The new url is already in the list
            continue
        if all(new_url != p.url for p in data.pages):
            # If the new URL is not in list
            # And it is also redirecting
            login_pages.append((page.url, new_url, form_details))
        else:
            # If the new URL is in the list
            for p in data.pages:
                if new_url == p.url:
                    # Have the same URL
                    if content != p.content:
                        # Different content
                        login_pages.append((page.url, new_url, form_details))
                    break
        # Starting session
        logged_out = True
        global current_login_page
        current_login_page = (page.url, form_details)
        while logged_out:
            # Until it won't encounter a logout page
            logged_out = False
            # Attempting to achieve data from page
            get_pages(data, new_url, browser, page.url, non_session_browser=non_session_browser)
            if logged_out:
                # If the session has encountered a logout page
                already_checked.clear()  # The function needs to go through all the session pages
                data.pages = list(pages_backup)  # Restoring the pages list
                browser.delete_all_cookies()
                browser.get(page.url)
                data.submit_form(form_details["inputs"], browser)  # Updating the session
                # Doing the loop all over again, without the logout page
        # If the session has not encountered a logout page
        pages_backup = list(data.pages)
    non_session_browser.close()  # Closing the webdriver


def is_session_alive(data: Data, browser: webdriver.Chrome) -> bool:
    """
    Function checks if the session of the browser is still alive
    @param data: The data object of the program
    @param browser: Chrome driver object
    @return: True - session still alive, False - session has logged out
    """
    same_content = 0
    different_content = 0
    for page in data.pages:
        if type(page) is SessionPage:
            browser.get(page.url)
            browser.refresh()
            if browser.page_source != page.content:
                # Does not have the same content
                different_content += 1
            else:
                # Have the same content
                same_content += 1
    # If there are more same-content pages than different-content pages
    return different_content <= same_content


def set_chromedriver(data: Data) -> webdriver.Chrome:
    """
    Function sets a browser web driver object
    @param data: The data object of the program
    @return: Chrome driver object
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
        return new_browser(data)
    except Exception:
        raise Exception("Setting up the web driver failed, please try again.")


def set_lists(data: Data):
    """
    Function sets the black and white lists
    @param data: The data object of the program
    @return: None
    """
    global white_list  # Required pages
    global black_list  # Block pages
    list_of_lists = [{"file": data.blacklist, "black": True},
                     {"file": data.whitelist, "black": False}]
    failed = False  # failed even once
    for dict_list in list_of_lists:
        if dict_list["file"]:
            if os.path.exists(dict_list["file"]):
                with open(dict_list["file"], "r") as f:
                    current_list = f.read()
            else:
                COLOR_MANAGER.print_error(f"The file {dict_list['file']} was not found", "\t")
                failed = True
                break
            try:
                current_list = [word for word in current_list.replace("\n", " ").replace(" ", "").split(",") if len(word)]
                if not len(current_list):
                    # Empty list
                    raise Exception("a")
                if dict_list["black"]:
                    black_list = current_list
                else:
                    white_list = current_list
            except Exception:
                failed = True
                COLOR_MANAGER.print_error(f"The file {dict_list['file']} is not in the"
                                            f" format of <word1>, <word2>.", "\t")
            else:
                COLOR_MANAGER.print_success(f"The file {dict_list['file']} has been"
                                            f" added to the filtering process.", "\t")
    if failed:
        # At least one of the specified lists is invalid
        COLOR_MANAGER.print_warning("The process will continue "
                                    "without the problematic list.", "\t")
    elif white_list and black_list:
        # The user specified valid data for both
        COLOR_MANAGER.print_warning("The process will filter"
                                    " the pages only by the white list.", "\t")
        black_list = list()  # Setting the black list to default
    print(COLOR_MANAGER.ENDC)


def logic(data: Data):
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
    # Setting white and black list
    set_lists(data)
    try:
        browser = set_chromedriver(data)  # Setting web browser driver
        print(COLOR_MANAGER.ENDC)
    except Exception as e:
        raise Exception(e, "\t")
    try:
        get_pages(data, data.url, browser, "")
        global already_checked
        # We need to clear them in case of session pages
        already_checked.clear()
    except Exception as e:
        raise Exception("Unknown problem occurred.", "\t")
    # In case of empty website
    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages", "\t")
    # Getting session pages
    get_session_pages(data, browser)
    # Printing the results
    print_result(data)
    # Transferring only the valid pages
    data.pages = [page for page in data.pages if valid_in_list(page)]
    browser.quit()


def print_result(data: Data):
    """
    Function prints the result of the web scraper
    @param data: The data object of the program
    @return: None
    """
    print("")
    if any(valid_in_list(page) and type(page) != SessionPage for page in data.pages):
        print(f"\t{COLOR_MANAGER.BLUE}Pages that does not require login authorization:{COLOR_MANAGER.ENDC}")
        print_types(data, Page)
    if any(valid_in_list(page) and type(page) == SessionPage for page in data.pages):
        # If there are session pages
        print(f"\t{COLOR_MANAGER.ORANGE}Pages that requires login authorization:{COLOR_MANAGER.ENDC}")
        print_types(data, SessionPage)
    if any(not valid_in_list(page) for page in data.pages):
        print(f"\t{COLOR_MANAGER.RED}Pages that are blocked from being checked:{COLOR_MANAGER.ENDC}")
        print_types(data)
    print(COLOR_MANAGER.ENDC)


def print_types(data: Data, page_type=None):
    """
    Function counts the different mime-types of pages
    @param data: The data object of the program
    @param page_type: Page or Session page, decides which page class to count
    @return: None
    """
    global type_colors
    type_count = dict()
    for key in type_colors.keys():
        type_count[key] = 0

    for page in data.pages:
        if (not page_type and not valid_in_list(page)) or \
                (type(page) == page_type and valid_in_list(page)):
            found = False
            for key in type_count.keys():
                if str(key).lower() in page.type:
                    type_count[key] += 1
                    found = True
            if not found:
                type_count["Other"] += 1

    if page_type == SessionPage:
        # Session page
        type_colors["HTML"] = COLOR_MANAGER.ORANGE
    else:
        type_colors["HTML"] = COLOR_MANAGER.BLUE
    for key in type_count.keys():
        if type_count[key] != 0:
            sign = "+"
            if not page_type:
                sign = "-"
            print_type(type_count[key], key, type_colors[key], sign)


def print_type(mime_type: int, name: str, color: str, sign: str):
    """
    Function print the page mime-type
    @param mime_type: The number of page of the mime-type
    @param name: The name of the mime-type
    @param color: The color of the print
    @param sign: The sign of the print
    @return: None
    """
    padding = " " * (PADDING - len(str(mime_type)))
    print(f"\t\t[{color}{sign}{COLOR_MANAGER.ENDC}]"
          f"{color} {mime_type}{padding}{name} pages{COLOR_MANAGER.ENDC}")
