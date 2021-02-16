from seleniumwire import webdriver, request as selenium_request
import random
import time

CHECK_STRING = "check"


def new_browser(data, session_page=None,
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


def submit_form(inputs: list, curr_text_input: dict,
                text: str, data, browser) -> (str, float, list):
    """
    Function submits a specified form
    @param inputs: A list of inputs of action form
    @param curr_text_input: The current text input we are checking
    @param text: The we want to implicate into the current text input
    @param data: The data object of the program
    @param browser: The webdriver object
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
    # Sending the request
    start = time.time()  # Getting time of normal input
    data.submit_form(inputs, browser)
    run_time = time.time() - start
    content = browser.page_source
    return content, run_time, check_strings
