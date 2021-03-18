#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# --------------- {Consts} ---------------
COLOR = COLOR_MANAGER.rgb(255, 255, 0)

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
                                        "in each of the text inputs, and counting the amount of 'check' "
                                        "strings in compare of the amount of 'echo' strings in the DOM of the resulted"
                                        "page.\n"
                                        "If there are more 'check' than 'echo' it might indicate of a non blind "
                                        "Command injection.")


def check(data):
    """
    Function checks the website for blind/non-blind OS injection
    @type data: Classes.Data
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
    filtered_forms = list()
    if "html" in page.type.lower():
        # We can check only html files
        forms = Methods.get_forms(page.content)  # Getting page forms
        for form in forms:
            if len(Methods.get_text_inputs(form["inputs"])) != 0:
                # If there are no text inputs, it can't be command injection
                filtered_forms.append(form)
    return filtered_forms


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
            temp_form = Methods.fill_input(form, curr_text_input, "echo " + Methods.CHANGING_SIGN)
            # Getting content of non-blind injection
            content, run_time, check_string = Methods.inject(data, page, temp_form, interceptor)
            normal_time += run_time
            normal_attempts += 1
            if content.count(check_string) > content.count(f"echo {check_string}"):
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


def interceptor(request):
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
