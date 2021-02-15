#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
import bs4 as soup
import re as regex  #? Used `https://regex101.com/` a lot to verify regex string.


COLOR = COLOR_MANAGER.rgb(169, 69, 169)
# The regex strings used to find all dom-xss sources.
SOURCES_RE = """(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)|\s*URLSearchParams[\(.]|\s*[.]*(getElementById|getElementByName|getElementByClassName)\("""
# The regex string used to find all dom-xss sinks.
SINKS_RE = """(document\.((write|writeln)\(|(domain\s*=))+)|.(innerHTML|outerHTML|insertAdjacentHTML|onevent)\s*=|((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getsource_htmlHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()"""
RESULT_STR = "The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts.\n" \
                "\t\t\tIf you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.\n" \
                "\t\t\tAvoid dangerous methods and instead use safer functions.\n" \
                "\t\t\tCheck if sources are directly related to sinks and if so prevent them from accessing each other.\n" \
                "\t\t\tFor more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html\n"


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
                                  f"\t\t\tThe Line is: {find_script_by_src(page.parent.content, page.url)}\n" \
                                  f"\t\t\tFrom page {page.parent.url}\n"
                    
                    res = Data.PageResult(page.parent, problem_str, RESULT_STR)
                    dom_xss_results.page_results.append(res)
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
            pass # No vulnerability was found.

        if len(vulnerable_dom_scripts.keys()) > 0:
            for script_index in vulnerable_dom_scripts.keys():
                script_tuple = vulnerable_dom_scripts.get(script_index, None)
                if script_tuple is None:
                    continue
                problem_str = f"Found a quite possibly vulnerable script to DOM based XSS (Script Index [{script_index}]).\n" \
                                f"\t\t\tThe script is: {str(script_tuple[0])}\n" \
                                f"\t\t\tThe sink patterns are: {str(script_tuple[1])}\n" \
                                f"\t\t\tThe source patterns are: {str(script_tuple[2])}\n" \
                                f"\t\t\tDanger level is {str(script_tuple[3])}\n"
               
                res = Data.PageResult(page, problem_str, RESULT_STR)
                dom_xss_results.page_results.append(res)

        if len(vulnerable_input_scripts.keys()) > 0:
            for script_index in vulnerable_input_scripts.keys():
                script_tuple = vulnerable_input_scripts.get(script_index, None)
                if script_tuple is None:
                    continue
                problem_str = f"Found a quite possibly vulnerable script to DOM based XSS (Script Index [{script_index}]).\n" \
                                f"\t\t\tThe script is: {str(script_tuple[0])}\n" \
                                f"\t\t\tThe sink patterns are: {str(script_tuple[1])}\n" \
                                f"\t\t\tThe input sources are: {str(script_tuple[2])}\n" \
                                f"\t\t\tDanger level is {str(script_tuple[3])}\n"
               
                res = Data.PageResult(page, problem_str, RESULT_STR)
                dom_xss_results.page_results.append(res)

    data.mutex.acquire()
    data.results.append(dom_xss_results)
    data.mutex.release()


def analyse_javascript(javascript_code:str):
    """
    This function looks for sinks and sources within the javascript included code.
    If it finds both at least one source and at least one sink it will return true.
    @param javascript_code (str): The source javascript page code.
    @returns bool: is the javascript source code possibly vulnerable (yes/no).
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
    @param html (str): The source html of the page.
    @param src (bool, optional): Should we search for script tags with src attribute. Defaults to False.
    @returns (list): enumerated list of script tags.
    """
    soup_obj = soup.BeautifulSoup(html, "html.parser")
    source_scripts = soup_obj.find_all("script", src=src)
    return list(enumerate(source_scripts))


def find_script_by_src(html: str, page_url:str):
    """
    This function finds a single script that has a src attribute and the source 
    is the specified page url.
    @param html: (str): The source html of the page in which we want to find the script tag.
    @param page_url: (str): The url of the source javascript page that will be searched for in the element.
    @returns (soup.element.Tag): The script tag that contained the page_url as a src attribute.
    """
    soup_obj = soup.BeautifulSoup(html, "html.parser")
    def script_filter(tag: soup.element.Tag):
        return tag.name == "script" and tag.has_attr("src") and page_url.endswith(tag["src"])
    scripts = soup_obj.find_all(script_filter, limit=1)
    return scripts[0]


def get_script_by_id(source_html:str, script_id:int):
    """
    @param source_html (str): The source html of the page in which we want to find the script tag.
    @param script_id (int): The id of the script tag (it's index from the top).
    @returns (soup.element.Tag): The script tag of the correct index or None if script was not found.
    """
    soup_obj = soup.BeautifulSoup(source_html, "html.parser")
    all_scripts = soup_obj.find_all("script")
    if script_id > -1 and script_id < len(all_scripts):
        return all_scripts[script_id]
    else:
        return None


def determine_possible_vulns(source_html: str):
    """
    A vulnerable script is a script which contains a sink which can be used to execute xss via a source.
    A script cannot be vulnerable without a sink so first we validate the existance of a sink with a regex containing all sinks.
    @param source_html (str): The source html of the web page to analyze.
    @returns (dict): A dictionary containing the scripts that has a tuple of sink patterns and their amount as values and the script indexes as keys.
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
    @param html (str): The source html of the page to check.
    @returns (tuple): The tuple containing the results, explanation at the return line.
    """

    def input_filter_function(tag: soup.element.Tag):
        """
        A filtering function for beautiful soup's `find_all` function to get all input tags that are of the types: `text`, `url` and `search`.
        @param tag: (soup.element.Tag): The current tag to filter.
        @returns (bool): Is the tag appropriate according to our terms.
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
    @param form_inputs (list): All form inputs.
    @param suspicious_scripts (dict): A dictionary containing all scripts that contain sources and/or sinks.
    @returns (dict): The dictionary of possibly very vulnerable scripts and their danger rating.
    """
    very_vulnerable = {}
    for script_index in suspicious_scripts.keys():
        script_str = suspicious_scripts[script_index][0]
        vuln_raises = 0
        vulnerable_inputs = []

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
    @param all_inputs (list): All input tags.
    @param suspicious_scripts (dict): A dictionary containing all scripts that contain sources and/or sinks.
    @returns (dict): The dictionary of possibly very vulnerable scripts and their danger rating.
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
    @param suspicious_scripts (dict): A dictionary containing all scripts that contain sinks.
        ? { script_index :  (script_string, regex_sink_patterns), ... }
    @param input_sources (tuple): The returned tuple from `find_input_fields` function, containing various input fields to check individually.

    !Raises:
    !    ValueError: `suspicious_scripts` parameter is empty list.
    !    ValueError: `input_sources` parameter is not in valid format, size should be 3.
    !    ValueError: The first value in `input_sources` parameter is false,
    !        meaning there are no input sources in given page and therefor no possible vulnerabilities.
    @returns (dict): A dictionary containing the more vulnerable script indexes as keys and the scripts themselves and their final danger levels as values.
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