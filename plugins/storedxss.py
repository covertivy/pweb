import Data
from colors import COLOR_MANAGER
import bs4
from bs4 import BeautifulSoup

COLOR = COLOR_MANAGER.TURQUOISE
PAYLOADS_PATH = "./plugins/xsspayloads.txt" # Assuming the payloads are in the same directory as the StoredXSS script.


def check(data: Data.Data):
    stored_xss_results = Data.CheckResults("Stored XSS", COLOR)
    problem_str = ""
    result_str = ""
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()

    for page in pages:
        # Only check html pages.
        if 'html' not in page.type:
            continue

        csp_info: dict= csp_check(page)

        if csp_info is not None:
            allowed_script_sources: dict = {}
            for key, value in csp_info['allow_scripts']:
                if value:
                    allowed_script_sources[key] = value
            
            allowed_image_sources: dict = {}
            for key, value in csp_info['allow_images']:
                if value:
                    allowed_image_sources[key] = value
        
            if '*' not in allowed_script_sources.keys() and not '*' in allowed_image_sources.keys():
                problem_str += "Page is protected by 'Content-Security-Policy' Headers and therefor is protected from general xss vulnerabilities.\n" \
                                "\t\t\tYou should still check for 'Content-Security-Policy' bypass vulnerabilities.\n"
                if len(allowed_script_sources.keys()) > 0:
                    problem_str += "\t\t\tPlease also note that some interesting `script-src` CSP Headers were also found: {}\n".format(allowed_script_sources.keys())
                if len(allowed_image_sources.keys()) > 0:
                    problem_str += "\t\t\tPlease also note that some interesting `img-src` CSP Headers were also found: {}\n".format(allowed_image_sources.keys())
                res = Data.PageResult(page, problem_str, result_str)
                stored_xss_results.page_results.append(res)
                continue
        
        # Do not perform this aggressive method if the aggressive flag is not checked.
        if not data.aggressive:
            stored_xss_results.page_results = "The Stored XSS plugin has only checked the 'Content-Security-Policy' Headers.\n"
            str_to_add = str("\t\t\tThe response headers did not contain any Content-Security-Policy Headers and therefor all XSS payloads might be effective!\n" if csp_info is None else "\t\t\tThe 'Content-Security-Policy' Headers that were found were in `script-src` {} and in `img-src` {}\n".format(allowed_script_sources.keys(), allowed_image_sources.keys()))
            stored_xss_results.page_results += str_to_add + "\t\t\tUnfortunately this plugin can no longer perform any aggressive checks since the -A flag was not checked, please use -h to learn more about this flag.\n"
            # Leave because if we found one result and we did not select the aggressive option then all page results will be the same.
            # (The csp headers are defined in the apache settings and therefor they will be the same for all pages).
            break
        else:
            allowed_sources: tuple= (True, True)
            if csp_info is not None:
                allowed_sources = tuple('*' in allowed_script_sources.keys(),'*' in allowed_image_sources.keys())
                
            allowed_payloads = select_payloads(allowed_sources)
            # TODO: verify this check is working with new page manager.
            vulnerable_inputs: dict = brute_force_alert(data, page, allowed_payloads)
            # TODO: finish delivery of analysis.

    data.mutex.acquire()
    data.results.append(stored_xss_results)
    data.mutex.release()


def csp_check(page: Data.Page):
    res_dict = {'allow_scripts': {}, 'allow_images': {}}
    headers: dict = page.request.response.headers

    if headers.get('Content-Security-Policy', None) is not None:
        csp_param_str = headers.get('Content-Security-Policy').lstrip().rstrip()

        def analyzeScriptSrcParams(param_args: list):
            res_dict = {'*': False, 'unsafe_eval': False, 'unsafe_inline': False, 'unsafe_hashes': False}
            for arg in param_args[1:]:
                if arg == '*':
                    res_dict['*'] = True
                elif arg == 'unsafe_eval': 
                    res_dict['unsafe_eval'] = True
                elif arg == 'unsafe_inline':
                    res_dict['unsafe_inline'] = True
                elif arg == 'unsafe_hashes':
                    res_dict['unsafe_hashes'] = True
            return res_dict

        def analyzeImageSrcParams(param_args: list):
            res_dict = {'*': False}
            for arg in param_args[1:]:
                if arg == '*':
                    res_dict['*'] = True
            return res_dict
        
        for param in csp_param_str.split('; '):
            # A param string will be "<param_name> <list of args separated by spaces>"
            # A param list will be [param_name, args...]
            param_args = param.split(' ')
            if param_args[0] == 'script_src':
                res_dict['allow_scripts'] = analyzeScriptSrcParams(param_args)
            elif param_args[0] == 'img_src':
                res_dict['allow_images'] = analyzeImageSrcParams(param_args)
        return res_dict
    else: 
        return None


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


def select_payloads(allowed_sources: tuple):
    """
    This function receives a tuple that indicates which payloads are allowed by the CSP and returns a 
    filtered list of all possibly effective payloads.
    @param allowed_sources (tuple): This is a tuple that contains specifications if we can use the <img> payloads or the <script> payloads. the order is (script, img) so for example (True, False) would mean that only scripts are allowed via the csp.
    @returns (list): A list where each element is a payload that was selected from the payloads text file.
    """
    payloads = list()
    with open(PAYLOADS_PATH, 'r', encoding='utf-16') as file:
        file_read = file.read()
        payloads = file_read.split('\n')
    
    if not all(allowed_sources):
        for payload in payloads:
            if not allowed_sources[0]: # Disallow scripts.
                if 'script' in payload.lower():
                    payloads.remove(payload)
            if not allowed_sources[1]: # Disallow images.
                if 'img' in payload.lower():
                    payloads.remove(payload)
    
    return payloads


def brute_force_alert(data: Data.Data, page: Data.Page, payloads: list):
    """
    This is a function to check every form input for possible stored xss vulnerability.
    A web browser checks for an alert and if it finds one it is vulnerable!
    !This method is extremely aggressive and should be used with caution!
    @param data (Data.Data): The data object.
    @param page (Data.Page): The page object of the current page.
    @param payloads (list): A list where each element is a payload that was selected from the payloads text file.
    @returns (dict): A dictionary of all vulnerable inputs and their ids, id for key and `soup.element.Tag` as value.
    """
    # A dictionary containing all the results from our check.
    vulnerable_forms = {}
    index = 0

    for form_details in get_forms(page.content):
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
                        # There is no given value to the input tag
                        input_tag["value"] = payload
                elif input_tag.get('name', None):
                    continue
            
            # Create a chrome web browser for current page.
            browser = open_browser(data, page)
            # Submit the form that was injected with the payload.
            data.submit_form(inputs, browser)
            # Close the browser after injecting and sending the payload.
            browser.quit()
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
                browser.quit()

    return vulnerable_forms