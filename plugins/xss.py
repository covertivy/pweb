#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
import bs4 as soup
import re as regex  # Used `https://regex101.com/` a lot to verify regex string.
from selenium import webdriver


COLOR = COLOR_MANAGER.rgb(255, 0, 100)
# The regex strings used to find all dom-xss sources.
SOURCES_RE = """(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)|(\s*URLSearchParams\()"""
# The regex string used to find all dom-xss sinks.
SINKS_RE = """((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getsource_htmlHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()"""

XSS_STRINGS = [
    "<script>alert(1);</script>",
    "><script>alert(1);</script>",
    "'<script>alert(1);</script>",
    "<img src=x onerror=alert(1)>",
    '<img src="javascript:alert(1);">',
    "<img src=javascript:alert(1)>",
    "<img src=javascript:alert(&quot;XSS&quot;)>",
    "<<SCRIPT>alert(1);//\<</SCRIPT>",
]


def check(data: Data.Data):
    dom_xss_results = Data.CheckResults("DOMXSS", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()

    for page in pages:
        possible_vulns = {}
        very_vulnerable = {}
        try:
            possible_vulns = determine_possible_vulns(page.content)
            very_vulnerable = further_analyse(
                possible_vulns, find_input_fields(page.content)
            )
        except:
            pass
        if len(very_vulnerable.keys()) > 0:

            for script_index in possible_vulns.keys():
                problem_str = f"Found a quite possibly vulnerable script to DOM based XSS (Script [{script_index}]).\nThe script is: {str(very_vulnerable[script_index])}"
                result_str = "The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts. If you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.\nAvoid dangerous methods and instead use safer functions.\nCheck if sources are directly related to sinks and if so prevent them from accessing each other.\nFor more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html"
                res = Data.PageResult(page, problem_str, result_str)
                dom_xss_results.page_results.append(res)

        vulnerable_inputs = check_forms(page.url, page.content)
        if len(vulnerable_inputs.keys()) > 0:
            for vulnerable_input_id in vulnerable_inputs.keys():
                problem_str = f"Found xss vulnerability in input [{vulnerable_input_id}].\nThe input is: {str(vulnerable_inputs[vulnerable_input_id])}"
                result_str = "The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts. If you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.\nAvoid dangerous methods and instead use safer functions.\nCheck if sources are directly related to sinks and if so prevent them from accessing each other.\nFor more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html"
                res = Data.PageResult(page, problem_str, result_str)
                dom_xss_results.page_results.append(res)

    data.mutex.acquire()
    data.results.append(dom_xss_results)
    data.mutex.release()


def get_scripts(html: str, src: bool = False) -> list:
    soup_obj = soup.BeautifulSoup(html, "html.parser")
    source_scripts = soup_obj.find_all("script", src=src)
    return list(enumerate(source_scripts))


def determine_possible_vulns(source_html: str) -> dict:
    """
    A vulnerable script is a script which contains a sink which can be used to execute xss via a source.
    A script cannot be vulnerable without a sink so first we validate the existance of a sink with a regex containing all sinks.
    Args:
        source_html (str): The source html of the web page to analyze.

    Returns:
        dict: a dictionary containing the scripts that have scripts and sink amount as values and the script indexes as keys.
    """

    # Fetch all source script tags from page html.
    all_scripts = get_scripts(source_html)
    sinks = {}  # Initialize empty dictionary for sinks.

    for script_index, script in all_scripts:
        sink_patterns = []

        regex_sink_matches = regex.finditer(SINKS_RE, str(script))

        # Look for sinks in script.
        for match in regex_sink_matches:
            match_groups = tuple(group for group in match.groups() if group is not None)
            sink_patterns.append(match_groups)
        if len(sink_patterns) > 0:
            sinks[script_index] = (sink_patterns, len(sink_patterns))

    return sinks


def check_forms(page_url: str, source_html: str) -> dict(int, soup.element.Tag):
    """
    This is a function to check every form input for possible xss vulnerability.
    A web browser checks for an alert and if it finds one it is vulnerable!
    Args:
        @param page_url (str): The url of the page to be checked. format should be "http://pageto.check:<optional port>/<required dirctories>/"
        @param source_html (str): The source html of the page to be checked.

    Returns:
        dict: A dictionary of all vulnerable inputs and their ids, id for key and `soup.element.Tag` as value.
    """
    # Create a chrome web driver.
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    options.add_argument("headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    browser = webdriver.Chrome(options=options)

    # Find forms in html.
    soup_obj = soup.BeautifulSoup(source_html, "html.parser")
    all_forms = soup_obj.find_all("form")

    # A dictionary containing all the results from our check.
    vulnerable_inputs = {}
    index = 0

    for form in all_forms:
        for input in list(set(form.find_all("input", type="text"))):
            input_id = index
            index += 1
            # Check each known xss string against input (more can be added if needed).
            for xss in XSS_STRINGS:
                if input_id in vulnerable_inputs.keys():
                    break
                # Generate url with correct url parameters.
                url = f"{page_url}{form.get('action')}?{input.get('id')}={xss}"
                # Get page with infected url.
                browser.get(url)
                try:
                    # Check for alert.
                    alert = browser.switch_to.alert
                    alert.accept()

                    # Add to vulnerable inputs list.
                    if input_id not in vulnerable_inputs.keys():
                        vulnerable_inputs[input_id] = input
                    else:
                        continue
                except:
                    pass  # No alert and therefor not vulnerable.
    return vulnerable_inputs


def find_input_fields(html: str) -> tuple:
    """
    Get all input fields and filter them to only useful input fields that can house text (can contain script tags).

    Args:
        html (str): The source html of the page to check.

    Returns:
        tuple: The tuple containing the results, explanation at the return line.
    """

    def input_filter_function(tag: soup.element.Tag) -> bool:
        """
        A filtering function for beautiful soup's `find_all` function to get all input tags that are of the types: `text`, `url` and `search`.

        Args:
            tag (soup.element.Tag): The current tag to filter

        Returns:
            bool: Is the tag appropriate according to our terms.
        """
        # If tag is of `input` type and has a `type` attribute.
        if tag.name != "input" or not tag.has_attr("type"):
            return False
        type_str = tag["type"].lower()
        # If input type is the type we want.
        if any([type_str == "text", type_str == "url", type_str == "search"]):
            return True

    soup_obj = soup.BeautifulSoup(html, "html.parser")
    # Find all input tags with our filter function.
    all_inputs = soup_obj.find_all(input_filter_function)
    form_inputs = []  # Empty list of inputs that are children of a form.

    # Seperate form inputs.
    for inp in all_inputs:
        # Check if input parent is form.
        if inp.parent.name == "form":
            form_inputs.append(inp)

    # (RETURN) a tuple which contains the following results:
    # [0]: a boolean expression which states if there are any inputs to check.
    # [1]: a list of inputs that belong to a form.
    # [2]: a list all inputs in the web page.
    return (
        len(all_inputs) > 0,
        form_inputs,
        all_inputs,
    )


def check_form_inputs(form_inputs: list, suspicious_scripts: dict) -> dict:
    """
    Go over each script and check if form input is used within it, if so it is possibly vulnerable!
    Different function from `check_all_inputs` since form inputs can be accessed differently.
    Reference: `https://stackoverflow.com/questions/18606305/accessing-formdata-values`

    Args:
        form_inputs (list): All form inputs.
        suspicious_scripts (dict): A dictionary containing all scripts that contain sources and/or sinks.

    Returns:
        dict: The dictionary of possibly very vulnerable scripts and their danger rating.
    """
    very_vulnerable = {}

    for script_index in suspicious_scripts.keys():
        script_str = suspicious_scripts[script_index][0]
        vuln_raises = 0

        if "FormData" in script_str:
            vuln_raises += script_str.count("FormData")

        for form_input in form_inputs:
            form_object = soup.Tag(form_input.parent)

            if (
                form_object.get("id") is not None
                and form_object.get("id") in script_str
            ):
                if (
                    f'getElementById("{form_object["id"]}").value' in script_str
                    or f"getElementById('{form_object['id']}').value" in script_str
                ):
                    vuln_raises += 1
            if (
                form_object.get("name") is not None
                and form_object.get("name") in script_str
            ):
                if (
                    f'getElementsByName("{form_object["name"]}")' in script_str
                    or f"getElementsByName('{form_object['name']}')" in script_str
                ):
                    vuln_raises += 1
            if (
                form_object.get("class") is not None
                and form_object.get("class") in script_str
            ):
                if (
                    f'getElementsByClassName("{form_object["class"]}")' in script_str
                    or f"getElementsByClassName('{form_object['class']}')" in script_str
                ):
                    vuln_raises += 1
        if vuln_raises > 0:
            very_vulnerable[script_index] = (
                suspicious_scripts[script_index],
                vuln_raises,
            )

    return very_vulnerable


def check_all_inputs(all_inputs: list, suspicious_scripts: dict) -> dict:
    """
    Go over each script and check if non form input is used within it, if so it is possibly vulnerable!
    Different function from `check_form_inputs` since form inputs can be accessed differently.
    Reference: `https://stackoverflow.com/questions/11563638/how-do-i-get-the-value-of-text-input-field-using-javascript`

    Args:
        all_inputs (list): All input tags.
        suspicious_scripts (dict): A dictionary containing all scripts that contain sources and/or sinks.

    Returns:
        dict: The dictionary of possibly very vulnerable scripts and their danger rating.
    """
    very_vulnerable = {}
    for script_index in suspicious_scripts.keys():
        vuln_raises = 0
        for input_tag in all_inputs:
            script_str = str(suspicious_scripts[script_index][0])

            if input_tag.get("id") is not None and input_tag.get("id") in script_str:
                if (
                    f'getElementById("{input_tag["id"]}").value' in script_str
                    or f"getElementById('{input_tag['id']}').value" in script_str
                ):
                    vuln_raises += 1
            if (
                input_tag.get("name") is not None
                and input_tag.get("name") in script_str
            ):
                if (
                    f'getElementsByName("{input_tag["name"]}")' in script_str
                    or f"getElementsByName('{input_tag['name']}')" in script_str
                ):
                    vuln_raises += 1
            if (
                input_tag.get("class") is not None
                and input_tag.get("class") in script_str
            ):
                if (
                    f'getElementsByClassName("{input_tag["class"]}")' in script_str
                    or f"getElementsByClassName('{input_tag['class']}')" in script_str
                ):
                    vuln_raises += 1

        if raises > 0:
            very_vulnerable[script_index] = (
                suspicious_scripts[script_index],
                vuln_raises,
            )

    return very_vulnerable


def further_analyse(suspicious_scripts: dict, input_sources: tuple) -> dict:
    """
    Further analyse each script that contained sinks,
    Check if any type of user input or a known source is used in any of the suspicious scripts,
    If so, they are way more likely to be vulnerable!

    Args:
        suspicious_scripts (dict): A dictionary containing all scripts that contain sources and/or sinks.
        input_sources (tuple): The returned tuple from `find_input_fields` function,
            containing various input fields to check individually.

    Raises:
        ValueError: `suspicious_scripts` parameter is empty list.
        ValueError: `input_sources` parameter is not in valid format, size should be 3.
        ValueError: The first value in `input_sources` parameter is false,
            meaning there are no input sources in given page and therefor no possible vulnerabilities.

    Returns:
        dict: A dictionary containing the more vulnerable script indexes as keys and the scripts themselves and their final danger levels as values.
    """

    if len(suspicious_scripts) == 0:
        raise ValueError("No suspicious scripts were given to further analyse!")
    elif len(input_sources) != 3:
        raise ValueError("Input sources were given in wrong format!")

    dom_sources = {}
    for script_index in suspicious_scripts.keys():
        regex_source_matches = regex.finditer(
            SOURCES_RE, str(suspicious_scripts[script_index])
        )
        # Look for dom_sources in script.
        source_patterns = []
        for match_index, match in enumerate(regex_source_matches):
            match_groups = tuple(group for group in match.groups() if group is not None)
            source_patterns.append(match_groups)
        if len(source_patterns) > 0:
            dom_sources[script_index] = (source_patterns, len(regex_source_matches))

    are_there_inputs, form_inputs, all_inputs = input_sources
    if (
        not are_there_inputs and len(dom_sources.keys()) == 0
    ):  # No input sources in html.
        raise ValueError("There are no input sources in the given page!")

    form_scripts = None
    if len(form_inputs) > 0:
        form_scripts = check_form_inputs(form_inputs, suspicious_scripts)
    general_scripts = check_all_inputs(all_inputs, suspicious_scripts)

    final_scripts = {}

    for script_index in dom_sources.keys():
        if script_index not in final_scripts.keys():
            final_scripts[script_index] = dom_sources[script_index]
        else:
            final_scripts[script_index] = (
                final_scripts[script_index][0],
                final_scripts[script_index][1] + dom_sources[script_index][1],
            )
    for script_index in general_scripts.keys():
        if script_index not in final_scripts.keys():
            final_scripts[script_index] = general_scripts[script_index]
        else:
            final_scripts[script_index] = (
                final_scripts[script_index][0],
                final_scripts[script_index][1] + general_scripts[script_index][1],
            )

    if form_scripts is None:
        return final_scripts
    for script_index in form_scripts.keys():
        if script_index not in final_scripts.keys():
            final_scripts[script_index] = form_scripts[script_index]
        else:
            final_scripts[script_index] = (
                final_scripts[script_index][0],
                final_scripts[script_index][1] + form_scripts[script_index][1],
            )

    return final_scripts
