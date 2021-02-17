#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# Consts:
COLOR = COLOR_MANAGER.rgb(255, 0, 128)
TIME = 10
MINIMUM_ATTEMPTS = 3

# Global variables:
comments = {"#": [f"sleep({TIME})"],
            "-- ": [f"sleep({TIME})"],
            "--": [f"dbms_pipe.receive_message(('a'),{TIME})",
                   f"WAITFOR DELAY '0:0:{TIME}'", f"pg_sleep({TIME})"]}


def check(data: Classes.Data):
    """
    Function checks the website for SQL injection
    @param data: The data object of the program
    @return: None
    """
    sqli_results = Classes.CheckResults("SQL Injection", COLOR)

    try:
        data.mutex.acquire()
        pages = data.pages  # Achieving the pages
        aggressive = data.aggressive
        data.mutex.release()
        for page in pages:
            # Getting the forms of each page
            forms = filter_forms(page)
            if forms and not aggressive:
                # The user did not specified his agreement
                # and there is a vulnerable page
                sqli_results.page_results = "The plugin check routine requires injecting text boxes," \
                                            " read about (-A) in our manual and try again."
                break
            for form in forms:
                try:
                    result = sql_injection(page, form, data)
                    if result.problem:
                        # If there is a problem with the page
                        sqli_results.page_results.append(result)
                except Exception:
                    continue
    except Exception as e:
        sqli_results.page_results = "Something went wrong..."

    data.mutex.acquire()
    data.results.append(sqli_results)  # Adding the results to the data object
    data.mutex.release()


def filter_forms(page: Classes.Page) -> list:
    """
    Function filters the pages that has an action form
    @param page: The current page
    @return: List of forms
    """
    filtered_forms = list()
    if "html" in page.type.lower():
        # We can check only html files
        forms = Methods.get_forms(page.content)  # Getting page forms
        for form in forms:
            if len(Methods.get_text_inputs(form)) != 0:
                # If there are no text inputs, it can't be command injection
                filtered_forms.append(form)
    return filtered_forms


def sql_injection(page, form: dict, data: Classes.Data) -> Classes.PageResult:
    """
    Function checks the page for SQL injection
    @param page: The current page
    @param form: The page's action form
    @param data: The data object of the program
    @return: Page result object
    """
    page_result = Classes.PageResult(page, "", "")
    global comments
    text_inputs = Methods.get_text_inputs(form)  # Getting the text inputs
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
                string = Methods.get_random_str(browser.page_source)
            elif "X" in string:
                # Replace X with a random string
                string = string.replace("X", Methods.get_random_str(browser.page_source))
            # Getting the updated form, in case of CSRF tokens
            forms = Methods.get_forms(content=browser.page_source)
            curr_form = dict()
            for curr_form in forms:
                if curr_form["action"] == form["action"] and curr_form["method"] == form["method"]:
                    # Have the same action and method
                    break
            # Submitting the new form
            c, r, s = Methods.submit_form(curr_form["inputs"], text_inputs[0], string, browser, data)
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


def set_browser(data: Classes.Data, page):
    """
    Function Sets up a new browser, sets its cookies and checks if the cookies are valid
    @param data: The data object of the program
    @param page: The current page
    @return: The browser object
    """
    if type(page) is Classes.SessionPage:
        # If the current page is not a session page
        return Methods.new_browser(data, session_page=page)  # Getting new browser
    browser = Methods.new_browser(data)  # Getting new browser
    browser.get(page.url)
    return browser


def write_vulnerability(results: dict, page_result: Classes.PageResult):
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
