#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# ---------------------------------- {Consts} --------------------------
COLOR = COLOR_MANAGER.rgb(100, 100, 255)
OUTSIDE_URL = "https://google.com"

# ---------------------------- {Global variables} ----------------------------
current_referer = None
problem_get = Classes.CheckResult("The use of GET request when submitting the form might be vulnerable.",
                                  "You can change the method of the request to POST.",
                                  "The plugin checks the DOM of the action form,\n"
                                  "in case of GET method, we recommend to change it or make sure it is secure.\n"
                                  "For a CSRF attacker it will be much harder to use this form for his attack"
                                  " if the form uses POST method.")
problem_referer = Classes.CheckResult("The form submission did not detect the 'Referer' header,"
                                      " which was not the same page that has the vulnerable form.",
                                      "You can validate the 'Referer' header of the request,"
                                      " so it will perform only actions from the current page.",
                                      "The plugin submits the action form with 3 different referer header values,\n"
                                      "first one is the URL of the page, the second one is https://google.com, "
                                      "and the third one is another page from the session, with the same domain.\n"
                                      "If the first result is the same as the other results, "
                                      "it might point out that the action form is letting other sources to use it.")
success_message = ""


def check(data):
    """
    This function checks the website for CSRF.

    @param data: The data object of the program.
    @type data: Classes.Data
    @return: None
    """
    csrf_results = Classes.CheckResults("CSRF", COLOR)
    try:
        data.mutex.acquire()
        pages = data.pages  # Achieving the pages.
        aggressive = data.aggressive
        data.mutex.release()
        for page in pages:
            # Getting the forms of each page.
            forms = filter_forms(page)
            if forms and not aggressive:
                # The user did not specified his agreement.
                # and there is a vulnerable page.
                csrf_results.warning = "The plugin check routine requires injecting text boxes," \
                                            " read about (-A) in our manual and try again."
                break
            for form in forms:
                try:
                    csrf(page, form, data)
                except Exception:
                    continue
    except Exception as e:
        csrf_results.error = "Something went wrong..."

    if problem_get.page_results or problem_referer.page_results:
        # Found a vulnerability.
        csrf_results.warning = "WARNING: The CSRF vulnerability is relevant only for action" \
                               " forms that involve the user's data."
    csrf_results.success = success_message
    csrf_results.results.append(problem_get)
    csrf_results.results.append(problem_referer)
    csrf_results.conclusion = "The best way to prevent CSRF vulnerability is to use CSRF Tokens, " \
                              "read more about it in: 'https://portswigger.net/web-security/csrf/tokens'."
    data.mutex.acquire()
    data.results_queue.put(csrf_results)  # Adding the results to the queue.
    data.mutex.release()


def filter_forms(page):
    """
    This function filters the pages that has an action form.

    @param page: The current page.
    @type page: Classes.Page
    @return: List of forms.
    @rtype: list
    """
    filtered_forms = list()
    if "html" in page.type.lower() and page.is_session:
        # The only thing we need is a HTML session page with a form.
        for form in Methods.get_forms(page.content):
            # Adding the page and it's form to the list.
            filtered_forms.append(form)
    return filtered_forms


def csrf(page, form, data):
    """
    This function checks the page for csrf.

    @param page: The current page.
    @type page: : Classes.SessionPage
    @param form: The page's action form.
    @type form: dict
    @param data: The data object of the program.
    @type data: Classes.Data
    @return: None
    """
    page_result = Classes.PageResult(page, f"Action form: '{form['action']}'")
    global success_message
    # Checking for csrf tokens.
    request_headers = page.request.headers
    response_headers = page.request.response.headers
    if response_headers.get("Set-Cookie") and \
            ("SameSite=Strict" in response_headers.get("Set-Cookie") or
             "csrf" in response_headers.get("Set-Cookie")) or request_headers.get("X-Csrf-Token"):
        # Found a SameSite or csrf token in response header.
        success_message = "The website is using CSRF prevention methods in it's response headers."
        return
    # Setting new browser.
    browser = Methods.new_browser(data, page, interceptor=interceptor)
    token = False
    try:
        for new_form in Methods.get_forms(browser.page_source):
            if new_form["action"] != form["action"]:
                # Not the same form.
                continue
            for input_tag in form["inputs"]:
                # Using the specified value.
                if "name" in input_tag.keys() and input_tag["value"]:
                    # Only if the input has a name and a value.
                    for new_input_tag in new_form["inputs"]:
                        if "name" in new_input_tag.keys() and new_input_tag["name"] == input_tag["name"]:
                            # If the input tags have the same name.
                            if new_input_tag["value"] != input_tag["value"]:
                                # If the input tags have different values.
                                token = True
                                break
                    if token:
                        # No need to look for another input tag.
                        break
                break  # There is only one fitting form.
    except Exception:
        pass
    browser.quit()
    if token:
        # Found a csrf token.
        success_message = "The website is using the CSRF Tokens method in it's forms."
        return
    # Join the url with the action (form request URL).
    if form["method"] == "get":
        # Dangerous by itself.
        problem_get.add_page_result(page_result, ", ")
    # Getting normal content.
    normal_content = get_response(form["inputs"], page.url, data, page)
    # Getting redirected content.
    referer_content = get_response(form["inputs"], OUTSIDE_URL, data, page)
    if normal_content == referer_content:
        # Does not filter referer header.
        problem_referer.add_page_result(page_result, ", ")
    elif page.parent:
        # Getting local redirected content.
        referer_content = get_response(form["inputs"], page.parent.url, data, page)
        if normal_content == referer_content:
            # Does not filter referer header.
            problem_referer.add_page_result(page_result, ", ")


def get_response(inputs, referer, data, page):
    """
    This function submits a specified form and gets the result content.

    @param inputs: A list of inputs of action form.
    @type inputs: list
    @param referer: A specified referer address.
    @type referer: str
    @param data: The data object of the program.
    @type data: Classes.Data
    @param page: The current page.
    @type page: Classes.SessionPage
    @return: The content of the resulted page.
    @rtype: str
    """
    content = ""
    try:
        # Sending the request.
        global current_referer
        current_referer = referer
        browser = Methods.new_browser(data, page, interceptor=interceptor)
        check_strings = list()
        inputs = [dict(input_tag) for input_tag in inputs]
        for input_tag in inputs:
            # Using the specified value.
            if input_tag in Methods.get_text_inputs(inputs):
                # Only if the input has a name.
                if not input_tag["value"]:
                    # There is no value to the input tag.
                    check_string = Methods.get_random_str(browser.page_source +
                                                          " ".join(str(x) for x in check_strings))
                    check_strings.append(check_string)
                    input_tag["value"] = check_string
        Methods.submit_form(data, browser, inputs)
        current_referer = None
        content = browser.page_source
        browser.quit()
        for string in check_strings:
            # In case that the random string is in the content.
            content = content.replace(string, "")
        # In case of referrers in content.
        content = content.replace(page.url, "").replace(OUTSIDE_URL, "")
        if page.parent:
            content = content.replace(page.parent.url, "")
    except Exception as e:
        pass
    finally:
        return Methods.remove_forms(content)


def interceptor(request):
    """
    This function acts like proxy, it changes the requests header.

    @param request: The current request.
    @type request: Methods.selenium_request.Request
    @return: None
    """
    # Block PNG, JPEG and GIF images.
    global current_referer
    if request.path.endswith(('.png', '.jpg', '.gif')):
        # Save run time.
        request.abort()
    elif current_referer:
        # In case of referer specified.
        del request.headers['Referer']  # Remember to delete the header first.
        request.headers['Referer'] = current_referer  # Spoof the referer.
