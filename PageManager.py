from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import Data, SessionPage, Page
import requests
import requests.utils
import http.cookiejar
from selenium import webdriver
import platform
import os
import io
import zipfile

# Global variables
# Dictionary of the mime-types and their color (find values in the logic function)
type_colors = dict()
# List of (login URL, logged-in URL, the session, login-form of the login URL)
login_pages = []
already_printed = []  # List of printed Pages/SessionPages
already_checked = []  # List of checked Pages/SessionPages
troublesome = []  # List of troublesome URLs
logout = []  # List of logout URLs
logged_out = False  # Logout flag
current_login_page = set()  # Where the session started
black_list = list()  # List of words that the user do not want to check

# Consts:
PADDING = 4
CHROME_DRIVERS = {
    "windows": "https://chromedriver.storage.googleapis.com/86.0.4240.22/chromedriver_win32.zip",
    "darwin": "https://chromedriver.storage.googleapis.com/86.0.4240.22/chromedriver_mac64.zip",
    "linux": "https://chromedriver.storage.googleapis.com/86.0.4240.22/chromedriver_linux64.zip",
}


def get_links(links: list, url: str) -> list:
    """
    Function filters the links list
    @param links: The list of every link in the page
    @param url: The current URL
    @return: List of valid links
    """
    valid_links = list()
    for link in [urljoin(url, link) for link in links]:
        if str(link).startswith(
            f"http://{str(url).replace('http://', '').split(':')[0].split('/')[0]}"
        ):
            # Only URLs that belongs to the website
            valid_links.append(link)
    valid_links = list(set(valid_links))
    valid_links.sort()  # Links list sorted in alphabetic order
    return valid_links


def get_login_form(data: Data, url: str) -> (dict, requests.Session):
    """
    Function gets the login form of the page
    @param data: The data object of the program
    @param url: The current URL
    @return: Dictionary of the form details, The session of the request
    """
    session = requests.session()
    session.cookies = http.cookiejar.CookieJar()
    res = session.get(url)  # Opening the URL
    forms = BeautifulSoup(res.content.decode(), "html.parser").find_all(
        "form"
    )  # Getting page forms
    for form in forms:
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
            return form_details, session
    return None, None


def submit_form(
    form_details: dict, url: str, session: requests.Session
) -> requests.Response:
    """
    Function submits the login form
    @param form_details: Dictionary of the form details
    @param url: The current URL
    @param session: The session of the request
    @return: The response of the login request
    """
    # Join the url with the action (form request URL)
    action_url = urljoin(url, form_details["action"])  # Getting action URL
    # The arguments body we want to submit
    args = dict()
    for input_tag in form_details["inputs"]:
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            args[input_tag["name"]] = input_tag["value"]
    # Sending the request
    if form_details["method"] == "post":
        return session.post(action_url, data=args)
    elif form_details["method"] == "get":
        return session.get(action_url, params=args)
    return requests.Response()


def get_pages(
    data: Data,
    curr_url: str,
    browser: webdriver.Chrome,
    recursive=True,
    session: requests.Session = None,
):
    """
    Function gets the lists of pages to the data object
    @param data: The data object of the program
    @param curr_url: The current URL the function checks
    @param browser:
    @param recursive: True- check all website pages, False- only the first reachable one
    @param session: In case of session page, the session is important for the connection
    @return: None
    """
    if len(data.pages) == data.max_pages:
        # In case of specified amount of pages, the function will stop
        return

    global logged_out
    if logged_out or curr_url in logout:
        # Not open logout pages
        return

    if session:
        # Session page
        try:
            res = session.get(curr_url)
            for p in data.pages:
                if p.url == res.url:
                    # Have the same URL
                    if type(p) is SessionPage:
                        # Redirected to another session page
                        troublesome.append(curr_url)  # No need to check
                        return
                    elif p.content == res.content.decode():
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
            req = requests.get(res.url)
            if req.url == res.url and "logout" in curr_url:
                # If the URL can be reachable from non-session point the session has logged out
                print(
                    f"\t[{COLOR_MANAGER.RED}-{COLOR_MANAGER.ENDC}]"
                    f" {COLOR_MANAGER.RED}{curr_url}{COLOR_MANAGER.ENDC}"
                )
                logged_out = True
                logout.append(curr_url)
                return
        except Exception as e:
            troublesome.append(curr_url)
            return
        else:
            page = SessionPage(
                res.url,
                res.status_code,
                res.headers.get("Content-Type").split(";")[0],
                res.content.decode(),
                session.cookies,
                current_login_page,
            )
            color = COLOR_MANAGER.ORANGE
    else:
        # Non-Session page
        try:
            res = requests.get(curr_url)
            page = Page(
                res.url,
                res.status_code,
                res.headers.get("Content-Type").split(";")[0],
                res.content.decode(),
            )
            color = COLOR_MANAGER.BLUE
        except Exception as e:
            # Couldn't open with the session
            troublesome.append(curr_url)
            return

    soup = None
    if "html" in page.type:
        # Only if the page is html
        try:
            # Rendering page
            if type(page) == SessionPage:
                # Setting cookies
                cookies = requests.utils.dict_from_cookiejar(page.cookies)
                for key in cookies.keys():
                    browser.add_cookie({"name": key, "value": cookies[key]})
            browser.get(page.url)
            page.url = browser.current_url  # Rendered URL
            page.content = browser.page_source  # Rendered content
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
        if printed_page.url == page.url and (
            printed_page.content == page.content or type(printed_page) == type(page)
        ):
            # Same URL and content or both are session
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
        print(f"\t[{color}+{COLOR_MANAGER.ENDC}] {color}{page.url}{COLOR_MANAGER.ENDC}")
        already_printed.append(page)

    # Checking if the page was already checked
    in_list = False
    for pages in data.pages:
        if pages.url == page.url and (
            pages.content == page.content or type(pages) == type(page)
        ):
            # Same URL and content or both are session
            in_list = True
    if not in_list:
        # Adding to the page list
        data.pages.append(page)

    # Adding to the already-checked list
    already_checked.append(page)

    if not soup:
        # There is no reason check non-html page
        return

    # Getting every application script in the page
    links = get_links(
        [script.get("src") for script in soup.find_all("script")], page.url
    )

    # Getting every css style in the page
    links.extend(
        get_links(
            [script.get("href") for script in soup.find_all(type="text/css")], page.url
        )
    )

    if recursive:
        # If the function is recursive
        # Getting every link in the page
        links.extend(
            get_links([link.get("href") for link in soup.find_all("a")], page.url)
        )

    for link in links:
        if logged_out or len(data.pages) == data.max_pages:
            # More efficient to check every time
            # If the session logged out or the pages amount is at its maximum
            return
        if all(link != page.url for page in data.pages) or session:
            # If the page is not in the page list
            if (
                not any(link == checked_page.url for checked_page in already_checked)
                and link not in troublesome
                and all(word not in link for word in black_list)
            ):
                # Page was not checked
                get_pages(data, link, browser, data.recursive, session)

    if not session and data.username and data.password:
        # If not session page and there are username and password specified
        try:
            form_details, session = get_login_form(data, page.url)
            if not form_details:
                # The page doesn't have valid login form
                return
            res = submit_form(form_details, page.url, session)
            if not res:
                # Something went wrong in the form
                return
            new_url = res.url
            content = res.content.decode()
            if any(new_url == url for origin, url, ses, form in login_pages):
                # The new url is already in the list
                return
            if all(new_url != p.url for p in data.pages):
                # If the new URL is not in list
                # It is also redirecting
                login_pages.append((page.url, new_url, session, form_details))
            else:
                # If the new URL is in the list
                for p in data.pages:
                    if new_url == p.url:
                        # Have the same URL
                        if content != p.content:
                            # Different content
                            login_pages.append(
                                (page.url, new_url, session, form_details)
                            )
                        break
        except Exception as e:
            pass


def chromedriver():
    operating_system = platform.system().lower()
    driver_file = "chromedriver"
    if operating_system == "windows":
        driver_file = "chromedriver.exe"
    if driver_file not in os.listdir("."):
        # Getting zip file
        print(
            f"\t[{COLOR_MANAGER.YELLOW}?{COLOR_MANAGER.ENDC}] {COLOR_MANAGER.YELLOW}"
            f"Downloading Chromedriver...{COLOR_MANAGER.ENDC}"
        )
        try:
            zip_content = io.BytesIO(
                requests.get(CHROME_DRIVERS[operating_system]).content
            )
            with zipfile.ZipFile(zip_content) as zip_ref:
                # Extracting the executable file
                zip_ref.extractall(".")
        except Exception:
            raise Exception("Download failed, please check your internet connection.")
    # There is a chromedriver in the folder
    driver_file = os.getcwd() + "\\" + driver_file  # Full path
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")
        options.add_argument("headless")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        browser = webdriver.Chrome(executable_path=driver_file, options=options)
        return browser
    except Exception:
        raise Exception("Setting up the web driver failed, please try again.")


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
        "Other": COLOR_MANAGER.PURPLE,
    }  # Dictionary of the mime-types and their color
    print(
        COLOR_MANAGER.BLUE
        + COLOR_MANAGER.HEADER
        + "Scraping pages:"
        + COLOR_MANAGER.ENDC
    )
    # Block pages
    if data.blacklist:
        try:
            global black_list
            file = open("blacklist.txt", "r")
            black_list = file.read()
            file.close()
            black_list = [word.replace(" ", "") for word in black_list.split(",")]
        except Exception as e:
            COLOR_MANAGER.print_error(
                "The file blacklist.txt was not found\n"
                "\tOr was not in the right format <word1>,<word2>",
                "\t",
            )
    try:
        browser = chromedriver()  # Setting web browser driver
    except Exception as e:
        raise Exception(e, "\t")
    try:
        get_pages(data, data.url, browser)
        global already_checked
        # We need to clear them in case of session pages
        already_checked.clear()
    except Exception as e:
        raise Exception("Unknown problem occurred.", "\t")

    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages", "\t")

    session_pages = 0
    if len(login_pages):
        # If there are specified username and password
        global logged_out
        global current_login_page
        pages_backup = list(data.pages)
        for origin, url, session, form in login_pages:
            # Check every login page
            logged_out = True
            current_login_page = (origin, form)
            while logged_out:
                # Until it won't encounter a logout page
                logged_out = False
                get_pages(
                    data, url, browser, session=session
                )  # Attempting to achieve data from page
                if logged_out:
                    # If the session has encountered a logout page
                    already_checked.clear()  # The function needs to go through all the session pages
                    data.pages = list(pages_backup)  # Restoring the pages list
                    form_details, session = get_login_form(
                        data, origin
                    )  # Getting new session
                    submit_form(form_details, origin, session)  # Updating the session
                    browser.get(origin)  # Setting browser to current page
                    # Doing the loop all over again, without the logout page
            # If the session has not encountered a logout page
            pages_backup = list(data.pages)
        # Counting the session pages
        for page in data.pages:
            if type(page) is SessionPage:
                session_pages += 1
    print_result(data, session_pages)
    browser.close()


def print_result(data: Data, session_pages: int):
    """
    Function prints the result of the web scraper
    @param data: The data object of the program
    @param session_pages: The number of session pages
    @return: None
    """
    print(
        f"\n\t{COLOR_MANAGER.BLUE}Pages that does not require login authorization:{COLOR_MANAGER.ENDC}"
    )
    print_types(data, Page)
    if session_pages != 0:
        # If there are session pages
        print(
            f"\t{COLOR_MANAGER.ORANGE}Pages that requires login authorization:{COLOR_MANAGER.ENDC}"
        )
        print_types(data, SessionPage)
    print(COLOR_MANAGER.ENDC)


def print_types(data: Data, page_type):
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
        if type(page) == page_type:
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
            print_type(type_count[key], key, type_colors[key])


def print_type(mime_type: int, name: str, color: str):
    """
    Function print the page mime-type
    @param mime_type: The number of page of the mime-type
    @param name: The name of the mime-type
    @param color: The color of the print
    @return: None
    """
    padding = " " * (PADDING - len(str(mime_type)))
    print(
        f"\t\t[{color}+{COLOR_MANAGER.ENDC}]"
        f"{color} {mime_type}{padding}{name} pages{COLOR_MANAGER.ENDC}"
    )
