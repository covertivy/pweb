#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# ----------------- {Consts} ---------------------
COLOR = COLOR_MANAGER.rgb(255, 0, 128)
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
    This function checks the website for SQL injection.

    @param data: The data object of the program
    @type data: Classes.Data
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
    This function filters the pages that has an action form.

    @param page: The current page
    @type page: Classes.Page
    @return: List of forms
    @rtype: list
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
    This function checks the page for SQL injection.

    @param page: The current page
    @type page: Classes.Page
    @param form: The page's action form
    @type form: dict
    @param data: The data object of the program
    @type data: Classes.Data
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
    This function fill the temp form text inputs with the CHANGING_SIGN.

    @param form: The temp form
    @type form: dict
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
