#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
import random

COLOR = COLOR_MANAGER.rgb(0, 255, 200)
CHECK_STRING = "check"
OUTSIDE_URL = "https://google.com"
current_referer = None


def check(data: Data.Data):
    """
    Function checks the website for CSRF
    @param data: The data object of the program
    @return: None
    """
    csrf_results = Data.CheckResults("CSRF", COLOR)
    data.mutex.acquire()
    pages = list(data.pages)  # Achieving the pages
    agreement = data.agreement
    data.mutex.release()
    try:
        # Filtering the pages list
        pages = filter_forms(pages, agreement)
        # [(page object, form dict),...]
        if len(pages):
            # There are pages with at least one text input
            if data.agreement:
                # The user specified his agreement
                for page, form in pages:
                    browser = set_browser(data, page)
                    try:
                        result = csrf(page, form, data, browser)
                        if result.problem:
                            # If there is a problem with the page
                            csrf_results.page_results.append(result)
                    except Exception:
                        pass
                    browser.close()
            else:
                # The user did not specified his agreement
                # and there is a vulnerable page
                csrf_results.page_results = "The plugin check routine requires submitting web forms," \
                                            " read about (-A) in our manual and try again."
    except Exception:
        csrf_results.page_results = "Something went wrong..."
    data.mutex.acquire()
    data.results.append(csrf_results)  # Adding the results to the data object
    data.mutex.release()


def get_forms(content: str):
    form_dict = list()
    forms = BeautifulSoup(content, "html.parser").find_all("form")  # Getting page forms
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
            form_dict.append(form_details)
        except:
            continue
    return form_dict


def filter_forms(pages: list, agreement: bool) -> list:
    """
    Function filters the pages that has an action form
    @param pages:List of pages
    @param agreement: The specified user's agreement
    @return: List of pages that has an action form
    """
    filtered_pages = list()
    for page in pages:
        if "html" not in page.type.lower():
            # If it is a non-html page we can not check for command injection
            continue
        if type(page) is not Data.SessionPage:
            # If the page is not a session page
            continue
        for form in get_forms(page.content):
            # Adding the page and it's form to the list
            filtered_pages.append((page, form))
            if not agreement:
                # The user did not specified his agreement
                return filtered_pages
    return filtered_pages


def csrf(page: Data.SessionPage, form: dict, data: Data.Data, browser) -> Data.PageResult:
    """
    Function checks the page for csrf
    @param page: The current page
    @param form: The page's action form
    @param data: The data object of the program
    @param browser: The Chrome browser object
    @return: Page result object
    """
    page_result = Data.PageResult(page, "", "")
    vulnerability = [False, False, False]
    # Checking for csrf tokens
    request_headers = page.request.headers
    response_headers = page.request.response.headers
    if response_headers.get("Set-Cookie") and \
            ("SameSite=Strict" in response_headers.get("Set-Cookie") or
             "csrf" in response_headers.get("Set-Cookie")) or request_headers.get("X-Csrf-Token"):
        # Found a SameSite or csrf token in response header
        return page_result
    # Setting new browser
    token = False
    try:
        for new_form in get_forms(browser.page_source):
            if new_form["action"] == form["action"]:
                # Same form
                for input_tag in form["inputs"]:
                    # Using the specified value
                    if "name" in input_tag.keys() and input_tag["value"]:
                        # Only if the input has a name and a value
                        for new_input_tag in new_form["inputs"]:
                            if "name" in new_input_tag.keys() and new_input_tag["name"] == input_tag["name"]:
                                # If the input tags have the same name
                                if new_input_tag["value"] != input_tag["value"]:
                                    # If the input tags have different values
                                    token = True
                                    break
                        if token:
                            # No need to look for another input tag
                            break
                break  # There is only one fitting form
    except Exception:
        pass
    if token:
        # Found a csrf token
        return page_result
    # Join the url with the action (form request URL)
    if form["method"] == "get":
        # Dangerous by itself
        vulnerability[0] = True
    # Getting normal content
    normal_content = get_response(form, page.url, data, browser)\
        .replace(page.url, "").replace(OUTSIDE_URL, "").replace(page.parent.url, "")
    # Getting redirected content
    browser.get(page.url)
    referer_content = get_response(form, OUTSIDE_URL, data, browser)\
        .replace(page.url, "").replace(OUTSIDE_URL, "").replace(page.parent.url, "")
    if normal_content == referer_content:
        # Does not filter referer header
        vulnerability[1] = True
    else:
        # Getting local redirected content
        browser.get(page.url)
        referer_content = get_response(form, page.parent.url, data, browser)\
            .replace(page.url, "").replace(OUTSIDE_URL, "").replace(page.parent.url, "")
        if normal_content == referer_content:
            # Does not filter referer header
            vulnerability[2] = True
    if sum(vulnerability):
        # If there is a vulnerability
        write_vulnerability(vulnerability, page_result)
    return page_result


def get_response(form: dict, referer: str, data: Data.Data, browser) -> str:
    """
    Function submits a specified form and gets the result content
    @param form: A dictionary of inputs of action form
    @param referer: A specified referer address
    @param data: The data object of the program
    @param browser: The browser object
    @return: The content of the resulted page
    """
    content = ""
    try:
        inputs = list()
        check_strings = list()
        for input_tag in form["inputs"]:
            # Using the specified value
            new_input_tag = dict(input_tag)
            if "name" in new_input_tag.keys():
                # Only if the input has a name
                if not new_input_tag["value"]:
                    # There is no value to the input tag
                    while True:
                        # While the random string in the list
                        check_string = CHECK_STRING + str(random.randint(1, 200))
                        if check_string not in check_strings:
                            break
                    check_strings.append(check_string)
                    new_input_tag["value"] = check_string
            inputs.append(new_input_tag)
        # Sending the request
        global current_referer
        current_referer = referer
        data.submit_form(inputs, browser)
        current_referer = None
        content = browser.page_source
        for string in check_strings:
            # In case that the random string is in the content
            content = content.replace(string, "")
    except Exception as e:
        pass
    finally:
        return content


def set_browser(data: Data.Data, page: Data.SessionPage):
    """
    Function Sets up a new browser, sets its cookies and checks if the cookies are valid
    @param data: The data object of the program
    @param page: The current page
    @return: The browser object
    """
    url = page.url
    if page.parent:
        # If the page is not first
        url = page.parent.url
    browser = data.new_browser()  # Getting new browser
    browser.request_interceptor = interceptor  # Setting request interceptor
    browser.set_page_load_timeout(60)  # Setting long timeout
    browser.get(url)  # Getting parent URL
    for cookie in page.cookies:  # Adding cookies
        browser.add_cookie(cookie)
    # Getting the page again, with the cookies
    browser.get(page.url)
    return browser


def interceptor(request):
    """
    Function acts like proxy, it changes the requests header
    @param request: The current request
    @return: None
    """
    # Block PNG, JPEG and GIF images
    global current_referer
    if request.path.endswith(('.png', '.jpg', '.gif')):
        # Save run time
        request.abort()
    elif current_referer:
        # In case of referer specified
        del request.headers['Referer']  # Remember to delete the header first
        request.headers['Referer'] = current_referer  # Spoof the referer


def write_vulnerability(results: list, page_result: Data.PageResult):
    """
    Function writes the problem and the solution of every problem that is found for a page
    @param results: a dictionary of text input and list of chars it didn't filter
    @param page_result: page result object of the current page
    @return: None
    """
    lines = sum(results)
    padding = " " * 25
    if results[0]:
        # GET problem
        page_result.problem += f"The use of GET request when submitting the form might be vulnerable."
        page_result.solution += f"You can change the method of the request to POST.\n{padding} "
        if lines > 1:
            # More than one line
            page_result.problem += "\n" + padding
    if results[1] or results[2]:
        # Referer problem
        page_result.solution += "You can validate the 'Referer' header of the request," \
                                f" so it will perform only actions from the current page.\n{padding} "
        if results[1]:
            # Referer to outside of the domain
            page_result.problem += "The page did not detect the 'Referer' header, which was outside of your domain."
        else:
            # Referer to inside of the domain
            page_result.problem += "The page did not detect the 'Referer' header," \
                                   f" which was not the same page that has the vulnerable form."
    page_result.solution += "The best way to prevent CSRF vulnerability is to use CSRF Tokens, " \
                            f"\n{padding} read more about it in: 'https://portswigger.net/web-security/csrf/tokens'."
