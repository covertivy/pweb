#!/usr/bin/python3
from colors import COLOR_MANAGER
import Classes
import Methods

# Consts:
COLOR = COLOR_MANAGER.rgb(0, 255, 200)
OUTSIDE_URL = "https://google.com"

# Global variables:
current_referer = None


def check(data: Classes.Data):
    """
    Function checks the website for CSRF
    @param data: The data object of the program
    @return: None
    """
    csrf_results = Classes.CheckResults("CSRF", COLOR)
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
                csrf_results.page_results = "The plugin check routine requires injecting text boxes," \
                                            " read about (-A) in our manual and try again."
                break
            for form in forms:
                try:
                    browser = set_browser(data, page)
                    result = csrf(page, form, data, browser)
                    if result.problem:
                        # If there is a problem with the page
                        csrf_results.page_results.append(result)
                except Exception:
                    continue
    except Exception as e:
        csrf_results.page_results = "Something went wrong..."

    data.mutex.acquire()
    data.results.append(csrf_results)  # Adding the results to the data object
    data.mutex.release()


def filter_forms(page: Classes.Page) -> list:
    """
    Function filters the pages that has an action form
    @param page: The current page
    @return: List of forms
    """
    filtered_forms = list()
    if "html" in page.type.lower() and type(page) is Classes.SessionPage:
        # The only thing we need is a HTML session page with a form
        for form in Methods.get_forms(page.content):
            # Adding the page and it's form to the list
            filtered_forms.append(form)
    return filtered_forms


def csrf(page: Classes.SessionPage, form: dict, data: Classes.Data, browser) -> Classes.PageResult:
    """
    Function checks the page for csrf
    @param page: The current page
    @param form: The page's action form
    @param data: The data object of the program
    @param browser: The Chrome browser object
    @return: Page result object
    """
    page_result = Classes.PageResult(page, "", "")
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
        for new_form in Methods.get_forms(browser.page_source):
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
    normal_content = get_response(form["inputs"], page.url, data, browser, page)
    # Getting redirected content
    browser.get(page.url)
    referer_content = get_response(form["inputs"], OUTSIDE_URL, data, browser, page)
    if normal_content == referer_content:
        # Does not filter referer header
        vulnerability[1] = True
    else:
        # Getting local redirected content
        browser.get(page.url)
        referer_content = get_response(form["inputs"], page.parent, data, browser, page)
        if normal_content == referer_content:
            # Does not filter referer header
            vulnerability[2] = True
    if sum(vulnerability):
        # If there is a vulnerability
        write_vulnerability(vulnerability, page_result)
    return page_result


def get_response(inputs: list, referer: str, data: Classes.Data, browser, page) -> str:
    """
    Function submits a specified form and gets the result content
    @param inputs: A list of inputs of action form
    @param referer: A specified referer address
    @param data: The data object of the program
    @param browser: The browser object
    @param page: The current page
    @return: The content of the resulted page
    """
    content = ""
    try:
        # Sending the request
        global current_referer
        current_referer = referer
        content, run_time, strings = Methods.submit_form(inputs, dict(), "", browser, data)
        current_referer = None
        content = browser.page_source
        for string in strings:
            # In case that the random string is in the content
            content = content.replace(string, "")
        # In case of referrers in content
        content = content.replace(page.url, "").replace(OUTSIDE_URL, "").replace(page.parent, "")
    except Exception as e:
        pass
    finally:
        return content


def set_browser(data: Classes.Data, page: Classes.SessionPage):
    """
    Function Sets up a new browser, sets its cookies and checks if the cookies are valid
    @param data: The data object of the program
    @param page: The current page
    @return: The browser object
    """
    return Methods.new_browser(data, interceptor=interceptor, session_page=page)


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


def write_vulnerability(results: list, page_result: Classes.PageResult):
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
