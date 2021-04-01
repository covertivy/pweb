import random
import time
import Classes
from seleniumwire import webdriver, request as selenium_request
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import json

# ------------- {Consts} -----------------
CHECK_STRING = "Check"
CHANGING_SIGN = "X1Y"
WAITING_TIME = 10
TEXT_TYPES = ["text", "password"]

# ------------------------- {Browser methods} -------------------------


def new_browser(data, page=None, debug=False, interceptor=None, remove_alerts=True):
    """
    Function creates a new browser instance for new session.
    @type data: Classes.Data
    @param data: The data object of the program.
    @type page: Classes.Page
    @param page: The browser needs the cookies and URL.
    @type debug: bool
    @param debug: In case of debugging, True will make the chromium window appear.
    @type interceptor: def
    @param interceptor: A pointer to an interceptor.
    @type remove_alerts: bool
    @param remove_alerts: If True, the browser will remove every alert
    @rtype: Classes.Browser
    @return: Chrome driver object.
    """
    if not data.driver:
        # There is no driver file path.
        raise Exception("There is no driver file path", "\t")
    options = webdriver.ChromeOptions()
    if not debug:
        # If it's not debug, the chromium will be headless.
        options.headless = True
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    try:
        browser = Classes.Browser(data.driver, options, remove_alerts)
    except Exception as e:
        # In case of failure, we need to try again
        return new_browser(data, page, debug, interceptor)

    def default_interceptor(request):
        """
        Inner function acts like proxy, it aborts every requests that we don't want
        @type request: selenium_request.Request
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
    if page:
        # Only if a page was specified
        if page.parent:
            browser.get(page.parent.url)  # Getting parent URL
        else:
            browser.get(page.url)  # Getting current URL
        for cookie in page.cookies:  # Adding cookies
            browser.add_cookie(cookie)
        # Getting the page again, with the cookies
        browser.get(page.url)
    return browser


def submit_form(inputs, browser, data):
    """
    Function submits a specified form
    @type inputs: list
    @param inputs: A list of inputs of action form, already full with values
    @type browser: webdriver.Chrome
    @param browser: The webdriver object
    @type data: Classes.Data
    @param data: The data object of the program
    @rtype: float
    @return: The time the action took.
    """
    # In case of multi-threading, we need to make sure that no one is interrupting anyone
    data.mutex.acquire()
    # Sending the request
    start = time.time()  # Getting time of normal input
    # The elements we want to submit
    elements = list()
    if browser.requests:
        del browser.requests
    for input_tag in inputs:
        if "type" in input_tag.keys() and input_tag['type'] == "hidden":
            continue
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            element = browser.find_element_by_name(input_tag["name"])
            try:
                if input_tag in get_text_inputs(inputs):
                    # You can send key only to text inputs
                    element.send_keys(input_tag["value"])
                elements.append({"element": element,
                                 "name": input_tag["name"],
                                 "type": input_tag["type"]})
            except Exception as e:
                # Could not send key to the form for some reason
                continue
    try:
        for element in elements[::-1]:
            if element["type"] in TEXT_TYPES:
                element["element"].send_keys(Keys.ENTER)  # Sending the form
            else:
                element["element"].click()
        if not len(browser.requests):
            # Did not do anything
            elements[0]["element"].submit()  # Sending the form
    except Exception as e:
        data.mutex.release()
        if not len(browser.requests):
            # Did not do anything
            raise e
    else:
        data.mutex.release()
    run_time = time.time() - start
    return run_time


def enter_cookies(data, browser, url):
    """
    Function adds the specified cookie to the browser.
    @type data: Classes.Data
    @param data: The data object of the program.
    @type browser: webdriver.Chrome
    @param browser: The webdriver object
    @type url: str
    @param url: The current URL
    @rtype: bool
    @return: True - The cookies were added, False - The cookies were not added
    """
    def add_cookie(a_cookie):
        """
        Inner function enter one cookie dictionary and checks if it was already in the browser
        @type a_cookie: dict
        @param a_cookie: Specified cookie
        @return: None
        """
        for b_cookie in browser.get_cookies():
            if a_cookie["name"] == b_cookie["name"]:
                # The cookies already in browser
                for key in a_cookie.keys():
                    b_cookie[key] = a_cookie[key]
            else:
                # The cookie is not in the browser
                browser.add_cookie(a_cookie)
    browser.get(url)
    before = list(browser.get_cookies())
    if data.cookies:
        try:
            with open(data.cookies) as json_file:
                cookies = json.load(json_file)
                if type(cookies) is list:
                    for cookie in cookies:
                        add_cookie(cookie)
                if type(cookies) is dict:
                    add_cookie(cookies)
        except Exception:
            return False
        browser.get(url)
        if before != browser.get_cookies():
            # Changed the cookies
            return True
    return False

# ------------------------------ {Helper methods} ------------------------------


def get_random_str(content):
    """
    Function generates a random string which is not in the current page
    @type content: str
    @param content: The content of the current page
    @rtype: str
    @return: random string
    """
    string = CHECK_STRING
    while True:
        string += str(random.randint(0, 10))
        if string not in content:
            return string


def get_text_inputs(inputs):
    """
    Function gets the text input names from a form
    @type inputs: list
    @param inputs: A list of inputs of action form
    @rtype: list
    @return: list of text inputs
    """
    text_inputs = list()
    for input_tag in inputs:
        # Using the specified value
        if "name" and "type" in input_tag.keys():
            # Only if the input has a name
            if input_tag["type"] and \
                    any(input_tag["type"] == input_type for input_type in TEXT_TYPES):
                # It is a text input tag
                text_inputs.append(input_tag)
    return text_inputs


def get_forms(content):
    """
    Function gets the forms of a page
    @type content: str
    @param content: The page content
    @rtype: list
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


def remove_forms(content):
    """
    Function removes the form code blocks from the HTML content
    @type content: str
    @param content: The HTML page content
    @rtype: str
    @return: The content without the forms
    """
    content = str(BeautifulSoup(content, "html.parser"))  # The bs4 object changes the HTML tags.
    for form in get_forms(content):
        content = content.replace(str(form["form"]), "")
    return content


def inject(data, page, form, interceptor=None):
    """
    Function inject a string into a text box and submit the form
    @type data: Classes.Data
    @param data: The data object of the program
    @type page: Classes.Page
    @param page: The current page
    @type form: dict
    @param form: A dictionary of inputs of action form
    @param interceptor: A pointer to an interceptor
    @rtype: set
    @return: Set of (The content of the page, The time it took submit the form, The random string that was used)
    """
    check_string = ""
    # Creating new browser
    browser = new_browser(data, page, interceptor=interceptor)
    # The arguments body we want to submit
    inputs = list()
    for new_form in get_forms(browser.page_source):
        # Getting the updated forms, in case of CSRF tokens
        if new_form["action"] != form["action"] or new_form["method"] != form["method"]:
            # It is not the right form
            continue
        new_inputs = new_form["inputs"]
        inputs = form["inputs"]
        check_string = get_random_str(browser.page_source)
        for index in range(len(new_inputs)):
            if not new_inputs[index]["value"]:
                # If there is no string specified
                if inputs[index]["value"]:
                    # If there is a value in the old input tag
                    if CHANGING_SIGN in inputs[index]["value"]:
                        # If there is a changing sign in the string
                        # Replacing the CHANGING SIGN
                        inputs[index]["value"] = inputs[index]["value"].replace(CHANGING_SIGN, check_string)
                else:
                    # If there is not, generate a random value
                    inputs[index]["value"] = get_random_str(browser.page_source)
            else:
                # There is a specified value, may be a CSRF token
                inputs[index]["value"] = new_inputs[index]["value"]
        break  # We found the form we were looking for
    # Submitting the new form
    run_time = submit_form(inputs, browser, data)
    content = browser.page_source
    browser.quit()
    return content, run_time, check_string


def fill_input(form, curr_text_input, string):
    """
    Function make a deep copy of a form and fill the specified text input with the string
    @type form: dict
    @param form: The current form
    @type curr_text_input: dict
    @param curr_text_input: The current text input tag
    @type string: str
    @param string: the string we want to use
    @rtype: dict
    @return: A deep copy of the form
    """
    new_form = dict()
    new_form["action"] = str(form["action"])  # Same action
    new_form["method"] = str(form["method"])  # Same method
    new_form["form"] = form["form"]  # Same form
    new_form["inputs"] = list()
    for input_tag in form["inputs"]:
        new_input_tag = dict(input_tag)  # Deep copy to the input tag
        if curr_text_input == new_input_tag:
            # This is the input we are looking for
            new_input_tag["value"] = string
        new_form["inputs"].append(new_input_tag)
    return new_form
