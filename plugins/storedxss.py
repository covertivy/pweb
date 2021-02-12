import Data
from colors import COLOR_MANAGER
import bs4
from bs4 import BeautifulSoup
import plugins.analyzeReqHeaders as headerAnalyzer

COLOR = COLOR_MANAGER.TURQUOISE
PAYLOADS_PATH = "./plugins/xsspayloads.txt" # Assuming the payloads are in the same directory as the StoredXSS script.

def check(data: Data.Data):
    stored_xss_results = Data.CheckResults("Stored XSS", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()

    for page in pages:
        # Only check html pages.
        if 'html' not in page.type:
            continue
        csp_info: dict= headerAnalyzer.csp_check(page)
        if not csp_info['allow_scripts'] and not csp_info['allow_images']:
            # Page is protected by csp but should be checked for content security policy bypass vulnerability.
            pass
        elif not csp_info['allow_scripts'] and csp_info['allow_images']:
            # Cannot run disallowed scripts on this page.
            pass
        elif csp_info['allow_scripts'] and not csp_info['allow_images']:
            # Cannot add disallowed images on this page. 
            pass
        else:
            # Both unauthorized scripts and images are allowed.
            pass
        
        # TODO: verify this check is working with new page manager.
        vulnerable_inputs: dict = brute_force_alert(data, page.url, page.content)
        
        # TODO: finish delivery of analysis.

    data.mutex.acquire()
    data.results.append(stored_xss_results)
    data.mutex.release()


def open_browser(data: Data.Data, page: Data.Page):
    url = page.url
    if page.parent:
        # If the page is not first.
        url = page.parent.url
    browser = data.new_browser()  # Getting new browser.
    browser.set_page_load_timeout(60)  # Setting long timeout.
    
    if type(page) is Data.SessionPage:
        browser.get(url)  # Getting parent URL.
        for cookie in page.cookies:  # Adding cookies.
            browser.add_cookie(cookie)
    
    # Getting the page again, with the cookies
    browser.get(page.url)
    return browser

def get_forms(content: str):
    form_list = list()
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
            form_details['form'] = form
            form_details["action"] = action
            form_details["method"] = method
            form_details["inputs"] = inputs
            form_list.append(form_details)
        except:
            continue
    return form_list

def brute_force_alert(data: Data.Data, page: Data.Page, source_html: str):
    """
    This is a function to check every form input for possible stored xss vulnerability.
    A web browser checks for an alert and if it finds one it is vulnerable!
    !This method is extremely aggressive and should be used with caution!
    Args:
        @param page_url (str): The url of the page to be checked. format should be "http://pageto.check:<optional port>/<required dirctories>/"
        @param source_html (str): The source html of the page to be checked.

    Returns:
        dict: A dictionary of all vulnerable inputs and their ids, id for key and `soup.element.Tag` as value.
    """
    # Do not perform this aggressive method if the aggressive flag is not checked.
    if not data.aggressive:
        return

    # A dictionary containing all the results from our check.
    vulnerable_forms = {}
    index = 0

    payloads = list()
    with open(PAYLOADS_PATH, 'r') as file:
        file_read = file.read()
        payloads = file_read.split('\n')

    for form_details in get_forms(source_html):
        form_id = index
        index += 1

        # Check each known xss payload against input from $PAYLOADS_PATH text file. (more can be added if needed).
        for payload in payloads:
            if form_id in vulnerable_forms.keys():
                    break
            inputs = list(form_details["inputs"])
            for input_tag in inputs:
                # Using the specified value
                input_tag = dict(input_tag)
                if "name" in input_tag.keys():
                    # Only if the input has a name
                    if not input_tag["value"]:
                        # There is no value to the input tag
                        input_tag["value"] = payload
                elif (not input.has_attr('name')):
                    continue
            
            # Create a chrome web browser for current page.
            browser = open_browser(data, page)
            # Submit the form that was injected with the payload.
            data.submit_form(inputs, browser)
            # Close the browser after injecting and sending the payload.
            browser.close()
            # Get reloaded page.
            browser = open_browser(data, page) 
            
            try:
                # Check for alert on reloaded page.
                alert = browser.switch_to.alert
                alert.accept()
                # If did not catch an error then page has popped an alert.
                # Add to vulnerable forms dictionary.
                vulnerable_forms[form_id] = (form_details['form'], payload)
            except:
                pass  # No alert and therefor not vulnerable.
            finally:
                # Close opened browser to prepare for next iteration.
                browser.close()

    return vulnerable_forms

