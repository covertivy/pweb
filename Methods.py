import random
import time
import Classes
from seleniumwire import webdriver, request as selenium_request
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# ------------------------------ Consts ------------------------------
CHECK_STRING = "Check"
CHANGING_SIGN = "X1Y"
WAITING_TIME = 10

# ------------------------- Browser methods -------------------------


def new_browser(data: Classes.Data, session_page: Classes.SessionPage = None,
                debug: bool = False, interceptor=None) -> webdriver.Chrome:
    """
    Function creates a new browser instance for new session
    @param data: The data object of the program
    @param session_page: In case session, the browser needs the cookies and URL
    @param debug: In case of debugging, True will make the chromium window appear
    @param interceptor:
    @return: Chrome driver object
    """
    if not data.driver:
        # There is no driver file path
        raise Exception("There is no driver file path", "\t")
    options = webdriver.ChromeOptions()
    if not debug:
        # If it's not debug, the chromium will be headless
        options.add_argument("headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    try:
        browser = webdriver.Chrome(executable_path=data.driver, options=options)
    except Exception as e:
        # In case of failure, we need to try again
        return new_browser(data, session_page, debug)

    def default_interceptor(request: selenium_request):
        """
        Inner function acts like proxy, it aborts every requests that we don't want
        @param request: The current request
        @return: None
        """
        # Block PNG, JPEG and GIF images
        if request.path.endswith(('.png', '.jpg', '.gif')):
            # Save run time
            request.abort()
    # Setting request interceptor
    if interceptor:
        browser.request_interceptor = interceptor
    else:
        browser.request_interceptor = default_interceptor
    # Setting long timeout
    browser.set_page_load_timeout(60)
    if session_page:
        # In case of session page
        browser.get(session_page.parent)  # Getting parent URL
        for cookie in session_page.cookies:  # Adding cookies
            browser.add_cookie(cookie)
        # Getting the page again, with the cookies
        browser.get(session_page.url)
    return browser


def submit_form(inputs: list, curr_text_input: dict,
                text: str, browser: webdriver.Chrome, data: Classes.Data) -> (str, float, list):
    """
    Function submits a specified form
    @param inputs: A list of inputs of action form
    @param curr_text_input: The current text input we are checking
    @param text: The we want to implicate into the current text input
    @param browser: The webdriver object
    @param data: The data object of the program
    @return: The content of the resulted page, the time the action took, the random strings
    """
    # The arguments body we want to submit
    inputs = [dict(input_tag) for input_tag in inputs]  # Deep copy of the list
    check_strings = list()  # List of random strings
    for input_tag in inputs:
        if not input_tag["value"]:
            # If the input tag has no value
            if "name" in input_tag.keys() and input_tag["name"] == curr_text_input["name"]:
                # Only if the input has the current name
                input_tag["value"] = text
            else:
                # If there is no value
                string = get_random_str(browser.page_source)
                input_tag["value"] = string
                check_strings.append(string)
    # In case of multi-threading, we need to make sure that no one is interrupting anyone
    data.mutex.acquire()
    # Sending the request
    start = time.time()  # Getting time of normal input
    # The elements we want to submit
    elements = list()
    del browser.requests
    try:
        for input_tag in inputs:
            if "type" in input_tag.keys() and input_tag['type'] == "hidden":
                continue
            # Using the specified value
            if "name" in input_tag.keys():
                # Only if the input has a name
                element = browser.find_element_by_name(input_tag["name"])
                element.send_keys(input_tag["value"])
                elements.append({"element": element, "name": input_tag["name"], "type": input_tag["type"]})
        for element in elements:
            if element["type"] == "text":
                element["element"].send_keys(Keys.ENTER)  # Sending the form
        if not len(browser.requests):
            # Did not do anything
            elements[0]["element"].submit()  # Sending the form
    except Exception as e:
        if not len(browser.requests):
            # Did not do anything
            raise e
    run_time = time.time() - start
    data.mutex.release()
    content = browser.page_source
    return content, run_time, check_strings

# ------------------------------ Helper methods ------------------------------


def get_random_str(content: str) -> str:
    """
    Function generates a random string which is not in the current page
    @param content: The content of the current page
    @return: random string
    """
    while True:
        string = CHECK_STRING + str(random.randint(0, 1000))
        if string not in content:
            return string


def get_text_inputs(form: dict) -> list:
    """
    Function gets the text input names from a form
    @param form: A dictionary of inputs of action form
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


def get_forms(content: str) -> list:
    """
    Function gets the forms of a page
    @param content: The page content
    @return: List of the forms
    """
    forms = list()
    for form in BeautifulSoup(content, "html.parser").find_all("form"):
        try:
            # Get the form action (requested URL)
            action = form.attrs.get("action").lower()
            # Get the form method (POST, GET, DELETE, etc)
            # If not specified, GET is the default in HTML
            method = form.attrs.get("method", "get").lower()
            # Get all form inputs
            inputs = []
            for input_tag in form.find_all("input"):
                input_dict = dict()
                # Get type of input form control
                input_type = input_tag.attrs.get("type")
                # Get name attribute
                input_name = input_tag.attrs.get("name")
                # Get the default value of that input tag
                input_dict["value"] = input_tag.attrs.get("value", "")
                # Add everything to that list
                if input_type:
                    input_dict["type"] = input_type
                if input_name:
                    input_dict["name"] = input_name
                inputs.append(input_dict)
            # Adding the form to the list
            forms.append({"action": action, "method": method,
                          "inputs": inputs, "form": form})
        except Exception:
            continue
    return forms


def inject(data: Classes.Data, page: Classes.Page, form: dict,
           curr_text_input: dict, setting_browser, string=None) -> (str, float, str):
    """
    Function inject a string into a text box and submit the form
    @param data: The data object of the program
    @param page: The current page
    @param curr_text_input: The current text input we are checking
    @param form: A dictionary of inputs of action form
    @param setting_browser: A pointer to a function that take (data, page) and returns browser
    @param string: The string we want to inject
    @return: Set of (the content of the page, the time it took submit the form, the random string that was used)
    """
    browser = None
    try:
        browser = setting_browser(data, page)
        check_string = get_random_str(browser.page_source)
        if not string:
            # If there is no string specified, generate a random string
            string = check_string
        elif CHANGING_SIGN in string:
            # Replace X with a random string
            string = string.replace(CHANGING_SIGN, check_string)
        # Getting the updated form, in case of CSRF tokens
        forms = get_forms(content=browser.page_source)
        curr_form = dict()
        for curr_form in forms:
            if curr_form["action"] == form["action"] and curr_form["method"] == form["method"]:
                # Have the same action and method
                break
        # Submitting the new form
        content, run_time, strings = submit_form(curr_form["inputs"], curr_text_input, string, browser, data)
    except Exception:
        # In case of failing, try again
        if browser:
            browser.quit()
        return inject(data, page, form, curr_text_input, string)
    else:
        # Success in submitting the form
        browser.quit()
        return content, run_time, check_string
