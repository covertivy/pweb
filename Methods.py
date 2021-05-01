import random
import time
import Classes
from seleniumwire import webdriver, request as selenium_request
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, element
import json


# ------------- Constants -----------------
CHECK_STRING = "Check"
CHANGING_SIGN = "X1Y"
WAITING_TIME = 10
TEXT_TYPES = ["text", "password"]


# ------------------------- Webdriver methods -------------------------
def new_browser(data: Classes.Data, page: Classes.Page = None, debug: bool = False,
                interceptor=None, remove_alerts: bool = True):
    """
    This function creates a new browser instance with a new session.

    @param data: The data object of the program.
    @type data: Classes.Data
    @param page: The page to be opened with the new browser to initialize cookies and get page (optional).
    @type page: Classes.Page
    @param debug: In case of debugging, in case of True the chrome window will appear.
    @type debug: bool
    @param interceptor: A pointer to an interceptor function.
    @type interceptor: a function
    @param remove_alerts: If True, the browser will remove every alert on `get` and `refresh` methods.
    @type remove_alerts: bool
    @return: Chrome web driver object.
    @rtype: Classes.Browser
    """
    if not data.driver:
        # There is no driver file path.
        raise Exception("There is no driver file path", "\t")
    options = webdriver.ChromeOptions()
    if not debug:
        # If it's not debug, the browser will be headless.
        options.headless = True
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    try:
        browser = Classes.Browser(data.driver, options, remove_alerts)
    except Exception as e:
        # In case of failure, we need to try again
        return new_browser(data, page, debug, interceptor)

    def default_interceptor(request: selenium_request.Request):
        """
        Inner function that acts like a proxy, it removes any requests we don't want.

        @param request: The current request
        @type request: selenium_request.Request
        @return: None
        """
        # Block PNG, JPEG and GIF images.
        if request.path.endswith(('.png', '.jpg', '.gif')):
            request.abort()  # Abort the unwanted request.
    
    # Setting up request interceptor.
    if interceptor:
        browser.request_interceptor = interceptor
    else:
        browser.request_interceptor = default_interceptor
    # Setting long timeout.
    browser.set_page_load_timeout(60)
    if page:
        # If a page was specified.
        if page.parent:
            browser.get(page.parent.url)  # Getting parent URL.
        else:
            browser.get(page.url)  # Getting current URL.
        for cookie in page.cookies:  # Adding cookies.
            browser.add_cookie(cookie)
        # Getting the page again, with the loaded cookies.
        browser.get(page.url)
    return browser


def submit_form(data: Classes.Data, browser: Classes.Browser, inputs: list):
    """
    Function submits the specified form.
    
    @param data: The data object of the program.
    @type data: Classes.Data
    @param browser: The webdriver object.
    @type browser: Classes.Browser
    @param inputs: A list of inputs that belong to a form, already filled with their desired values to submit.
    @type inputs: list
    @return: The time the action took.
    @rtype: float
    """
    # In case of multi-threading, we need to make sure that no one is interrupting anyone.
    data.mutex.acquire()
    # Getting time of normal input.
    start = time.time()
    # The elements we want to submit.
    elements = list()
    if browser.requests:
        del browser.requests
    before_submit = browser.page_source  # There are action forms that use js instead of requests.
    for input_tag in inputs:
        if input_tag.attrs.get("type", None) is not None and input_tag["type"] == "hidden":
            continue
        # Using the inserted value.
        if input_tag.attrs.get("name", None) is not None:
            # Only if the input has a name attribute.
            try:
                element = browser.find_element_by_name(input_tag["name"])
                if input_tag in get_text_inputs(inputs):
                    # You can only send a key to text inputs.
                    element.send_keys(input_tag["value"])
                elements.append({"element": element,
                                "name": input_tag["name"],
                                "type": input_tag["type"]})
            except:
                # Could not send keys to the form for some reason.
                continue
    try:
        for element in elements[::-1]:
            if element["type"] in TEXT_TYPES:
                element["element"].send_keys(Keys.ENTER)  # Sending the form.
            else:
                element["element"].click()
            try:
                # Check if page has somehow loaded an alert, if so we know the form was submitted.
                browser.switch_to.alert
            except:
                continue
            else:
                break
        if not len(browser.requests) and before_submit == browser.page_source:
            # Did not do anything.
            elements[0]["element"].submit()  # Sending the form.
    except Exception as e:
        if not len(browser.requests) and before_submit == browser.page_source:
            # Did not do anything.
            raise e
    finally:
        data.mutex.release()
    return time.time() - start


def enter_cookies(data: Classes.Data, browser: Classes.Browser, url: str):
    """
    This function adds the specified cookies to the browser instance.
    
    @param data: The data object of the program.
    @type data: Classes.Data
    @param browser: The webdriver object.
    @type browser: Classes.Browser
    @param url: The URL to get after inserting the cookies.
    @type url: str
    @return: True - The cookies were added, False - The cookies were not added.
    @rtype: bool
    """
    def add_cookie(a_cookies: dict):
        """
        Inner function that receives one cookie dictionary and checks
        if it already exists in the browser, if not it adds it.
       
        @param a_cookies: The cookie to check.
        @type a_cookies: dict
        @return: None
        """
        for existing_cookie in browser.get_cookies():
            if a_cookies["name"] == existing_cookie["name"]:
                # The cookie is already in the browser.
                for key in a_cookies.keys():
                    existing_cookie[key] = a_cookies[key]
            else:
                # The cookie is not in the browser.
                browser.add_cookie(a_cookies)

    browser.get(url)
    before = list(browser.get_cookies())  # Cookies before adding our cookies.
    if data.cookies:
        # If a cookies file was specified.
        try:
            with open(data.cookies) as json_file:
                cookies = json.load(json_file)  # Load cookies json as a python object.

                # Try to add every cookie that was found.
                if type(cookies) is list:
                    for cookie in cookies:
                        add_cookie(cookie)
                if type(cookies) is dict:
                    add_cookie(cookies)
                
        except Exception:
            # We could not add the cookies.
            return False
        
        # Get page with new cookies.
        browser.get(url)
        if before != browser.get_cookies():
            # The cookies were modified.
            return True
    
    # No changes were made to the cookies.
    return False


# ------------------------------ Helper methods ------------------------------
def get_random_str(content: str):
    """
    This function generates a random string and ensures does not exist in the current page source.
    
    @param content: The content of the current page.
    @type content: str
    @return: The random string.
    @rtype: str
    """
    string = CHECK_STRING
    while True:
        string += str(random.randint(0, 10))
        if string not in content:
            return string


def get_text_inputs(inputs: list):
    """
    This function receives a list of form inputs and extracts all the text inputs from them.
    
    @param inputs: A list of inputs from a form.
    @type inputs: list
    @return: The list of all the text inputs.
    @rtype: list
    """
    text_inputs = list()
    for input_tag in inputs:
        # Using the specified value.
        if input_tag.attrs.get("name", None) is not None and input_tag.attrs.get("type", None) is not None:
            # Only if the input has a name.
            if input_tag["type"] and any(input_tag["type"] == input_type for input_type in TEXT_TYPES):
                # It is a text input tag.
                text_inputs.append(input_tag)
    return text_inputs


def get_forms(content: str):
    """
    This function gets all the forms from a page source html and turns each
    of them into a dictionary which makes the access to the forms and their
    attributes a lot easier. It also contains the inputs within the form to help
    minimize interaction with the bs4 module while working with the output of this function.

    @param content: The page content.
    @type content: str
    @return: List of all the forms.
    @rtype: list
    """
    forms = list()
    for form in BeautifulSoup(content, "html.parser").find_all("form"):
        try:
            # Get the form action (requested URL).
            if form.attrs.get("action", None) is not None:
                action = form["action"].lower()
            else:
                action = ""
            # Get the form method (POST, GET, DELETE, etc).
            # If not specified, GET is the default in HTML.
            if form.attrs.get("method", None) is not None:
                method = form["method"].lower()
            else:
                method = ""
            # Get all form inputs.
            inputs = [input_tag for input_tag in form.find_all("input")]
            # Adding the form to the list.
            forms.append({"form": form, "action": action, "method": method, "inputs": inputs})
        except:
            continue
    return forms


def remove_forms(content: str):
    """
    This function removes all the form tag blocks from the HTML content.

    @param content: The HTML page content.
    @type content: str
    @return: The content without the forms.
    @rtype: str
    """
    content = str(BeautifulSoup(content, "html.parser"))  # The bs4 object changes the HTML tags.
    for form in get_forms(content):
        content = content.replace(str(form["form"]), "")
    return content


def inject(data: Classes.Data, page: Classes.Page, form: dict, interceptor=None):
    """
    This function injects a string into a text box and submits the form.

    @param data: The data object of the program.
    @type data: Classes.Data
    @param page: The current page.
    @type page: Classes.Page
    @param form: A dictionary of inputs of action form.
    @type form: dict
    @param interceptor: A function pointer to an interceptor function.
    @type interceptor: function
    @return: Tuple of (The content of the page, The time it took submit the form, The random string that was used)
    @rtype: tuple
    """
    check_string = ""
    # Creating new browser.
    browser = new_browser(data, page, interceptor=interceptor)
    # The arguments body we want to submit.
    inputs = list()
    for new_form in get_forms(browser.page_source):
        # Getting the updated forms, in case of CSRF tokens.
        if new_form["action"] != form["action"] or new_form["method"] != form["method"]:
            # It is not the right form.
            continue
        new_inputs = new_form["inputs"]
        inputs = form["inputs"]
        check_string = get_random_str(browser.page_source)
        for index in range(len(new_inputs)):
            if not new_inputs[index]["value"]:
                # If there is no string specified.
                if inputs[index]["value"]:
                    # If there is a value in the old input tag.
                    if CHANGING_SIGN in inputs[index]["value"]:
                        # If there is a changing sign in the string.
                        # Replacing the CHANGING SIGN.
                        inputs[index]["value"] = inputs[index]["value"].replace(CHANGING_SIGN, check_string)
                else:
                    # If there is not, generate a random value.
                    inputs[index]["value"] = get_random_str(browser.page_source)
            else:
                # There is a specified value, may be a CSRF token.
                inputs[index]["value"] = new_inputs[index]["value"]
        break  # We found the form we were looking for.
    # Submitting the new form.
    run_time = submit_form(data, browser, inputs)
    content = browser.page_source
    browser.quit()
    return content, run_time, check_string


def fill_input(form: dict, curr_text_input: dict, string: str):
    """
    This function makes a deep copy of a form and fills the specified text input with the specified string.
    
    @param form: The current form.
    @type form: dict
    @param curr_text_input: The current text input tag.
    @type curr_text_input: dict
    @param string: the string we want to use.
    @type string: str
    @return: A deep copy of the form.
    @rtype: dict
    """
    new_form = dict()
    new_form["action"] = str(form["action"])  # Same action.
    new_form["method"] = str(form["method"])  # Same method.
    new_form["form"] = form["form"]  # Same form.
    new_form["inputs"] = list()
    for input_tag in form["inputs"]:
        temp_input_tag = input_tag
        if curr_text_input == temp_input_tag:
            # This is the input we are looking for.
            temp_input_tag["value"] = string
        new_form["inputs"].append(temp_input_tag)
    return new_form
