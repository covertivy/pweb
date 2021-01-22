#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
import bs4 as soup
import re as regex  # Used `https://regex101.com/` a lot to verify regex string.
from selenium import webdriver


COLOR = COLOR_MANAGER.rgb(255, 0, 100)
# The regex strings used to find all dom-xss sources.
SOURCES_RE = """(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)|\s*URLSearchParams[\(.]|\s*[.]*(getElementById|getElementByName|getElementByClassName)\("""
# The regex string used to find all dom-xss sinks.
SINKS_RE = """((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getsource_htmlHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()"""

XSS_STRINGS = [
    "<script>alert(1);</script>",
    "><script>alert(1);</script>",
    "'<script>alert(1);</script>",
    "<img src=x onerror=alert(1)>",
    '<img src="javascript:alert(1);">',
    "<img src=javascript:alert(1)>",
    "<img src=javascript:alert(&quot;1&quot;)>",
    "<img src=x onerror=javascript:alert(1)>",
    "<img src=x onerror=javascript:alert(1);>",
    "<<SCRIPT>alert(1);//\<</SCRIPT>",
]


def check(data: Data.Data):
    dom_xss_results = Data.CheckResults("DOMXSS", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()

    for page in pages:
        if "html" not in page.type:
            if "javascript" in page.type:
                # Look for sources and sinks in javascript source code.
                if analyse_javascript(page.content):
                    problem_str = f"Found javascript code that is quite possibly vulnerable to DOM based XSS:\n" \
                                  f"\tThe Line is: {find_script_by_src(page.parent.content, page.url)}\n" \
                                  f"\tFrom page {page.parent.url}\n"
                    result_str = "The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts.\n" \
                                 "\tIf you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.\n" \
                                 "\tAvoid dangerous methods and instead use safer functions.\n" \
                                 "\tCheck if sources are directly related to sinks and if so prevent them from accessing each other.\n" \
                                 "\tFor more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html\n"
                    res = Data.PageResult(page.parent, problem_str, result_str)
                    dom_xss_results.page_results.append(res)
            else:
                 continue  # Ignore non javascript pages.       

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
                script = get_script_by_id(page.content, script_index)
                if script is None:
                    continue
                problem_str = f"Found a quite possibly vulnerable script to DOM based XSS (Script Index [{script_index}]).\n" \
                                f"\tThe script is: {str(script)}\n"
                result_str = "The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts.\n" \
                                 "\tIf you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.\n" \
                                 "\tAvoid dangerous methods and instead use safer functions.\n" \
                                 "\tCheck if sources are directly related to sinks and if so prevent them from accessing each other.\n" \
                                 "\tFor more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html\n"                res = Data.PageResult(page, problem_str, result_str)
                dom_xss_results.page_results.append(res)

    data.mutex.acquire()
    data.results.append(dom_xss_results)
    data.mutex.release()


def analyse_javascript(javascript_code:str) -> bool:
    """[summary]
    This function looks for sinks and sources within the javascript included code.
    If it finds both at least one source and at least one sink it will return true.
    Args:
        javascript_code (str): The source javascript page code.

    Returns:
        bool: is the javascript source code possibly vulnerable (yes/no).
    """
    match_sources_in_code = regex.finditer(SOURCES_RE, javascript_code)
    match_sinks_in_code = regex.finditer(SINKS_RE, javascript_code)

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


def get_scripts(html: str, src: bool = False) -> list:
    soup_obj = soup.BeautifulSoup(html, "html.parser")
    source_scripts = soup_obj.find_all("script", src=src)
    return list(enumerate(source_scripts))


def find_script_by_src(html: str, page_url:str) -> soup.Tag:
    soup_obj = soup.BeautifulSoup(html, "html.parser")
    def script_filter(tag, page_url:str) -> bool:
        return tag.name == "script" and tag.has_attr("src") and page_url.endswith(tag["src"])
    script = soup_obj.find(script_filter, page_url)
    return script


def get_script_by_id(source_html:str, script_id:int) -> soup.Tag:
    soup_obj = soup.BeautifulSoup(source_html, "html.parser")
    all_scripts = soup_obj.find_all("script")
    if script_id > -1 and script_id < len(all_scripts):
        return all_scripts[script_id]
    else:
        return None


def determine_possible_vulns(source_html: str) -> dict:
    """
    A vulnerable script is a script which contains a sink which can be used to execute xss via a source.
    A script cannot be vulnerable without a sink so first we validate the existance of a sink with a regex containing all sinks.
    Args:
        source_html (str): The source html of the web page to analyze.

    Returns:
        dict: a dictionary containing the scripts that has a tuple of sink patterns and their amount as values and the script indexes as keys.
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

        # Get rid of duplicate regex matches.
        sink_patterns = list(set(sink_patterns))

        if len(sink_patterns) > 0:
            sinks[script_index] = (sink_patterns, len(sink_patterns))

    return sinks


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
        if any(
            [
                type_str == "text",
                type_str == "url",
                type_str == "search",
                type_str == "select",
            ]
        ):
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
        for match in regex_source_matches:
            match_groups = tuple(group for group in match.groups() if group is not None)
            source_patterns.append(match_groups)

        # Get rid of duplicate regex matches.
        source_patterns = list(set(source_patterns))

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
            print(
                f"Adding vulnerable script to final_scripts!\n{suspicious_scripts[script_index]}"
            )
            final_scripts[script_index] = dom_sources[script_index]
        else:
            final_scripts[script_index] = (
                final_scripts[script_index][0],
                final_scripts[script_index][1] + dom_sources[script_index][1],
            )

    if len(general_scripts.keys()) == 0:
        return final_scripts
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
