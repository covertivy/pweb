#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
import time
import random

# --------------- {Consts} ---------------
COLOR = COLOR_MANAGER.rgb(255, 255, 0)
NON_BLIND_STRING = "checkcheck"

# -------------------------------- {Global variables} ---------------------------------
curr_text_input = dict()
curr_char = ""
blind_problem = Classes.CheckResult("These text inputs allowed blind Command injection, "
                                    f"the query ' ping -c {Methods.WAITING_TIME} 127.0.0.1' "
                                    f"has slowed down the server's response.", "",
                                    "The plugin submits the action form with the query "
                                    f"' ping -c {Methods.WAITING_TIME} 127.0.0.1',\n"
                                    f"if the server's response is delayed, "
                                    f"it must indicate of Command injection vulnerability.")
non_blind_problem = Classes.CheckResult("These text inputs *may* have allowed Command injection,"
                                        " the plugin has detected an echo message that "
                                        f"indicate about a Command injection vulnerability.", "",
                                        "The plugin submits the action form with a 'echo check' "
                                        "in each of the text inputs,\n"
                                        "and counting the amount of 'check' strings in compare of the amount of 'echo' "
                                        "strings in the DOM of the resulted page.\n"
                                        "If there are more 'check' than 'echo' it might indicate of a non blind "
                                        "Command injection.")


def check(data):
    """
    Function checks the website for blind/non-blind OS injection
    @type data: Classes.Data
    @param data: The data object of the program
    @return: None
    """
    ci_results = Data.CheckResults("Command Injection", COLOR)
    try:
        data.mutex.acquire()
        pages = data.pages  # Achieving the pages
        aggressive = data.aggressive
        data.mutex.release()
        # Filtering the pages list
        pages = filter_forms(pages, aggressive)
        # [(page object, form dict),...]
        if len(pages):
            # There are pages with at least one text input
            if data.aggressive:
                # The user specified his agreement
                for page, form in pages:
                    try:
                        result = command_injection(page, form, data)
                        if result.problem:
                            # If there is a problem with the page
                            ci_results.page_results.append(result)
                    except Exception:
                        continue
            else:
                # The user did not specified his agreement
                # and there is a vulnerable page
                ci_results.warning = "The plugin check routine requires injecting text boxes," \
                                          " read about (-A) in our manual and try again."
                break
            for form in forms:
                try:
                    command_injection(page, form, data)
                except Exception:
                    continue
    except Exception as e:
        ci_results.error = "Something went wrong..."

    ci_results.results.append(blind_problem)
    ci_results.results.append(non_blind_problem)
    ci_results.conclusion = f"You can validate the input from the " \
                            f"vulnerable parameters, by checking for " \
                            f"vulnerable characters or wrong input type."

    data.mutex.acquire()
    data.results_queue.put(ci_results)  # Adding the results to the data object
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
            # If it is a non-html page we can not check for command injection
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
                    # If there are no text inputs, it can't be command injection
                    filtered_pages.append((page, form_details))
                    if not aggressive:
                        # The user did not specified his agreement
                        return filtered_pages
            except:
                continue
    return filtered_pages


def command_injection(page, form, data):
    """
    Function checks the page for blind/non-blind OS injection
    @type page: Classes.Page
    @param page: The current page
    @type form: dict
    @param form: The page's action form
    @type data: Classes.Data
    @param data: The data object of the program
    @return: None
    """
    page_result = Classes.PageResult(page, f"Action form '{form['action']}': ")
    chars_to_filter = ["&", "&&", "|", "||", ";", "\n"]
    text_inputs = Methods.get_text_inputs(form["inputs"])  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = list()
    found_vulnerability = False
    normal_time = 0
    normal_attempts = 0
    global curr_text_input
    global curr_char
    for curr_char in chars_to_filter:
        for curr_text_input in text_inputs:  # In case of more than one text input
            # Getting content of non-blind injection
            browser.get(page.url)
            while True:
                string = NON_BLIND_STRING + str(random.randint(0, 1000))
                if string not in browser.page_source:
                    break
            start = time.time()  # Getting time of normal input
            content = submit_form(form, curr_text_input,
                                  f"{char}echo {string}", data, browser)
            normal_time = time.time() - start
            average_time += normal_time
            attempts += 1
            if content.count(string) > content.count(f"echo {string}"):
                # The web page printed the echo message
                results[curr_text_input["name"]].append(curr_char)
                found_vulnerability = True
    if found_vulnerability:
        # Found non blind injection in the form
        write_vulnerability(results, page_result)
        non_blind_problem.add_page_result(page_result, "\n")
        return
    # Didn't find anything
    for curr_text_input in text_inputs:
        for char in chars_to_filter:  # In case of more than one text input
            # Getting time of blind injection
            injection_time = 0
            injection_attempts = 0
            while True:
                temp_form = Methods.fill_input(form, curr_text_input,
                                               f" ping -c {Methods.WAITING_TIME} 127.0.0.1")
                content, run_time, s = Methods.inject(data, page, temp_form, interceptor)
                injection_time += run_time
                injection_attempts += 1
                difference = injection_time/injection_attempts - normal_time/normal_attempts
                if difference < Methods.WAITING_TIME + 2:
                    # It did not took too much time
                    if difference > Methods.WAITING_TIME - 2:
                        # The injection slowed down the server response
                        results[curr_text_input["name"]].append(char)
                        found_vulnerability = True
                        break
                    if difference < 2:
                        break
    if found_vulnerability:
        # In case of blind OS injection
        write_vulnerability(results, page_result)
        blind_problem.add_page_result(page_result, "\n")


def set_browser(data: Data.Data, page: Data.SessionPage):
    """
    Function acts like proxy, it changes the requests header
    @type request: Methods.selenium_request.Request
    @param request: The current request
    @return: None
    """
    # Block PNG, JPEG and GIF images
    global curr_text_input
    if request.path.endswith(('.png', '.jpg', '.gif')):
        # Save run time
        request.abort()
    elif curr_text_input and request.params \
            and curr_text_input["name"] in request.params.keys():
        # In case of params
        params = dict(request.params)
        params[curr_text_input["name"]] = curr_char + params[curr_text_input["name"]]
        request.params = params


def write_vulnerability(results, page_result):
    """
    Function writes the problem of the form into the page result
    @type results: dict
    @param results: A dictionary of text input and list of chars it didn't filter
    @type page_result: Classes.PageResult
    @param page_result: page result object of the current page
    @return: None
    """
    start_line = ""
    for key in results.keys():
        # For every text input
        if len(results[key]):
            # If the input is vulnerable
            page_result.description += f"{start_line}The parameter '{key}' did not filter the character"
            start_line = ". "  # For the next lines, we want to separate with '. '
            if len(results[key]) == 1:
                page_result.description += ": "
            else:
                page_result.description += "s: "
            # Adding the vulnerable chars
            for char in results[key]:
                if char == "\n":
                    char = "\\n"
                page_result.description += f"'{char}', "
            # Removing last ", "
            page_result.description = page_result.description[:-2]
