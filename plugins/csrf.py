#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import random

COLOR = COLOR_MANAGER.rgb(255, 255, 0)
CHECK_STRING = "checkcheck"


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
        forms = BeautifulSoup(page.content, "html.parser").find_all("form")  # Getting page forms
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
                # Adding the page and it's form to the list
                filtered_pages.append((page, form_details))
                if not agreement:
                    # The user did not specified his agreement
                    return filtered_pages
            except:
                continue
    return filtered_pages


def csrf(page: Data.SessionPage, form: dict) -> Data.PageResult:
    """
    Function checks the page for csrf
    @param page: The current page
    @param form: The page's action form
    @return: Page result object
    """
    page_result = Data.PageResult(page, "", "")
    # Join the url with the action (form request URL)
    action_url = urljoin(page.url, form["action"])  # Getting action URL
    if form["method"] == "get":
        # Dangerous by itself
        pass
    # Getting normal response
    normal_response = get_response(new_session(page.cookies), action_url, form)
    # Getting redirected response
    referer_response = get_referer_response(new_session(page.cookies), action_url, form)
    return page_result


def new_session(cookies) -> requests.Session:
    """
    Function create a new session
    @param cookies: We need those cookies to save the session
    @return: The session object
    """
    # Setting session for connection
    session = requests.Session()
    # Setting cookies
    session.cookies = cookies
    return session


def get_referer_response(session: requests.Session, action_url: str, form: dict) -> requests.Response:
    """
    Function gets the content of the page if we set a referer header
    @param session: Requests session object
    @param action_url: Action URL the website asks
    @param form: A dictionary of inputs of action form
    @return: The content of the resulted page
    """
    # Setting referer
    session.headers.update({'referer': "https://www.google.com/"})
    return get_response(session, action_url, form)


def get_response(session: requests.Session, action_url: str, form: dict) -> requests.Response:
    """
    Function submits a specified form and gets the result content
    @param session: Requests session object
    @param action_url: Action URL the website asks
    @param form: A dictionary of inputs of action form
    @return: The content of the resulted page
    """
    # The arguments body we want to submit
    args = dict()
    for input_tag in form["inputs"]:
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            if input_tag["value"]:
                args[input_tag["name"]] = input_tag["value"]
            else:
                args[input_tag["name"]] = CHECK_STRING + str(random.randint(1, 200))
    # Sending the request
    if form["method"] == "post":
        # POST request
        response = session.post(action_url, data=args)
    else:
        # GET request
        response = session.get(action_url, params=args)
    return response
