#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup

# Consts:
TIME = 10
COLOR = COLOR_MANAGER.rgb(255, 255, 0)

# Global variables
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
                if len(Data.get_text_inputs(form_details)) != 0:
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
    text_inputs = Data.get_text_inputs(form)  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = list()

    def inject(string=None) -> (str, float, str):
        """
        Inner function inject a string into a text box and submit the form
        @param string: The string we want to inject
        @return: Set of (the content of the page, the time it took submit the form)
        """
        browser = None
        try:
            browser = set_browser(data, page)
            check_string = Data.get_random_str(browser.page_source)
            if not string:
                # If there is no string specified, generate a random string
                string = check_string
            elif "X" in string:
                # Replace X with a random string
                string = string.replace("X", check_string)
            c, r, s = Data.submit_form(form["inputs"], curr_text_input, string, data, browser)
        except Exception:
            # In case of failing, try again
            if browser:
                browser.quit()
            return inject(string)
        else:
            browser.quit()
            return c, r, check_string

    check_for_blind = True
    normal_time = 0
    normal_attempts = 0
    global curr_text_input
    global curr_char
    for curr_char in chars_to_filter:
        for curr_text_input in text_inputs:  # In case of more than one text input
            # Getting content of non-blind injection
            content, run_time, s = inject("echo X")
            normal_time += run_time
            normal_attempts += 1
            if content.count(s) > content.count(f"echo {s}"):
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
                    content, run_time, s = inject(f" ping -c {TIME} 127.0.0.1")
                    injection_time += run_time
                    injection_attempts += 1
                    difference = injection_time/injection_attempts - normal_time/normal_attempts
                    if difference < TIME + 2:
                        # It did not took too much time
                        if difference > TIME - 2:
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
