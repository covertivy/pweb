#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# Consts:
COLOR = COLOR_MANAGER.rgb(255, 255, 0)

# Global variables
curr_text_input = dict()
curr_char = ""


def check(data: Classes.Data):
    """
    Function checks the website for blind/non-blind OS injection
    @param data: The data object of the program
    @return: None
    """
    ci_results = Classes.CheckResults("Command Injection", COLOR)
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
                ci_results.page_results = "The plugin check routine requires injecting text boxes," \
                                          " read about (-A) in our manual and try again."
                break
            for form in forms:
                try:
                    result = command_injection(page, form, data)
                    if result.problem:
                        # If there is a problem with the page
                        ci_results.page_results.append(result)
                except Exception:
                    continue
    except Exception as e:
        ci_results.page_results = "Something went wrong..."

    data.mutex.acquire()
    data.results.append(ci_results)  # Adding the results to the data object
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


def command_injection(page, form: dict, data: Classes.Data) -> Classes.PageResult:
    """
    Function checks the page for blind/non-blind OS injection
    @param page: The current page
    @param form: The page's action form
    @param data: The data object of the program
    @return: Page result object
    """
    page_result = Classes.PageResult(page, "", "")
    chars_to_filter = ["&", "&&", "|", "||", ";", "\n"]
    text_inputs = Methods.get_text_inputs(form)  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = list()
    check_for_blind = True
    normal_time = 0
    normal_attempts = 0
    global curr_text_input
    global curr_char
    for curr_char in chars_to_filter:
        for curr_text_input in text_inputs:  # In case of more than one text input
            # Getting content of non-blind injection
            content, run_time, check_string = Methods.inject(data, page, form,
                                                             curr_text_input, set_browser,
                                                             "echo " + Methods.CHANGING_SIGN)
            normal_time += run_time
            normal_attempts += 1
            if content.count(check_string) > content.count(f"echo {check_string}"):
                # The web page printed the echo message
                results[curr_text_input["name"]].append(curr_char)
                check_for_blind = False
    if check_for_blind:
        # Didn't find anything
        found_vulnerability = False
        for curr_text_input in text_inputs:
            for char in chars_to_filter:  # In case of more than one text input
                # Getting time of blind injection
                injection_time = 0
                injection_attempts = 0
                while True:
                    content, run_time, s = Methods.inject(data, page, form,
                                                          curr_text_input, set_browser,
                                                          f" ping -c {Methods.WAITING_TIME} 127.0.0.1")
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
            write_vulnerability(results, page_result,
                                "allowed blind OS injection, it did not detected the character")
    else:
        # In case of non-blind OS injection
        write_vulnerability(results, page_result,
                            "allowed OS injection, it did not detected the character")
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
        return Methods.new_browser(data, session_page=page, interceptor=interceptor)  # Getting new browser
    browser = Methods.new_browser(data, interceptor=interceptor)  # Getting new browser
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


def write_vulnerability(results: dict, page_result: Classes.PageResult, problem: str):
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
