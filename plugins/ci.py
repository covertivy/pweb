#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
import time

# Consts:
COLOR = COLOR_MANAGER.rgb(255, 255, 0)
curr_text_input = dict()
curr_char = ""


def check(data: Data.Data):
    """
    Function checks the website for blind/non-blind OS injection
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
                ci_results.page_results = "The plugin check routine requires injecting text boxes," \
                                          " read about (-A) in our manual and try again."
    except Exception as e:
        ci_results.page_results = "Something went wrong..."

    data.mutex.acquire()
    data.results.append(ci_results)  # Adding the results to the data object
    data.mutex.release()


def filter_forms(pages: list, aggressive: bool) -> list:
    """
    Function filters the pages that has an action form
    @param pages:List of pages
    @param aggressive: The specified user's agreement
    @return: List of pages that has an action form
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


def command_injection(page, form: dict, data: Data.Data) -> Data.PageResult:
    """
    Function checks the page for blind/non-blind OS injection
    @param page: The current page
    @param form: The page's action form
    @param data: The data object of the program
    @return: Page result object
    """
    page_result = Data.PageResult(page, "", "")
    chars_to_filter = ["&", "&&", "|", "||", ";", "\n"]
    browser = set_browser(data, page)
    text_inputs = get_text_inputs(form)  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = list()
    check_for_blind = True
    average_time = 0
    attempts = 0
    global curr_text_input
    global curr_char
    for curr_char in chars_to_filter:
        for curr_text_input in text_inputs:  # In case of more than one text input
            # Getting content of non-blind injection
            browser.get(page.url)
            string = Data.get_random_str(browser.page_source)
            start = time.time()  # Getting time of normal input
            content = submit_form([dict(input_tag) for input_tag in form["inputs"]],
                                  f"echo {string}", data, browser)
            normal_time = time.time() - start
            average_time += normal_time
            attempts += 1
            if content.count(string) > content.count(f"echo {string}"):
                # The web page printed the echo message
                results[curr_text_input["name"]].append(curr_char)
                check_for_blind = False
    average_time /= attempts  # Getting average response time
    if check_for_blind:
        # Didn't find anything
        browser.quit()
        browser = set_browser(data, page)
        found_vulnerability = False
        for curr_text_input in text_inputs:
            for char in chars_to_filter:  # In case of more than one text input
                # Getting time of blind injection
                again = True
                while again:
                    again = False
                    browser.get(page.url)
                    start = time.time()
                    submit_form([dict(input_tag) for input_tag in form["inputs"]],
                                f" ping -c 5 127.0.0.1", data, browser)
                    injection_time = time.time() - start
                    if injection_time - average_time > 7:
                        # Too much time
                        again = True
                        browser.quit()
                        browser = set_browser(data, page)
                    elif injection_time - average_time > 3:
                        # The injection slowed down the server response
                        results[curr_text_input["name"]].append(char)
                        found_vulnerability = True

        if found_vulnerability:
            # In case of blind OS injection
            write_vulnerability(results, page_result,
                                "allowed blind OS injection, it did not detected the character")
    else:
        # In case of non-blind OS injection
        write_vulnerability(results, page_result,
                            "allowed OS injection, it did not detected the character")
    browser.quit()
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
        return Data.new_browser(data, session_page=page, interceptor=interceptor)  # Getting new browser
    browser = Data.new_browser(data, interceptor=interceptor)  # Getting new browser
    browser.get(page.url)
    return browser


def interceptor(request):
    """
    Function acts like proxy, it changes the requests header
    @param request: The current request
    @return: None
    """
    # Block PNG, JPEG and GIF images
    global curr_text_input
    if request.path.endswith(('.png', '.jpg', '.gif')):
        # Save run time
        request.abort()
    elif curr_text_input and request.params and curr_text_input["name"] in request.params.keys():
        # In case of params
        params = dict(request.params)
        params[curr_text_input["name"]] = curr_char + params[curr_text_input["name"]]
        request.params = params


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


def submit_form(inputs: list, text: str, data: Data.Data, browser):
    """
    Function submits a specified form
    @param inputs: A list of inputs of action form
    @param text: The we want to implicate into the current text input
    @param data: The data object of the program
    @param browser: The webdriver object
    @return: The content of the resulted page
    """
    # The arguments body we want to submit
    for input_tag in inputs:
        # Using the specified value
        if "name" in input_tag.keys():
            if input_tag["name"] == curr_text_input["name"]:
                # Only if the input has the current name
                input_tag["value"] = text
            elif not input_tag["value"]:
                input_tag["value"] = Data.get_random_str(browser.page_source)
    # Sending the request
    data.submit_form(inputs, browser)
    content = browser.page_source
    return content


def write_vulnerability(results: dict, page_result: Data.PageResult, problem: str):
    """
    Function writes the problem and the solution of every problem that is found for a page
    @param results: a dictionary of text input and list of chars it didn't filter
    @param page_result: page result object of the current page
    @param problem: string of found problem
    @return: None
    """
    for key in results.keys():
        # For every text input
        if len(results[key]):
            # If the input is vulnerable
            page_result.problem += f"The text parameter '{key}' {problem}"
            page_result.solution += f"Validate the input of the text parameter '{key}' from "
            if len(results[key]) == 1:
                page_result.problem += ": "
                page_result.solution += "this character."
            else:
                page_result.problem += "s: "
                page_result.solution += "those characters."
            # Adding the vulnerable chars
            for char in results[key]:
                if char == "\n":
                    char = "\\n"
                page_result.problem += f"'{char}', "
            # Removing last ", "
            page_result.problem = page_result.problem[:-2]
