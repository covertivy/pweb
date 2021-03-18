#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# ----------------- {Consts} ---------------------
COLOR = COLOR_MANAGER.rgb(255, 0, 128)
MINIMUM_ATTEMPTS = 3
MAXIMUM_ATTEMPTS = 3
NON_BLIND_WORDS = ["error", "fail"]

# ----------------------- {Global variables} ------------------------------
comments = {"#": [f"sleep({Methods.WAITING_TIME})"],
            "-- ": [f"sleep({Methods.WAITING_TIME})"],
            "--": [f"dbms_pipe.receive_message(('a'),{Methods.WAITING_TIME})",
                   f"WAITFOR DELAY '0:0:{Methods.WAITING_TIME}'", f"pg_sleep({Methods.WAITING_TIME})"]}
query = str()
non_blind_problem = Classes.CheckResult("", "")
blind_problem = Classes.CheckResult("", "")


def check(data):
    """
    Function checks the website for SQL injection
    @type data: Classes.Data
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

    blind_problem.problem = "These text inputs allowed blind SQL injection, " \
                            f"the query '{query}' has slowed down the server's response."
    sqli_results.results.append(blind_problem)
    non_blind_problem.problem = "These text inputs *may* have allowed SQL injection," \
                                " the plugin has detected an error message that " \
                                f"may indicate about a SQL vulnerability,\n" \
                                f"while using the query '{query}'."
    sqli_results.results.append(non_blind_problem)
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
    filtered_forms = list()
    if "html" in page.type.lower():
        # We can check only html files
        forms = Methods.get_forms(page.content)  # Getting page forms
        for form in forms:
            if len(Methods.get_text_inputs(form["inputs"])) != 0:
                # If there are no text inputs, it can't be command injection
                filtered_forms.append(form)
    return filtered_forms


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
    for key in NON_BLIND_WORDS:
        words_count[key] = 0
    words_count["sleep"] = 0
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
            query = f"{Methods.CHANGING_SIGN}'" \
                    f" OR NOT {sleep} LIMIT 1{comment}"
            temp_form = Methods.fill_input(form, text_inputs[0], query)
            fill_temp_form(temp_form)
            content, run_time, string = Methods.inject(data, page, temp_form)
            injection_time = run_time  # Injected input run time
            injection_attempts = 1
            for key in NON_BLIND_WORDS:
                if content.lower().count(key) > words_count[key] and\
                        (string in content or content.lower().count("sleep") > words_count["sleep"]):
                    # The screen printed an error message
                    page_result.description += f"The text parameter '{text_inputs[0]['name']}'."
                    non_blind_problem.add_page_result(page_result, "\n")
                    comments = {comment: [sleep]}  # Found the data base's sleep function and comment
                    return
            while True:
                difference = injection_time/injection_attempts - normal_time/normal_attempts
                if difference < Methods.WAITING_TIME + 2:
                    # It did not took too much time
                    if difference > Methods.WAITING_TIME - 2:
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
    if len(Methods.get_text_inputs(form["inputs"])) < 3:
        return
    for input_tag in form["inputs"]:
        if input_tag in Methods.get_text_inputs(form["inputs"]):
            # If it is a text input
            if "value" in input_tag.keys() and not input_tag["value"]:
                # There is no value to the text input
                input_tag["value"] = Methods.CHANGING_SIGN
