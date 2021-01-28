#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import random

COLOR = COLOR_MANAGER.rgb(255, 255, 0)
CHECK_STRING = "check"


def check(data: Data.Data):
    """
    Function checks the website for CSRF
    @param data: The data object of the program
    @return: None
    """
    csrf_results = Data.CheckResults("CSRF", COLOR)

    data.mutex.acquire()
    pages = data.pages  # Achieving the pages
    agreement = data.agreement
    data.mutex.release()
    try:
        # Filtering the pages list
        pages = filter_forms(pages, agreement)
        # [(page object, form dict),...]
        if len(pages):
            # There are pages with at least one text input
            if data.agreement:
                # The user specified his agreement
                for page, form in pages:
                    try:
                        result = csrf(page, form)
                        if result.problem:
                            # If there is a problem with the page
                            csrf_results.page_results.append(result)
                    except Exception:
                        continue
            else:
                # The user did not specified his agreement
                # and there is a vulnerable page
                csrf_results.page_results = "The plugin check routine requires submitting web forms," \
                                            " read about (-a) in our manual and try again."
    except Exception:
        csrf_results.page_results = "Something went wrong..."
    data.mutex.acquire()
    data.results.append(csrf_results)  # Adding the results to the data object
    data.mutex.release()


def get_forms(content: str):
    form_dict = list()
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
            for input_tag in form.find_all("input"):
                # Get type of input form control
                input_type = input_tag.attrs.get("type", "text")
                # Get name attribute
                input_name = input_tag.attrs.get("name")
                # Get the default value of that input tag
                input_value = input_tag.attrs.get("value", "")
                # Add everything to that list
                input_dict = dict()
                if input_type:
                    input_dict["type"] = input_type
                if input_name:
                    input_dict["name"] = input_name
                input_dict["value"] = input_value
                inputs.append(input_dict)
            # Setting the form dictionary
            form_details = dict()
            form_details["action"] = action
            form_details["method"] = method
            form_details["inputs"] = inputs
            form_dict.append(form_details)
        except:
            continue
    return form_dict


def filter_forms(pages: list, agreement: bool) -> list:
    """
    Function filters the pages that has an action form
    @param pages:List of pages
    @param agreement: The specified user's agreement
    @return: List of pages that has an action form
    """
    filtered_pages = list()
    for page in pages:
        if "html" not in page.type.lower():
            # If it is a non-html page we can not check for command injection
            continue
        if type(page) is not Data.SessionPage:
            # If the page is not a session page
            continue
        for form in get_forms(page.content):
            # Adding the page and it's form to the list
            filtered_pages.append((page, form))
            if not agreement:
                # The user did not specified his agreement
                return filtered_pages
    return filtered_pages


def csrf(page: Data.SessionPage, form: dict) -> Data.PageResult:
    """
    Function checks the page for csrf
    @param page: The current page
    @param form: The page's action form
    @return: Page result object
    """
    page_result = Data.PageResult(page, "", "")
    vulnerability = [False, False, False]
    # Checking for csrf tokens
    session = new_session(page.cookies, page.url)
    session.cookies = page.cookies
    reload = session.get(page.url).text
    token = False
    for new_form in get_forms(reload):
        if new_form["action"] == form["action"]:
            # Same form
            for input_tag in form["inputs"]:
                # Using the specified value
                if "name" in input_tag.keys() and input_tag["value"]:
                    # Only if the input has a name and a value
                    for new_input_tag in new_form["inputs"]:
                        if "name" in new_input_tag.keys() and new_input_tag["name"] == input_tag["name"]:
                            # If the input tags have the same name
                            if new_input_tag["value"] != input_tag["value"]:
                                # If the input tags have different values
                                token = True
                                break
                    if token:
                        # No need to look for another input tag
                        break
            break  # There is only one fitting form
    if token:
        # Found a csrf token
        return page_result
    # Join the url with the action (form request URL)
    action_url = urljoin(page.url, form["action"])  # Getting action URL
    if form["method"] == "get":
        # Dangerous by itself
        vulnerability[0] = True
    # Getting normal content
    normal_content = get_response(new_session(page.cookies, page.url),
                                  action_url, form)
    # Getting redirected content
    referer_content = get_response(new_session(page.cookies, "https://google.com"),
                                   action_url, form)
    if normal_content == referer_content:
        # Does not filter referer header
        vulnerability[1] = True
    else:
        # Getting redirected content
        referer_content = get_response(new_session(page.cookies, page.parent.url),
                                       action_url, form)
        if normal_content == referer_content:
            # Does not filter referer header
            vulnerability[2] = True
    write_vulnerability(vulnerability, page_result, action_url)
    return page_result


def new_session(cookies, referer) -> requests.Session:
    """
    Function create a new session
    @param cookies: We need those cookies to save the session
    @param referer: The last known URL that called the page
    @return: The session object
    """
    # Setting session for connection
    session = requests.Session()
    # Setting cookies
    session.cookies = cookies
    # Setting referer
    session.headers.update({'referer': referer})
    return session


def get_response(session: requests.Session, action_url: str, form: dict) -> str:
    """
    Function submits a specified form and gets the result content
    @param session: Requests session object
    @param action_url: Action URL the website asks
    @param form: A dictionary of inputs of action form
    @return: The content of the resulted page
    """
    # The arguments body we want to submit
    args = dict()
    check_strings = list()
    for input_tag in form["inputs"]:
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            if input_tag["value"]:
                args[input_tag["name"]] = input_tag["value"]
            else:
                while True:
                    # While the random string in the list
                    check_string = CHECK_STRING + str(random.randint(1, 200))
                    if check_string not in check_strings:
                        break
                check_strings.append(check_string)
                args[input_tag["name"]] = check_string
    # Sending the request
    if form["method"] == "post":
        # POST request
        content = session.post(action_url, data=args).text
    else:
        # GET request
        content = session.get(action_url, params=args).text
    for string in check_strings:
        # In case that the random string is in the content
        content = content.replace(string, "")
    return content


def write_vulnerability(results: list, page_result: Data.PageResult, action_url):
    """
    Function writes the problem and the solution of every problem that is found for a page
    @param results: a dictionary of text input and list of chars it didn't filter
    @param page_result: page result object of the current page
    @param action_url: The action URL
    @return: None
    """
    lines = sum(results)
    padding = " " * 25
    if results[0]:
        # GET problem
        page_result.problem += f"The use of GET request when submitting the form '{action_url}' might be vulnerable."
        page_result.solution += f"You can change the method of the request to POST.\n{padding} "
        if lines > 1:
            # More than one line
            page_result.problem += "\n" + padding
    if results[1] or results[2]:
        # Referer problem
        page_result.solution += "You can validate the 'Referer' header of the request," \
                                f" so it will perform only actions from the current page.\n{padding} "
        if results[1]:
            # Referer to outside of the domain
            page_result.problem += "The page did not detect the 'Referer' header, which was outside of your domain."
        else:
            # Referer to inside of the domain
            page_result.problem += "The page did not detect the 'Referer' header," \
                                   f" which was not the same page that has the action '{action_url}'."
    page_result.solution += "The best way to prevent CSRF vulnerability is to use CSRF Tokens, " \
                            f"\n{padding} read more about it in: 'https://portswigger.net/web-security/csrf/tokens'."
