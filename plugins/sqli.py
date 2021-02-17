#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup

COLOR = COLOR_MANAGER.rgb(255, 0, 128)
TIME = 10
MINIMUM_ATTEMPTS = 3
comments = {"#": [f"sleep({TIME})"],
            "-- ": [f"sleep({TIME})"],
            "--": [f"dbms_pipe.receive_message(('a'),{TIME})",
                   f"WAITFOR DELAY '0:0:{TIME}'", f"pg_sleep({TIME})"]}


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
                if len(Data.get_text_inputs(form_details)) != 0:
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
    text_inputs = Data.get_text_inputs(form)  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = 0
    found_vulnerability = False
    normal_time = 0
    normal_attempts = 0

    def inject(string=None) -> (str, float):
        """
        Inner function inject a string into a text box and submit the form
        @param string: The string we want to inject
        @return: Set of (the content of the page, the time it took submit the form)
        """
        browser = None
        try:
            browser = set_browser(data, page)
            if not string:
                # If there is no string specified, generate a random string
                string = Data.get_random_str(browser.page_source)
            elif "X" in string:
                # Replace X with a random string
                string = string.replace("X", Data.get_random_str(browser.page_source))
            c, r, s = Data.submit_form(form["inputs"], text_inputs[0], string, browser)
        except Exception:
            # In case of failing, try again
            if browser:
                browser.quit()
            return inject(string)
        else:
            browser.quit()
            return c, r

    for _ in range(MINIMUM_ATTEMPTS):
        # Injecting
        content, run_time = inject()
        normal_time += run_time
        normal_attempts += 1

    for comment in comments.keys():
        # Checking every comment
        for sleep in comments[comment]:
            # Checking every sleep function
            content, run_time = inject(f"X' OR NOT {sleep} LIMIT 1{comment}")
            injection_time = run_time  # Injected input run time
            injection_attempts = 1
            while True:
                difference = injection_time/injection_attempts - normal_time/normal_attempts
                if difference < TIME + 2:
                    # It did not took too much time
                    if difference > TIME - 2:
                        # The injection slowed down the server response
                        results[text_inputs[0]["name"]] = difference
                        comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                        found_vulnerability = True
                        break
                    if difference < 2:
                        break
                # It took too much time to load the page
                content, run_time = inject()
                normal_time += run_time
                normal_attempts += 1

                content, run_time = inject(f"X' OR NOT {sleep} LIMIT 1{comment}")
                injection_time += run_time  # Injected input run time
                injection_attempts += 1
            if found_vulnerability:
                # If a vulnerability is found, There is no reason to check another comment
                break
        if found_vulnerability:
            # If a vulnerability is found, There is no reason to check another comment
            break
    write_vulnerability(results, page_result)
    return page_result


def set_browser(data: Data.Data, page):
    """
    Function Sets up a new browser, sets its cookies and checks if the cookies are valid
    @param data: The data object of the program
    @param page: The current page
    @return: The browser object
    """
    if type(page) is Data.SessionPage:
        # If the current page is not a session page
        return Data.new_browser(data, session_page=page)  # Getting new browser
    browser = Data.new_browser(data)  # Getting new browser
    browser.get(page.url)
    return browser


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
            page_result.problem = f"The text parameter '{key}' allowed blind SQL injection," \
                                  " the server has slowed down by %3.1f seconds." % results[key]
            page_result.solution = f"You can validate the input from the " \
                                   f"'{key}' parameter, by checking for " \
                                   f"vulnerable characters or wrong input type"
