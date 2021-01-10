#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import time

COLOR = COLOR_MANAGER.rgb(255, 0, 128)
comments = {"#": ["sleep(5)"],
            "-- ": ["sleep(5)"],
            "--": ["dbms_pipe.receive_message(('a'),5)", "WAITFOR DELAY '0:0:5'", "pg_sleep(5)"]}
CHECK_STRING = "checkcheck"


def check(data: Data.Data):
    """
    Function checks the website for SQL injection
    @param data: The data object of the program
    @return: None
    """
    sqli_results = Data.CheckResults("SQL Injection", COLOR)

    data.mutex.acquire()
    pages = data.pages  # Achieving the pages
    data.mutex.release()
    # Filtering the pages list
    try:
        pages = filter_forms(pages)  # [(page object, form dict),...]
        if len(pages):
            # There are pages with at least one text input
            if data.agreement:
                # The user specified his agreement
                for page, form in pages:
                    try:
                        result = sql_injection(page, form)
                        if result.problem:
                            # If there is a problem with the page
                            sqli_results.page_results.append(result)
                    except Exception as e:
                        continue
            else:
                # The user did not specified his agreement
                sqli_results.page_results = "The plugin check routine requires injecting text boxes," \
                                            " read about (-a) in our manual and try again."
    except Exception as e:
        sqli_results.page_results = "Something went wrong..."
    data.mutex.acquire()
    data.results.append(sqli_results)  # Adding the results to the data object
    data.mutex.release()


def filter_forms(pages: list) -> list:
    """
    Function filters the pages that has an action form
    @param pages:List of pages
    @return: List of pages that has an action form
    """
    filtered_pages = list()
    for page in pages:
        if "html" not in page.type.lower():
            # If it is a non-html page we can not check for sql injection
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
                if len(get_text_inputs(form_details)) != 0:
                    # If there are no text inputs, it can't be sql injection
                    filtered_pages.append((page, form_details))
            except:
                continue
    return filtered_pages


def sql_injection(page, form: dict) -> Data.PageResult:
    """
    Function checks the page for SQL injection
    @param page: The current page
    @param form: The page's action form
    @return: Page result object
    """
    page_result = Data.PageResult(page, "", "")
    global comments
    if type(page) == Data.SessionPage:
        cookies = page.cookies
    else:
        cookies = None
    # Join the url with the action (form request URL)
    action_url = urljoin(page.url, form["action"])  # Getting action URL
    text_inputs = get_text_inputs(form)  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = False
    found_vulnerability = False
    for text_input in text_inputs:
        for comment in comments.keys():
            # Checking every comment
            for sleep in comments[comment]:
                # Checking every sleep function
                start = time.time()
                submit_form(action_url, form, cookies, text_input, f"{CHECK_STRING}")
                normal_time = time.time() - start  # Normal input run time
                start = time.time()
                submit_form(action_url, form, cookies, text_input,
                            f"{CHECK_STRING}' OR NOT {sleep} LIMIT 1{comment}")
                injection_time = time.time() - start  # Injected input run time
                if injection_time - normal_time > 3:
                    # The injection slowed down the server response
                    results[text_input["name"]] = True
                    comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                    found_vulnerability = True
                    break  # There is no reason to check another sleep function
            if found_vulnerability:
                # If a vulnerability is found, There is no reason to check another comment
                break
    write_vulnerability(results, page_result)
    return page_result


def get_text_inputs(form) -> list:
    """
    Function gets the text input names from a form
    @param form: a dictionary of inputs of action form
    @return: list of text inputs
    """
    text_inputs = list()
    for input_tag in form["inputs"]:
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            if input_tag["type"] and input_tag["type"] == "text":
                text_inputs.append(input_tag)
    return text_inputs


def submit_form(action_url: str, form: dict, cookies, curr_text_input: dict, text: str):
    """
    Function submits a specified form
    @param action_url: Action URL the website asks
    @param form: A dictionary of inputs of action form
    @param cookies: In case of session, we need those cookies
    @param curr_text_input: The current text input we are checking
    @param text: The we want to implicate into the current text input
    @return: The content of the resulted page
    """
    # Setting session for connection
    session = requests.Session()
    if cookies:
        # In case of session page
        session.cookies = cookies
    # The arguments body we want to submit
    args = dict()
    for input_tag in form["inputs"]:
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            if input_tag["name"] == curr_text_input["name"]:
                args[input_tag["name"]] = f"{text}"
            else:
                args[input_tag["name"]] = input_tag["value"]
    # Sending the request
    content = str()
    if form["method"] == "post":
        content = session.post(action_url, data=args).text
    elif form["method"] == "get":
        content = session.get(action_url, params=args).text
    return content


def write_vulnerability(results: dict, page_result: Data.PageResult):
    """
    Function writes the problem and the solution of every problem that is found for a page
    @param results: a dictionary of text input and list of chars it didn't filter
    @param page_result: page result object of the current page
    @return: None
    """
    for key in results.keys():
        # For every text input
        if results[key]:
            # If the input is vulnerable
            page_result.problem += f"The text parameter '{key}' allowed SQL injection"
            page_result.solution += f"TBA"
