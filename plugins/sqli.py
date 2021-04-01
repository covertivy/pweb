#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
import time
import random

# ----------------- {Consts} ---------------------
COLOR = COLOR_MANAGER.rgb(255, 0, 128)
TIME = 10
MINIMUM_ATTEMPTS = 3
MAXIMUM_ATTEMPTS = 3
ERROR_WORDS = ["error", "fail"]
QUERY_WORDS = ["sleep", "limit"]

# ----------------------- {Global variables} ------------------------------
comments = {"#": [f"sleep({Methods.WAITING_TIME})"],
            "-- ": [f"sleep({Methods.WAITING_TIME})"],
            "--": [f"dbms_pipe.receive_message(('a'),{Methods.WAITING_TIME})",
                   f"WAITFOR DELAY '0:0:{Methods.WAITING_TIME}'", f"pg_sleep({Methods.WAITING_TIME})"]}
query = str()
non_blind_problem = Classes.CheckResult("", "", "The plugin submits the action forms and check for 'error' or 'fail'"
                                                " words in the resulted page, it might indicate false positives,"
                                                " it made for sleep function blocking.\n"
                                                "You can check yourself if these are just irrelevant error messages.")
blind_problem = Classes.CheckResult("", "", "The plugin uses the sleep function of SQL "
                                            "to slow down the server's response.\n"
                                            "Compares between the response time and if the difference"
                                            " is close to 10 seconds, it must indicate SQL injection vulnerability.")


def check(data):
    """
    Function checks the website for SQL injection
    @type data: Classes.Data
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
                sqli_results.warning = "The plugin check routine requires injecting text boxes," \
                                            " read about (-A) in our manual and try again."
                break
            for form in forms:
                try:
                    sql_injection(page, form, data)
                except Exception:
                    continue
    except Exception as e:
        sqli_results.error = "Something went wrong..."

    non_blind_problem.problem = "These text inputs *may* have allowed SQL injection," \
                                " the plugin has detected an error message that " \
                                f"may indicate about a SQL vulnerability,\n" \
                                f"while using the query '{query}'."
    sqli_results.results.append(non_blind_problem)
    blind_problem.problem = "These text inputs allowed blind SQL injection, " \
                            f"the query '{query}' has slowed down the server's response."
    sqli_results.results.append(blind_problem)
    sqli_results.conclusion = f"You can validate the input from the " \
                              f"vulnerable parameters, by checking for " \
                              f"vulnerable characters or wrong input type."
    data.mutex.acquire()
    data.results_queue.put(sqli_results)  # Adding the results to the queue
    data.mutex.release()


def filter_forms(page):
    """
    Function filters the pages that has an action form
    @type page: Classes.Page
    @param page: The current page
    @rtype: list
    @return: List of forms
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


def sql_injection(page, form, data):
    """
    Function checks the page for SQL injection
    @type page: Classes.Page
    @param page: The current page
    @type form: dict
    @param form: The page's action form
    @type data: Classes.Data
    @param data: The data object of the program
    @return: None
    """
    page_result = Classes.PageResult(page, f"Action form '{form['action']}': ")
    global comments
    global query
    text_inputs = Methods.get_text_inputs(form["inputs"])  # Getting the text inputs
    words_count = dict()
    for key in ERROR_WORDS:
        words_count[key] = 0
    for key in QUERY_WORDS:
        words_count[key] = 0
    input_in_dom = False
    normal_time = 0
    normal_attempts = 0

    for _ in range(MINIMUM_ATTEMPTS):
        # Injecting
        temp_form = Methods.fill_input(form, dict(), "")
        fill_temp_form(temp_form)
        content, run_time, string = Methods.inject(data, page, temp_form)
        if string in content:
            input_in_dom = True  # If the form prints the input to the dom
        for key in words_count.keys():
            if content.lower().count(key) > words_count[key]:
                words_count[key] = content.lower().count(key)
        normal_time += run_time
        normal_attempts += 1

    for comment in comments.keys():
        # Checking every comment
        for sleep in comments[comment]:
            # Checking every sleep function
            query = f"{Methods.CHANGING_SIGN}'" \
                    f" OR NOT {sleep} LIMIT 1{comment}"
            temp_form = Methods.fill_input(form, text_inputs[0], query)
            fill_temp_form(temp_form)
            content, run_time, string = Methods.inject(data, page, temp_form)
            injection_time = run_time  # Injected input run time
            injection_attempts = 1
            for key in ERROR_WORDS:
                if content.lower().count(key) > words_count[key]:
                    # If there is a error word key in the content
                    found = False
                    if input_in_dom and query not in content:
                        # Normal input printed to the screen, sleep query did not
                        found = True
                    elif string not in content and \
                            any(content.lower().count(word) > words_count[word] for word in QUERY_WORDS):
                        # The check string was not printed, but the query words were printed.
                        found = True
                    if found:
                        # The screen printed an error message
                        page_result.description += f"The text parameter '{text_inputs[0]['name']}'."
                        non_blind_problem.add_page_result(page_result, "\n")
                        comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                        return
            while True:
                difference = injection_time/injection_attempts - normal_time/normal_attempts
                if difference < TIME + 2:
                    # It did not took too much time
                    if difference > TIME - 2:
                        # The injection slowed down the server response
                        page_result.description += f"The text parameter '{text_inputs[0]['name']}'" \
                                                    " slowed down the server by %3.1f seconds." % difference
                        blind_problem.add_page_result(page_result, "\n")
                        comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                        return
                    if difference < 2:
                        break
                elif injection_attempts == MAXIMUM_ATTEMPTS:
                    # It took too much time to load the page
                    page_result.description += f"The text parameter '{text_inputs[0]['name']}'" \
                                               " slowed down the server by %3.1f seconds." % difference
                    blind_problem.add_page_result(page_result, "\n")
                    comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                    return
                # Between 2-8 seconds we need to make sure
                temp_form = Methods.fill_input(form, dict(), "")
                fill_temp_form(temp_form)
                content, run_time, string = Methods.inject(data, page, temp_form)
                normal_time += run_time
                normal_attempts += 1
                temp_form = Methods.fill_input(form, text_inputs[0], query)
                fill_temp_form(temp_form)
                content, run_time, string = Methods.inject(data, page, temp_form)
                injection_time += run_time  # Injected input run time
                injection_attempts += 1


def fill_temp_form(form):
    """
    Function fill the temp form text inputs with the CHANGING_SIGN
    @type form: dict
    @param form: The temp form
    @return: None
    """
    # Block PNG, JPEG and GIF images
    if request.path.endswith(('.png', '.jpg', '.gif')):
        # Save run time
        request.abort()


def get_text_inputs(form) -> list:
    """
    Function gets the text input names from a form
    @param form: a dictionary of inputs of action form
    @return: list of text inputs
    """
    text_inputs = list()
    for input_tag in form["inputs"]:
        if input_tag in Methods.get_text_inputs(form["inputs"]):
            # If it is a text input
            if "value" in input_tag.keys() and not input_tag["value"]:
                # There is no value to the text input
                input_tag["value"] = Methods.CHANGING_SIGN
