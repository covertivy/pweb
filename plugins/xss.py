import bs4
import Classes
import Methods
from colors import COLOR_MANAGER
from bs4 import BeautifulSoup, element, Tag
import re as regex  #? Used `https://regex101.com/` a lot to verify regex string.
from seleniumwire import webdriver

COLOR = COLOR_MANAGER.TURQUOISE
PAYLOADS_PATH = "./plugins/xsspayloads.txt" # Assuming the payloads are in the same directory as this script file.
INJECTION_IDENTIFIER = "##~##" # Will be used to customize the payload in the `brute_force_alert` method.

#*-------------------------------------------------------------------
# >                XSS CONSTANT OUTPUT STRINGS                      |
#*-------------------------------------------------------------------
XSS_PROBLEM_STR = """GENERAL XSS:
This vulnerability occurs when untrusted data from the user is interpreted and executed as javascript code.
By running this untrusted code the attacker can manipulate the javascript functions and run whatever code he wishes to.
This enables a plethora of attacks, one of them being reflected xss.
"""

XSS_SOLUTION_STR = """Preventing cross-site scripting is trivial in some cases but can be much harder depending on the complexity of the application and the ways it handles user-controllable data.
In general, effectively preventing XSS vulnerabilities is likely to involve a combination of the following measures:
    - Filter input on arrival. At the point where user input is received, filter as strictly as possible based on what is expected or valid input.
    - Encode data on output. At the point where user-controllable data is output in HTTP responses, encode the output to prevent it from being interpreted as active content. Depending on the output context, this might require applying combinations of HTML, URL, JavaScript, and CSS encoding.
    - Use appropriate response headers. To prevent XSS in HTTP responses that aren't intended to contain any HTML or JavaScript, you can use the Content-Type and X-Content-Type-Options headers to ensure that browsers interpret the responses in the way you intend.
    - Content Security Policy. As a last line of defense, you can use Content Security Policy (CSP) to reduce the severity of any XSS vulnerabilities that still occur."""

XSS_EXPLANATION_STR = """The algorithm that was used to get a general idea of general XSS vulnerabilities was to simply inject payloads to each form on a given page until an alert pops.
If and alert has indeed popped, then we know the page is vulnerable to reflected xss."""

#*-------------------------------------------------------------------
# >                DOM XSS CONSTANT OUTPUT STRINGS                  |
#*-------------------------------------------------------------------
# The regex strings used to find all dom-xss sources.
SOURCES_RE = """(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)|\s*URLSearchParams[\(.]|\s*[.]*(getElementById|getElementByName|getElementByClassName)\("""
# The regex string used to find all dom-xss sinks.
SINKS_RE = """(document\.((write|writeln)\(|(domain\s*=))+)|.(innerHTML|outerHTML|insertAdjacentHTML|onevent)\s*=|((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getsource_htmlHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()"""

DOM_XSS_PROBLEM_STR = """DOM XSS:
This vulnerability occurs when untrusted data from the user is shown in the DOM (Document Model Object).
By inserting this untrusted data to the DOM the attacker can manipulate the html elements and make changes to the page (locally).
This enables a plethora of attacks, one of them being reflected xss."""

DOM_XSS_SOLUTION_STR = """The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts.
If you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.
Avoid dangerous methods and instead use safer functions.
Check if sources are directly related to sinks and if so prevent them from accessing each other.
For more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html"""

DOM_XSS_EXPLANATION_STR = """The algorithm that was used to get a general idea of DOM XSS vulnerabilities was to find potentially problematic
javascript functions within each script tag and see if any user input is used in the same script tag. If so, the chances of DOM XSS are potentially high.
To find each javascript source and sink we used regex patterns."""

#*-------------------------------------------------------------------
# >              STORED XSS CONSTANT OUTPUT STRINGS                 |
#*-------------------------------------------------------------------
STORED_XSS_PROBLEM_STR = """STORED XSS:
This vulnerability occurs when untrusted data from the user is interpreted and executed as javascript code but is also stored on the webserver's database.
This is a very dangerous attack since now not only the user sees the effects of it locally but also everyone that visits that page.
By running this untrusted code on all client's browsers the attacker can manipulate the javascript functions and run whatever code he wishes to.
"""

STORED_XSS_SOLUTION_STR = """Preventing cross-site scripting is trivial in some cases but can be much harder depending on the complexity of the application and the ways it handles user-controllable data.
In general, effectively preventing XSS vulnerabilities is likely to involve a combination of the following measures:
    - Filter input on arrival. At the point where user input is received, filter as strictly as possible based on what is expected or valid input.
    - Encode data on output. At the point where user-controllable data is output in HTTP responses, encode the output to prevent it from being interpreted as active content. Depending on the output context, this might require applying combinations of HTML, URL, JavaScript, and CSS encoding.
    - Use appropriate response headers. To prevent XSS in HTTP responses that aren't intended to contain any HTML or JavaScript, you can use the Content-Type and X-Content-Type-Options headers to ensure that browsers interpret the responses in the way you intend.
    - Content Security Policy. As a last line of defense, you can use Content Security Policy (CSP) to reduce the severity of any XSS vulnerabilities that still occur."""

STORED_XSS_EXPLANATION_STR = """The algorithm that was used to get a general idea of STORED XSS vulnerabilities was to re-visit each page we have found to be vulnerable to regular XSS vulnerabilities,
By re-visiting each vulnerable page we can check if our page will raise another alert.
If so then we can conclude that out previous payload had been stored on the server's database and will now be loaded each time we open the page.
"""

#*-------------------------------------------------------------------

def check(data: Classes.Data):
    domxss_result: Classes.CheckResult = check_dom(data)
    xss_result: Classes.CheckResult = Classes.CheckResult(XSS_PROBLEM_STR, XSS_SOLUTION_STR, XSS_EXPLANATION_STR)
    stored_xss_result: Classes.CheckResult = Classes.CheckResult(STORED_XSS_PROBLEM_STR, STORED_XSS_SOLUTION_STR, STORED_XSS_EXPLANATION_STR)
    all_xss_results: Classes.CheckResults = Classes.CheckResults("XSS", COLOR)

    data.mutex.acquire()
    aggressive = data.aggressive
    pages = data.pages
    data.mutex.release()

    if not aggressive:
        all_xss_results.warning = "Unfortunately this plugin cannot perform any aggressive checks since the -A flag was not checked, please use -h to learn more about this flag.\n"

    vulnerable_pages = []

    for page in pages:
        # Only check html pages.
        if 'html' not in page.type:
            continue
        
        # Get Content Security Policy Information.
        csp_info: dict= csp_check(page)

        if csp_info is not None:
            # Get information about the script CSP info.
            allowed_script_sources: dict = {}
            for key, value in csp_info['allow_scripts']:
                if value:
                    allowed_script_sources[key] = value

            # Get information about the img CSP info.
            allowed_image_sources: dict = {}
            for key, value in csp_info['allow_images']:
                if value:
                    allowed_image_sources[key] = value

            # Show conclusion of the Content Security Policy evaluation.
            if '*' not in allowed_script_sources.keys() and not '*' in allowed_image_sources.keys():
                problem_str = "Page is protected by 'Content-Security-Policy' Headers and therefor is protected from general xss vulnerabilities.\nYou should still check for 'Content-Security-Policy' bypass vulnerabilities.\n"
                if len(allowed_script_sources.keys()) > 0:
                    problem_str += f"Please also note that some interesting `script-src` CSP Headers were also found: {allowed_script_sources.keys()}\n"
                if len(allowed_image_sources.keys()) > 0:
                    problem_str += f"Please also note that some interesting `img-src` CSP Headers were also found: {allowed_image_sources.keys()}\n"
                
                xss_result.add_page_result(Classes.PageResult(page, problem_str))
                continue
        
        csp_conclusion = "The XSS plugin has checked the 'Content-Security-Policy' Headers.\n"
        str_to_add = str("The response headers did not contain any Content-Security-Policy Headers and therefor all XSS payloads might be effective!\n" if csp_info is None else f"The 'Content-Security-Policy' Headers that were found were in `script-src` {allowed_script_sources.keys()} and in `img-src` {allowed_image_sources.keys()}\n")
        csp_conclusion += str_to_add
        xss_result.add_page_result(Classes.PageResult(page, csp_conclusion))

        # Do not perform this aggressive method if the aggressive flag is not checked.
        if not aggressive:
            # Skip this page.
            continue
        else:
            # Perform payload injection and check for stored xss.
            # Use the Content Security Policy information to select the appropriate payloads.
            allowed_sources: tuple = (True, True)
            if csp_info is not None:
                allowed_sources = ('*' in allowed_script_sources.keys(), '*' in allowed_image_sources.keys())
            
            # Select appropriate payloads according to the CSP information.
            allowed_payloads = select_payloads(allowed_sources)
            # Try to trigger an alert with all the selected available payloads.
            vulnerable_forms: dict = brute_force_alert(data, page, allowed_payloads)

            if vulnerable_forms is None:
                continue # Page has no forms and therefor we do not check it.
            
            for vulnerable_form_id in vulnerable_forms.keys():
                # Get information about successful attack.
                vulnerable_form = vulnerable_forms[vulnerable_form_id][0]
                vulnerable_input = vulnerable_forms[vulnerable_form_id][1]
                successful_payload = vulnerable_forms[vulnerable_form_id][2]
                special_string = vulnerable_forms[vulnerable_form_id][3]

                xss_result.add_page_result(Classes.PageResult(page, f"Found a form that had caused an alert to pop from the following payload: '{successful_payload}'.\nThe Vulnerable Form is (Form Index [{vulnerable_form_id}]):\n{vulnerable_form}\nThe Vulnerable Input is:\n{vulnerable_input}\n"))
                vulnerable_pages.append((page, special_string)) # Will be used by the stored xss checks later.
    
    # Check each of the already vulnerable pages for stored xss.
    vulnerable_stored: list = check_for_stored(data, vulnerable_pages)
    if vulnerable_stored is not None and len(vulnerable_stored) != 0:
        for page_with_stored in vulnerable_stored:
            stored_xss_result.add_page_result(Classes.PageResult(page_with_stored, f"This page had shown an alert after refreshing it which strongly indicates it may vulnerable to stored xss.\n"))

    # Deliver Analysis.
    all_xss_results.results.append(xss_result)
    all_xss_results.results.append(domxss_result)
    all_xss_results.results.append(stored_xss_result)
    data.mutex.acquire()
    data.results_queue.put(all_xss_results)
    data.mutex.release()

##########################################################################! General XSS Recognition Logic !##########################################################################
def csp_check(page: Classes.Page):
    """
    This function receives a page and checks the response headers in order to find Content Security Policy parameters
    in which case it evaluates the policy and determines which payloads can be run on this specific page.

    @param page: The page who's headers we check for content security policy headers.
    @type page: Classes.Page
    @return: The results dictionary {'allow_scripts': {'*': False, 'unsafe_eval': False, 'unsafe_inline': False, 'unsafe_hashes': False}, 'allow_images': {'*': False}}
    @rtype: dict
    """
    res_dict = {'allow_scripts': {}, 'allow_images': {}}
    headers: dict = page.request.response.headers

    if headers.get('Content-Security-Policy', None) is not None:
        csp_param_str = headers.get('Content-Security-Policy').lstrip().rstrip()

        def analyzeScriptSrcParams(param_args: list):
            res_dict = {'*': False, 'unsafe_eval': False, 'unsafe_inline': False, 'unsafe_hashes': False}
            for arg in param_args[1:]:
                if arg == '*':
                    # Are all scripts allowed.
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
                    # Are all images allowed.
                    res_dict['*'] = True
            return res_dict
        
        for param in csp_param_str.split('; '):
            # A param string will be "<param_name> <list of args separated by spaces>".
            # A param list will be [param_name, args...].
            param_args = param.split(' ')
            if param_args[0] == 'script_src':
                res_dict['allow_scripts'] = analyzeScriptSrcParams(param_args)
            elif param_args[0] == 'img_src':
                res_dict['allow_images'] = analyzeImageSrcParams(param_args)
        return res_dict
    else: 
        # No Content Security Policy was present.
        return None


def select_payloads(allowed_sources: tuple):
    """
    This function receives a tuple that indicates which payloads are allowed by the CSP and returns a 
    filtered list of all possibly effective payloads.

    @param allowed_sources: This is a tuple that contains specifications if we can use the <img> payloads or the <script> payloads. the order is (script, img) so for example (True, False) would mean that only scripts are allowed via the csp.
    @type allowed_sources: tuple
    @return: A list where each element is a payload that was selected from the payloads text file.
    @rtype: list
    """
    payloads = list()
    with open(PAYLOADS_PATH, 'r') as payloads_file:
        # Read payloads from file.
        file_read = payloads_file.read()
        # Separate each payload by newline.
        payloads = file_read.split("\n") 
    
    # Strip redundant spaces.
    for i in range(len(payloads)):
        # Remove non important spaces.
        payloads[i] = payloads[i].lstrip().rstrip()
        if payloads[i] == "":
            # Remove empty payloads.
            payloads.remove(payloads[i])
        elif INJECTION_IDENTIFIER not in payloads[i]:
            # Must contain the special injection identifier to inject custom strings into the alert.
            payloads.remove(payloads[i])

    # Remove all the payloads that are blocked by the CSP.
    if not all(allowed_sources):
        for payload in payloads:
            if not allowed_sources[0]: # Disallow scripts.
                if 'script' in payload.lower():
                    payloads.remove(payload)
            if not allowed_sources[1]: # Disallow images.
                if 'img' in payload.lower():
                    payloads.remove(payload)
    
    return payloads


def brute_force_alert(data: Classes.Data, page: Classes.Page, payloads: list):
    """
    This is a function to check every form input for possible stored xss vulnerability.
    A web browser checks for an alert and if it finds one it is vulnerable!
    !This method is extremely aggressive and should be used with caution!

    @param data: The data object.
    @type data: Classes.Data
    @param page: The page object of the current page.
    @type page : Classes.Page
    @param payloads: A list where each element is a payload that was selected from the payloads text file.
    @type payloads: list
    @return: A dictionary of all vulnerable inputs and their ids, id for key and tuple (form tag: `element.Tag`, payload) as value.
    @rtype: dict
    """
    # A dictionary containing all the results from our check.
    vulnerable_forms = {}
    index = 0
    # Create a chrome web browser for current page.
    browser: Classes.Browser = Methods.new_browser(data, page, remove_alerts=False)
    page_forms: list = Methods.get_forms(page.content)
    if len(page_forms) == 0:
        return None
    
    # The page content, will be used to ensure each payload is different.
    content: str = page.content
    for form_details in page_forms:
        is_vulnerable = False # A boolean indicating whether the current form was vulnerable or not.
        form_id = index # Give an index to each form.
        # Check each known xss payload against input from $PAYLOADS_PATH text file. (more can be added if needed).
        for payload in payloads:
            # Dump alerts to allow form submission without problem.
            browser.dump_alerts()
            # A dictionary to which we will save each input tag and it's corresponding random string as a key.
            input_ids = {}
            # Get all text inputs from the form.
            inputs = Methods.get_text_inputs(form_details["inputs"])
            for input_tag in inputs:
                # Generate a random string which will serve as the payload string as well as the input key.
                special_str = Methods.get_random_str(content)
                content += f"\n{special_str}" # To avoid repetitive payloads (`get_random_str` will take this into consideration).
                # Modify payload to hold the special string.
                curr_payload = payload.replace(INJECTION_IDENTIFIER, f"\"{special_str}\"")
                # Add the input into the inputs dictionary.
                input_ids[special_str] = input_tag
                # Fill input with our desired payload.
                form_details = Methods.fill_input(form_details, input_tag, curr_payload)

            try:
                # Submit the form that was injected with the payload (in `try` because could raise an error).
                Methods.submit_form(data, browser, form_details["inputs"])      
            except:
                pass
            
            try:
                while not is_vulnerable:
                    # Check for alert on page.
                    alert = browser.switch_to.alert
                    # If did not catch an error then page has popped an alert.
                    # Add to vulnerable forms dictionary.
                    if alert.text in input_ids.keys():
                        vulnerable_form: Tag = form_details['form']
                        vulnerable_input = vulnerable_form.findChild("input", {"name": input_ids[alert.text]["name"]})
                        vulnerable_forms[form_id] = (str(vulnerable_form), str(vulnerable_input), payload, alert.text)
                        is_vulnerable = True
                    
                    # Accept the alert to continue to the next alert (if it exists).
                    alert.accept()
            except:
                pass # No alert and therefor no problem.
            finally:
                # Advance the form index.
                index += 1
                if is_vulnerable:
                    # Page was found to be vulnerable and therefor no need to check.
                    break
                # Refresh current page to prepare for next iteration.
                browser.refresh()
    # Close the webdriver and return results.
    browser.quit()
    return vulnerable_forms


##########################################################################! STORED XSS Recognition Logic !###########################################################################
def check_for_stored(data: Classes.Data, vulnerable_pages: list):
    """
    This function receives a list of already known vulnerable pages to XSS and checks if an alert containing the special 
    string as it's text exists, if so then we know this alert had stayed from our previous injection and therefor this page is vulnerable to Stored XSS.

    @param data: The data object of the program.
    @type data: Classes.Data
    @param vulnerable_pages: A list containing each vulnerable page and the special string in the alert which was caused by our xss as a tupple [tuple(Classes.Page, str)].
    @type vulnerable_pages: list
    @return: A list of all the pages that were found to be vulnerable to Stored XSS.
    @rtype: list
    """
    if len(vulnerable_pages) == 0:
        return
    
    stored_xss_pages = list()
    for page, special_string in vulnerable_pages:
        # Create new browser.
        browser: Classes.Browser = Methods.new_browser(data, page, remove_alerts=False)
        found = False
        try:
            while not found:
                # Check for alert on page.
                alert = browser.switch_to.alert
                # If did not catch an error then page has popped an alert.
                # Add to vulnerable forms dictionary.
                if alert.text == special_string:
                    stored_xss_pages.append(page)
                    found = True
                alert.accept()
        except:
            pass # No alert and therefor not vulnerable.
        finally:
            # Close opened browser to prepare for next iteration.
            browser.quit()

    return stored_xss_pages


############################################################################! DOM XSS Recognition Logic !############################################################################
def check_dom(data: Classes.Data):
    """
    This function is in charge of running all the DOM XSS checks and scans and to deliver a CheckResult object back to the main `check` method.

    @param data: The data object of the program.
    @type data: Classes.Data
    @return: The CheckResult with the DOM XSS analysis.
    @rtype: Classes.CheckResult
    """
    dom_xss_result = Classes.CheckResult(DOM_XSS_PROBLEM_STR, DOM_XSS_SOLUTION_STR, DOM_XSS_EXPLANATION_STR)

    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()

    for page in pages:
        if "html" not in page.type:
            if "javascript" in page.type:
                # Look for sources and sinks in javascript source code.
                if analyse_javascript(page.content):
                    javascript_page_result_str = f"Found javascript code that is quite possibly vulnerable to DOM based XSS:\n" \
                                  f"The Line is: {find_script_by_src(page.parent.content, page.url)}\n" \
                                  f"From page {page.parent.url}\n"
                    dom_xss_result.add_page_result(Classes.PageResult(page.parent, javascript_page_result_str), '\n')
            else:
                 continue  # Ignore non javascript pages.       

        possible_vulns = {}
        vulnerable_dom_scripts = {}
        vulnerable_input_scripts = {}
        try:
            possible_vulns = determine_possible_vulns(page.content)
            vulnerable_dom_scripts, vulnerable_input_scripts = further_analyse(
                possible_vulns, find_input_fields(page.content)
            )
        except Exception as e:
            continue # No vulnerability was found.
        
        # Deliver analysis results.
        if len(vulnerable_dom_scripts.keys()) > 0:
            for script_index in vulnerable_dom_scripts.keys():
                script_tuple = vulnerable_dom_scripts.get(script_index, None)
                if script_tuple is None:
                    continue
                script_result_str = f"Found a quite possibly vulnerable script to DOM based XSS (Script Index [{script_index}]).\nThe script is: {str(script_tuple[0])}\nThe sink patterns are: {str(script_tuple[1])}\nThe source patterns are: {str(script_tuple[2])}\nDanger level is {str(script_tuple[3])}\n"
                dom_xss_result.add_page_result(Classes.PageResult(page, script_result_str), '\n')

        if len(vulnerable_input_scripts.keys()) > 0:
            for script_index in vulnerable_input_scripts.keys():
                script_tuple = vulnerable_input_scripts.get(script_index, None)
                if script_tuple is None:
                    continue
                input_result_str = f"Found a quite possibly vulnerable script to DOM based XSS (Script Index [{script_index}]).\nThe script is: {str(script_tuple[0])}\nThe sink patterns are: {str(script_tuple[1])}\nThe input sources are: {str(script_tuple[2])}\nDanger level is {str(script_tuple[3])}\n"
                dom_xss_result.add_page_result(Classes.PageResult(page, input_result_str), '\n')
    
    return dom_xss_result


def analyse_javascript(javascript_code: str):
    """
    This function looks for sinks and sources within the javascript included code.
    If it finds both at least one source and at least one sink it will return true.

    @param javascript_code: The source javascript page code.
    @type javascript_code: str
    @return: A boolean indicating whether the javascript source code is possibly vulnerable (yes/no).
    @rtype: bool
    """
    match_sources_in_code = regex.finditer(SOURCES_RE, javascript_code, regex.IGNORECASE)
    match_sinks_in_code = regex.finditer(SINKS_RE, javascript_code, regex.IGNORECASE)

    sources = []
    # Look for sources in code.
    for match in match_sources_in_code:
        match_groups = tuple(group for group in match.groups() if group is not None)
        sources.append(match_groups)
    # Look for sinks in code.
    sinks = []
    for match in match_sinks_in_code:
        match_groups = tuple(group for group in match.groups() if group is not None)
        sinks.append(match_groups)
    
    sources = list(set(sources))
    sinks = list(set(sinks))

    if len(sinks) > 0 and len(sources) > 0:
        return True
    return False


def get_scripts(html: str, src: bool = False):
    """
    This function searches for all the script tags within the page html and
    returns a list of of enumerated script tags.

    @param html: The source html of the page.
    @type html: str
    @param src: Should we search for script tags with src attribute. Defaults to False (optional).
    @type src: bool
    @return: The enumerated list of script tags.
    @rtype: list
    """
    html = BeautifulSoup(html, "html.parser")
    source_scripts = html.find_all("script", src=src)
    return list(enumerate(source_scripts))


def find_script_by_src(html: str, page_url:str):
    """
    This function finds a single script that has a src attribute and the source 
    is the specified page url.

    @param html: The source html of the page in which we want to find the script tag.
    @type html: str
    @param page_url: The url of the source javascript page that will be searched for in the element.
    @type page_url: str
    @return: The script tag that contained the page_url as a src attribute.
    @rtype: Tag
    """
    soup = BeautifulSoup(html, "html.parser")
    def script_filter(tag: element.Tag):
        return tag.name == "script" and tag.has_attr("src") and page_url.endswith(tag["src"])
    scripts = soup.find_all(script_filter, limit=1)
    if len(scripts) == 0:
        return None
    return scripts[0]


def get_script_by_id(source_html:str, script_id:int):
    """
    This function finds a script in a specific index in the page source html.

    @param source_html: The source html of the page in which we want to find the script tag.
    @type source_html: str
    @param script_id: The id of the script tag (it's index from the top).
    @type script_id: int
    @return: The script tag of the correct index or None if script was not found.
    @rtype: Tag
    """
    soup = BeautifulSoup(source_html, "html.parser")
    all_scripts = soup.find_all("script")
    if script_id > -1 and script_id < len(all_scripts):
        return all_scripts[script_id]
    else:
        return None


def determine_possible_vulns(source_html: str):
    """
    A vulnerable script is a script which contains a sink which can be used to execute xss via a source.
    A script cannot be vulnerable without a sink so first we validate the existance of a sink with a regex containing all sinks.

    @param source_html: The source html of the web page to analyze.
    @type source_html: str
    @return: A dictionary containing the scripts that has a tuple of sink patterns and their amount as values and the script indexes as keys.
    @rtype: dict
    """
    # Fetch all source script tags from page html.
    all_scripts = get_scripts(source_html)
    sinks = {}  # Initialize empty dictionary for sinks.

    for script_index, script in all_scripts:
        sink_patterns = []

        regex_sink_matches = regex.finditer(SINKS_RE, str(script), regex.IGNORECASE)

        # Look for sinks in script.
        for match in regex_sink_matches:
            match_groups = tuple(group for group in match.groups() if group is not None)
            sink_patterns.append(match_groups)

        # Get rid of duplicate regex matches.
        sink_patterns = list(set(sink_patterns))

        if len(sink_patterns) > 0:
            sinks[script_index] = (script, sink_patterns)

    return sinks


def find_input_fields(html: str):
    """
    Get all input fields and filter them to only useful input fields that can house text (can contain script tags).

    @param html: The source html of the page to check.
    @type html: str
    @return: The tuple containing the results, explanation at the return line.
    @rtype: tuple
    """

    def input_filter_function(tag: element.Tag):
        """
        A filtering function for beautiful soup's `find_all` function to get all input tags that are of the types: `text`, `url` and `search`.

        @param tag: The current tag to filter.
        @type tag: Tag
        @return: Is the tag appropriate according to our terms.
        @rtype: bool
        """
        # If tag is of `input` type and has a `type` attribute.
        if tag.name != "input" or not tag.has_attr("type"):
            return False
        type_str = tag["type"].lower()
        # If input type is the type we want.
        if any(
            [
                type_str == "text",
                type_str == "url",
                type_str == "search",
                type_str == "select",
            ]
        ):
            return True

    soup = BeautifulSoup(html, "html.parser")
    # Find all input tags with our filter function.
    all_inputs = soup.find_all(input_filter_function)
    form_inputs = []  # Empty list of inputs that are children of a form.

    # Separate form inputs.
    for inp in all_inputs:
        # Check if input parent is form.
        if inp.parent.name == "form":
            form_inputs.append(inp)

    #? (RETURN) a tuple which contains the following results:
    #? [0]: a boolean expression which states if there are any inputs to check.
    #? [1]: a list of inputs that belong to a form.
    #? [2]: a list all inputs in the web page.
    return (
        len(all_inputs) > 0,
        all_inputs,
        form_inputs
    )


def check_form_inputs(form_inputs: list, suspicious_scripts: dict):
    """
    Go over each script and check if form input is used within it, if so it is possibly vulnerable!
    Different function from `check_all_inputs` since form inputs can be accessed differently.
    Reference: `https://stackoverflow.com/questions/18606305/accessing-formdata-values`

    @param form_inputs: All form inputs.
    @type form_inputs: list
    @param suspicious_scripts: A dictionary containing all scripts that contain sources and/or sinks.
    @type suspicious_scripts: dict
    @return: The dictionary of possibly very vulnerable scripts and their danger rating.
    @rtype: dict
    """
    very_vulnerable = {}
    for script_index in suspicious_scripts.keys():
        script_str = suspicious_scripts[script_index][0]
        vuln_raises = 0
        vulnerable_inputs = []

        if "FormData" in script_str:
            vuln_raises += script_str.count("FormData")

        for form_input in form_inputs:
            form_object = Tag(form_input.parent)

            if (
                form_object.get("id") is not None
                and form_object.get("id") in script_str
            ):
                if (
                    f'getElementById("{form_object["id"]}").value' in script_str
                    or f"getElementById('{form_object['id']}').value" in script_str
                ):
                    vuln_raises += 1
                    vulnerable_inputs.append(form_input)
            if (
                form_object.get("name") is not None
                and form_object.get("name") in script_str
            ):
                if (
                    f'getElementsByName("{form_object["name"]}")' in script_str
                    or f"getElementsByName('{form_object['name']}')" in script_str
                ):
                    vuln_raises += 1
                    vulnerable_inputs.append(form_input)
            if (
                form_object.get("class") is not None
                and form_object.get("class") in script_str
            ):
                if (
                    f'getElementsByClassName("{form_object["class"]}")' in script_str
                    or f"getElementsByClassName('{form_object['class']}')" in script_str
                ):
                    vuln_raises += 1
                    vulnerable_inputs.append(form_input)

        if vuln_raises > 0:
            very_vulnerable[script_index] = (
                suspicious_scripts[script_index][0], # Script string.
                suspicious_scripts[script_index][1], # Script sinks.
                vulnerable_inputs, # Script form input sources.
                vuln_raises + len(suspicious_scripts[script_index][1]) # Script "danger" level.
            )

    return very_vulnerable


def check_all_inputs(all_inputs: list, suspicious_scripts: dict):
    """
    Go over each script and check if non form input is used within it, if so it is possibly vulnerable!
    Different function from `check_form_inputs` since form inputs can be accessed differently.
    Reference: `https://stackoverflow.com/questions/11563638/how-do-i-get-the-value-of-text-input-field-using-javascript`

    @param all_inputs: All input tags.
    @type all_inputs: list
    @param suspicious_scripts: A dictionary containing all scripts that contain sources and/or sinks.
    @type suspicious_scripts: dict
    @return: The dictionary of possibly very vulnerable scripts and their danger rating.
    @rtype: dict
    """
    very_vulnerable = {}
    for script_index in suspicious_scripts.keys():
        vuln_raises = 0
        vulnerable_inputs = []
        for input_tag in all_inputs:
            script_str = str(suspicious_scripts[script_index][0])

            if input_tag.get("id") is not None and input_tag.get("id") in script_str:
                if (
                    f'getElementById("{input_tag["id"]}").value' in script_str
                    or f"getElementById('{input_tag['id']}').value" in script_str
                ):
                    vuln_raises += 1
                    vulnerable_inputs.append(input_tag)
            if (
                input_tag.get("name") is not None
                and input_tag.get("name") in script_str
            ):
                if (
                    f'getElementsByName("{input_tag["name"]}")' in script_str
                    or f"getElementsByName('{input_tag['name']}')" in script_str
                ):
                    vuln_raises += 1
                    vulnerable_inputs.append(input_tag)
            if (
                input_tag.get("class") is not None
                and input_tag.get("class") in script_str
            ):
                if (
                    f'getElementsByClassName("{input_tag["class"]}")' in script_str
                    or f"getElementsByClassName('{input_tag['class']}')" in script_str
                ):
                    vuln_raises += 1
                    vulnerable_inputs.append(input_tag)

        if vuln_raises > 0:
            very_vulnerable[script_index] = (
                suspicious_scripts[script_index][0], # Script string.
                suspicious_scripts[script_index][1], # Script sinks.
                vulnerable_inputs, # Script input sources.
                vuln_raises + len(suspicious_scripts[script_index][1]) # Script "danger" level.
            )

    return very_vulnerable


def further_analyse(suspicious_scripts: dict, input_sources: tuple):
    """
    Further analyse each script that contained sinks,
    Check if any type of user input or a known source is used in any of the suspicious scripts,
    If so, they are way more likely to be vulnerable!

    !Raises:
    !    ValueError: `suspicious_scripts` parameter is empty list.
    !    ValueError: `input_sources` parameter is not in valid format, size should be 3.
    !    ValueError: The first value in `input_sources` parameter is false,
    !        meaning there are no input sources in given page and therefor no possible vulnerabilities.

    @param suspicious_scripts: A dictionary containing all scripts that contain sinks.
        ? { script_index :  (script_string, regex_sink_patterns), ... }
    @type suspicious_scripts: dict
    @param input_sources: The returned tuple from `find_input_fields` function, containing various input fields to check individually.
    @type input_sources: tuple
    @return: A dictionary containing the more vulnerable script indexes as keys and the scripts themselves and their final danger levels as values.
    @rtype: dict
    """

    if len(suspicious_scripts) == 0:
        raise ValueError("No suspicious scripts were given to further analyse!")
    elif len(input_sources) != 3:
        raise ValueError("Input sources were given in wrong format!")

    # Find all vulnerable scripts to dom xss sources and sinks.
    vulnerable_scripts = {}
    for script_index in suspicious_scripts.keys():
        regex_source_matches = regex.finditer(
            SOURCES_RE, str(suspicious_scripts[script_index][0]), regex.IGNORECASE
        )
        # Look for dom_sources in script.
        source_patterns = []
        for match in regex_source_matches:
            match_groups = tuple(group for group in match.groups() if group is not None)
            source_patterns.append(match_groups)

        # Get rid of duplicate regex matches.
        source_patterns = list(set(source_patterns))

        if len(source_patterns) > 0:
            vulnerable_scripts[script_index] = (suspicious_scripts[script_index][0],suspicious_scripts[script_index][1] , source_patterns)


    # Check if there are input fields that might be sources.
    are_there_inputs, form_inputs, all_inputs = input_sources
    
    form_scripts = None
    final_input_scripts = {}
    final_source_sink_scripts = {}
    if are_there_inputs:
        if len(form_inputs) > 0:
            form_scripts = check_form_inputs(form_inputs, suspicious_scripts) # Scripts that access form data.
        input_scripts = check_all_inputs(all_inputs, suspicious_scripts) # Scripts that access input field data.

        for script_index in input_scripts.keys():
            if script_index not in final_input_scripts.keys():
                final_input_scripts[script_index] = (
                    input_scripts[script_index][0], # Script string.
                    input_scripts[script_index][1], # Script sink patterns.
                    input_scripts[script_index][2], # Script vulnerable input fields.
                    input_scripts[script_index][3]  # Total "danger" value.
                )

        if form_scripts is not None:
            for script_index in form_scripts.keys():
                if script_index not in final_input_scripts.keys():
                    final_input_scripts[script_index] = {
                        form_scripts[script_index][0], # Script string.
                        form_scripts[script_index][1], # Script sink patterns.
                        form_scripts[script_index][2], # Script vulnerable input fields.
                        form_scripts[script_index][3]  # Total "danger" value.
                    }
                else:
                    final_input_scripts[script_index] = (
                        final_input_scripts[script_index][0], # Script string.
                        final_input_scripts[script_index][1], # Script sink patterns.
                        final_input_scripts[script_index][2] + form_scripts[script_index][2], # Script vulnerable input fields.
                        final_input_scripts[script_index][3] + form_scripts[script_index][3] - len(final_input_scripts[script_index][1])  # Total "danger" value.
                    )

    for script_index in vulnerable_scripts.keys():
        if script_index not in final_source_sink_scripts.keys():
            final_source_sink_scripts[script_index] = (
                vulnerable_scripts[script_index][0], # Script string.
                vulnerable_scripts[script_index][1], # Script sink patterns.
                vulnerable_scripts[script_index][2], # Script source patterns.
                len(vulnerable_scripts[script_index][1]) + len(vulnerable_scripts[script_index][2]) # Total "danger" value.
            )

    return final_source_sink_scripts, final_input_scripts
