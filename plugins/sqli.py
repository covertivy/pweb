#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
import time
import random

COLOR = COLOR_MANAGER.rgb(255, 0, 128)
comments = {"#": ["sleep(5)"],
            "-- ": ["sleep(5)"],
            "--": ["dbms_pipe.receive_message(('a'),5)", "WAITFOR DELAY '0:0:5'", "pg_sleep(5)"]}
CHECK_STRING = "check"


def check(data: Data.Data):
    """
    Function checks the website for SQL injection
    @param data: The data object of the program
    @return: None
    """
    sqli_results = Data.CheckResults("SQL Injection", COLOR)

    data.mutex.acquire()
    pages = data.pages  # Achieving the pages
    aggressive = data.aggressive
    data.mutex.release()
    try:
        # Filtering the pages list
        pages = filter_forms(pages, aggressive)
        # [(page object, form dict),...]
        if len(pages):
            # There are pages with at least one text input
            if aggressive:
                # The user specified his agreement
                for page, form in pages:
                    try:
                        result = sql_injection(page, form, data)
                        if result.problem:
                            # If there is a problem with the page
                            sqli_results.page_results.append(result)
                    except Exception:
                        print(page.url)
                        continue
            else:
                # The user did not specified his agreement
                # and there is a vulnerable page
                sqli_results.page_results = "The plugin check routine requires injecting text boxes," \
                                            " read about (-A) in our manual and try again."
    except Exception:
        sqli_results.page_results = "Something went wrong..."
    data.mutex.acquire()
    data.results.append(sqli_results)  # Adding the results to the data object
    data.mutex.release()


def filter_forms(pages: list, aggressive: bool) -> list:
    """
    Function filters the pages that has an action form
    @param pages:List of pages
    @param aggressive: If it's false the user did not specified his agreement
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
                    if not aggressive:
                        # The user did not specified his agreement
                        return filtered_pages
            except Exception:
                continue
    return filtered_pages


def sql_injection(page, form: dict, data: Data.Data) -> Data.PageResult:
    """
    Function checks the page for SQL injection
    @param page: The current page
    @param form: The page's action form
    @param data: The data object of the program
    @return: Page result object
    """
    page_result = Data.PageResult(page, "", "")
    global comments
    browser = set_browser(data, page)
    text_inputs = get_text_inputs(form)  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = False
    found_vulnerability = False
    string = get_random_str(browser.page_source)
    start = time.time()  # Getting time of normal input
    submit_form([dict(input_tag) for input_tag in form["inputs"]],
                text_inputs[0], string, data, browser)
    normal_time = time.time() - start
    for text_input in text_inputs:
        browser.close()
        browser = set_browser(data, page)
        for comment in comments.keys():
            # Checking every comment
            for sleep in comments[comment]:
                # Checking every sleep function
                again = True
                while again:
                    again = False
                    start = time.time()
                    submit_form([dict(input_tag) for input_tag in form["inputs"]], text_input,
                                f"{get_random_str(browser.page_source)}' OR NOT {sleep} LIMIT 1{comment}",
                                data, browser)
                    injection_time = time.time() - start  # Injected input run time
                    if injection_time - normal_time > 7:
                        # Too much time
                        again = True
                        browser.close()
                        browser = set_browser(data, page)
                    elif injection_time - normal_time > 3:
                        # The injection slowed down the server response
                        results[text_input["name"]] = True
                        comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                        found_vulnerability = True
                if found_vulnerability:
                    # If a vulnerability is found, There is no reason to check another comment
                    break
            if found_vulnerability:
                # If a vulnerability is found, There is no reason to check another comment
                break
    browser.close()
    write_vulnerability(results, page_result)
    return page_result


def set_browser(data: Data.Data, page: Data.SessionPage):
    """
    Function Sets up a new browser, sets its cookies and checks if the cookies are valid
    @param data: The data object of the program
    @param page: The current page
    @return: The browser object
    """
    url = page.url
    if page.parent:
        # If the page is not first
        url = page.parent.url
    browser = data.new_browser()  # Getting new browser
    browser.set_page_load_timeout(60)  # Setting long timeout
    browser.get(url)  # Getting parent URL
    for cookie in page.cookies:  # Adding cookies
        browser.add_cookie(cookie)
    # Getting the page again, with the cookies
    browser.get(page.url)
    return browser


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


def get_random_str(content: str) -> str:
    while True:
        string = CHECK_STRING + str(random.randint(0, 1000))
        if string not in content:
            return string


def submit_form(inputs: list, curr_text_input: dict,
                text: str, data: Data.Data, browser):
    """
    Function submits a specified form
    @param inputs: A list of inputs of action form
    @param curr_text_input: The current text input we are checking
    @param text: The we want to implicate into the current text input
    @param data: The data object of the program
    @param browser: The webdriver object
    @return: The content of the resulted page
    """
    # The arguments body we want to submit
    for input_tag in inputs:
        # Using the specified value
        if not input_tag["value"]:
            if "name" in input_tag.keys() and input_tag["name"] == curr_text_input["name"]:
                # Only if the input has the current name
                input_tag["value"] = text
            else:
                input_tag["value"] = get_random_str(browser.page_source)
    # Sending the request
    data.submit_form(inputs, browser)
    content = browser.page_source
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
            page_result.problem = f"The text parameter '{key}' allowed SQL injection"
            page_result.solution = f"You can validate the input from the " \
                                   f"'{key}' parameter, by checking for " \
                                   f"vulnerable characters or wrong input type"
