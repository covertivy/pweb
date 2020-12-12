from bs4 import BeautifulSoup
from urllib.parse import urljoin
from colors import COLOR_MANAGER
from Data import Data, SessionPage, Page
import requests
import http.cookiejar


login_pages = []  # List of (login URL, logged-in URL, the session)
already_printed = []  # List of printed Pages/SessionPages
already_checked = []  # List of checked Pages/SessionPages
troublesome = []  # List of troublesome URLs
logout = []  # List of logout URLs
logged_out = False


def get_links(links: list, url: str) -> list:
    valid_links = list()
    for link in [urljoin(url, link) for link in links]:
        if str(link).startswith(f"{str(url).split(':')[0]}:{str(url).split(':')[1]}"):
            # Only URLs that belongs to the website
            valid_links.append(link)
    valid_links.sort()  # Links list sorted in alphabetic order
    return valid_links


def get_login_form(data: Data, url: str):
    session = requests.session()
    session.cookies = http.cookiejar.CookieJar()
    res = session.get(url)  # Opening the URL
    forms = BeautifulSoup(res.content.decode(), "html.parser").find_all("form")  # Getting page forms
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
            inputs.append({"type": input_type, "name": input_name, "value": input_value})
        if login_input[0] and login_input[1]:
            # There both username and password in the form
            form_details = dict()
            form_details["action"] = action
            form_details["method"] = method
            form_details["inputs"] = inputs
            return form_details, session
    return None, None


def submit_form(form_details: dict, url: str, session: requests.Session):
    # Join the url with the action (form request URL)
    action_url = urljoin(url, form_details["action"])  # Getting action URL
    # The arguments body we want to submit
    args = dict()
    for input_tag in form_details["inputs"]:
        # Using the specified value
        args[input_tag["name"]] = input_tag["value"]
    # Sending the request
    if form_details["method"] == "post":
        return session.post(action_url, data=args)
    elif form_details["method"] == "get":
        return session.get(action_url, params=args)
    return None


def get_pages(data: Data, curr_url: str, recursive=True, session: requests.Session = None):
    """
    Function gets the lists of pages to the data object
    :param data: the data object of the program
    :param curr_url: the current URL the function checks
    :param recursive: True- check all website pages, False- only the first reachable one
    :param session: In case of session page, the br is important for the connection
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
            page = SessionPage(res.url, res.status_code, res.headers.get("Content-Type").split(";")[0],
                               res.content.decode(), session.cookies)
            color = COLOR_MANAGER.ORANGE
    else:
        # Non-Session page
        try:
            res = requests.get(curr_url)
            page = Page(res.url, res.status_code, res.headers.get("Content-Type").split(";")[0],
                        res.content.decode())
            color = COLOR_MANAGER.BLUE
        except Exception as e:
            # Couldn't open with the session
            troublesome.append(curr_url)
            return

    if page.url != curr_url:
        # If the current URL is redirecting to another URL
        troublesome.append(curr_url)

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

    if not any(page.url == printed_page.url and type(page) == type(printed_page)
               for printed_page in already_printed):
        # If the page was not printed
        if not soup:
            # If it is a non-html page
            if "css" in page.type:
                color = COLOR_MANAGER.PINK
            if "application" in page.type:
                color = COLOR_MANAGER.GREEN
        # Printing the page
        print(f"\t[{color}+{COLOR_MANAGER.ENDC}] {color}{page.url}{COLOR_MANAGER.ENDC}")
        already_printed.append(page)

    # Checking if the page was already checked
    in_list = False
    for pages in data.pages:
        if pages.url == page.url and (pages.content == page.content or type(pages) == type(page)):
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
    scripts = get_links([script.get("src") for script in soup.find_all("script")], page.url)
    for script in scripts:
        if all(script != page.url for page in data.pages) or session:
            # If the script is not in the page list
            if (not any(script == checked_page.url for checked_page in already_checked)
                    and script not in troublesome):
                # Page was not checked
                get_pages(data, script, data.recursive, session)

    # Getting every css style in the page
    styles = get_links([script.get("href") for script in soup.find_all(type="text/css")], page.url)
    for style in styles:
        if all(style != page.url for page in data.pages) or session:
            # If the script is not in the page list
            if (not any(style == checked_page.url for checked_page in already_checked)
                    and style not in troublesome):
                # Page was not checked
                get_pages(data, style, data.recursive, session)

    if recursive:
        # If the function is recursive
        links = get_links([link.get("href") for link in soup.find_all("a")], page.url)  # Getting every link in the page
        for link in links:
            if logged_out or len(data.pages) == data.max_pages:
                # More efficient to check every time
                # If the session logged out or the pages amount is at its maximum
                return
            if all(link != page.url for page in data.pages) or session:
                # If the page is not in the page list
                if (not any(link == checked_page.url for checked_page in already_checked)
                        and link not in troublesome):
                    # Page was not checked
                    get_pages(data, link, data.recursive, session)

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
            if any(new_url == url for origin, url, ses in login_pages):
                # The new url is already in the list
                return
            if all(new_url != p.url for p in data.pages):
                # If the new URL is not in list
                # It is also redirecting
                login_pages.append((page.url, new_url, session))
            else:
                # If the new URL is in the list
                for p in data.pages:
                    if new_url == p.url:
                        # Have the same URL
                        if content != p.content:
                            # Different content
                            login_pages.append((page.url, new_url, session))
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
        raise Exception("Unknown problem occurred.", "\t")

    if len(data.pages) == 0:
        raise Exception("Your website doesn't have any valid web pages", "\t")

    session_pages = 0
    if len(login_pages):
        # If there are specified username and password
        # login_pages = get_login_pages(data)
        global logged_out
        pages_backup = list(data.pages)
        for origin, url, session in login_pages:
            # Check every login page
            logged_out = True
            while logged_out:
                # Until it won't encounter a logout page
                logged_out = False
                get_pages(data, url, session=session)  # Attempting to achieve data from page
                if logged_out:
                    # If the session has encountered a logout page
                    already_checked.clear()  # The function needs to go through all the session pages
                    data.pages = list(pages_backup)  # Restoring the pages list
                    form_details, session = get_login_form(data, origin)  # Getting new session
                    submit_form(form_details, origin, session)  # Updating the session
                    # Doing the loop all over again, without the logout page
            # If the session has not encountered a logout page
            pages_backup = list(data.pages)
        # Counting the session pages
        for page in data.pages:
            if type(page) is SessionPage:
                session_pages += 1
    if session_pages != 0:
        print(f"\n\t{COLOR_MANAGER.BLUE}Pages that does not require login authorization: "
              f"{len(data.pages) - session_pages}\n"
              f"\t{COLOR_MANAGER.ORANGE}Pages that requires login authorization: {session_pages}\n")
    else:
        print(f"\n\t{COLOR_MANAGER.BLUE}Number of pages: {len(data.pages)}\n")