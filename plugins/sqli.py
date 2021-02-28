#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# Consts:
COLOR = COLOR_MANAGER.rgb(255, 0, 128)
MINIMUM_ATTEMPTS = 3
MAXIMUM_ATTEMPTS = 3
NON_BLIND_WORDS = ["error", "fail"]
NON_BLIND_SIGN = 400

# Global variables:
comments = {"#": [f"sleep({Methods.WAITING_TIME})"],
            "-- ": [f"sleep({Methods.WAITING_TIME})"],
            "--": [f"dbms_pipe.receive_message(('a'),{Methods.WAITING_TIME})",
                   f"WAITFOR DELAY '0:0:{Methods.WAITING_TIME}'", f"pg_sleep({Methods.WAITING_TIME})"]}


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
            if len(Methods.get_text_inputs(form["inputs"])) != 0:
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
    text_inputs = Methods.get_text_inputs(form["inputs"])  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = 0
    words_count = dict()
    for key in NON_BLIND_WORDS:
        words_count[key] = 0
    words_count["sleep"] = 0
    found_vulnerability = False
    normal_time = 0
    normal_attempts = 0
    for _ in range(MINIMUM_ATTEMPTS):
        # Injecting
        temp_form = Methods.fill_input(form, dict(), "")
        fill_temp_form(temp_form)
        content, run_time, s = Methods.inject(data, page, temp_form)
        for key in words_count.keys():
            if content.lower().count(key) > words_count[key]:
                words_count[key] = content.lower().count(key)
        normal_time += run_time
        normal_attempts += 1
    for comment in comments.keys():
        # Checking every comment
        for sleep in comments[comment]:
            # Checking every sleep function
            temp_form = Methods.fill_input(form, text_inputs[0], f"{Methods.CHANGING_SIGN}'"
                                                                   f" OR NOT {sleep} LIMIT 1{comment}")
            fill_temp_form(temp_form)
            content, run_time, string = Methods.inject(data, page, temp_form)
            injection_time = run_time  # Injected input run time
            injection_attempts = 1
            for key in NON_BLIND_WORDS:
                if content.lower().count(key) > words_count[key] and\
                        (string in content or content.lower().count("sleep") > words_count["sleep"]):
                    # The screen printed an error message
                    results[text_inputs[0]["name"]] = NON_BLIND_SIGN
                    comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                    found_vulnerability = True
                    break
            if found_vulnerability:
                # If a vulnerability is found, There is no reason to check another comment
                break
            while True:
                difference = injection_time/injection_attempts - normal_time/normal_attempts
                if difference < Methods.WAITING_TIME + 2:
                    # It did not took too much time
                    if difference > Methods.WAITING_TIME - 2:
                        # The injection slowed down the server response
                        results[text_inputs[0]["name"]] = difference
                        comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                        found_vulnerability = True
                        break
                    if difference < 2:
                        break
                elif injection_attempts == MAXIMUM_ATTEMPTS:
                    # It took too much time to load the page
                    results[text_inputs[0]["name"]] = difference
                    comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                    found_vulnerability = True
                    break
                # Between 2-8 seconds we need to make sure
                temp_form = Methods.fill_input(form, dict(), "")
                fill_temp_form(temp_form)
                content, run_time, string = Methods.inject(data, page, temp_form)
                normal_time += run_time
                normal_attempts += 1
                temp_form = Methods.fill_input(form, text_inputs[0], f"{Methods.CHANGING_SIGN}'"
                                                                     f" OR NOT {sleep} LIMIT 1{comment}")
                fill_temp_form(temp_form)
                content, run_time, string = Methods.inject(data, page, temp_form)
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


def fill_temp_form(form: dict):
    """
    Function fill the temp form text inputs with the CHANGING_SIGN
    @param form: The temp form
    @return: None
    """
    if len(Methods.get_text_inputs(form["inputs"])) < 3:
        return
    for input_tag in form["inputs"]:
        if input_tag in Methods.get_text_inputs(form["inputs"]):
            # If it is a text input
            if "value" in input_tag.keys() and not input_tag["value"]:
                # There is no value to the text input
                input_tag["value"] = Methods.CHANGING_SIGN


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
            if results[key] == NON_BLIND_SIGN:
                page_result.problem = f"The text parameter '{key}' may have allowed SQL injection," \
                                      " the plugin detected an error message that " \
                                      "may indicate about a SQL vulnerability."
            else:
                page_result.problem = f"The text parameter '{key}' allowed blind SQL injection," \
                                      " the server has slowed down by %3.1f seconds." % results[key]
            page_result.solution = f"You can validate the input from the " \
                                   f"'{key}' parameter, by checking for " \
                                   f"vulnerable characters or wrong input type"
