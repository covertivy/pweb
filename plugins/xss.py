#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
import bs4 as soup
import re as regex  # Import the Regex Module.
from threading import Lock


COLOR = COLOR_MANAGER.rgb(255, 0, 100)
SOURCES_RE = regex.compile(
    """/(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)/"""
)  # The regex string used to find all dom-xss sources.
SINKS_RE = regex.compile(
    """/((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getsource_htmlHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()/"""
)  # The regex string used to find all dom-xss sinks.


def check(data: Data.Data):
    dom_xss_results = Data.CheckResults("XSS", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()
    for page in pages:
        possible_vulns = determine_vulns(page.content)
        if len(possible_vulns.keys()) > 0:
            amount_str = ""
            if len(possible_vulns.keys()) == 1:
                amount_str = "script that was"
            else:
                amount_str = "scripts that were"

            scripts_str = ""
            for script_index in possible_vulns.keys():
                scripts_str = scripts_str + f"Script {script_index}.\n"

            problem_str = f"Found {len(possible_vulns.keys())} {amount_str} possibly vulnerable to DOM based XSS.\n{scripts_str}"
            result_str = "The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts. If you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.\nAvoid dangerous methods and instead use safer functions.\nCheck if sources are directly related to sinks and if so prevent them from accessing each other.\nFor more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html"
            res = Data.PageResult(page, problem_str, result_str)
            dom_xss_results.page_results.append(res)
    data.mutex.acquire()
    data.results.append(dom_xss_results)
    data.mutex.release()


def get_scripts(html: str, src: bool = False):
    soup_obj = soup.BeautifulSoup(html, "html.parser")
    source_scripts = soup_obj.find_all("script", src=src)
    return list(enumerate(source_scripts))


def determine_vulns(source_html: str):
    all_scripts = get_scripts(source_html)
    sources = {}
    sinks = {}

    for script_index, script in all_scripts:
        source_patterns = []
        for pattern in regex.finditer(SOURCES_RE, str(script)):
            pattern_groups = tuple(
                group for group in pattern.groups() if group is not None
            )
            source_patterns.append(pattern_groups)
        if len(source_patterns) > 0:
            sources[script_index] = source_patterns

        sink_patterns = []
        for pattern in regex.finditer(SINKS_RE, str(script)):
            pattern_groups = tuple(
                group for group in pattern.groups() if group is not None
            )
            sink_patterns.append(pattern_groups)
        if len(sink_patterns) > 0:
            sinks[script_index] = sink_patterns

    suspicious_scripts = {}
    for script_index in range(all_scripts[-1][0] + 1):
        if (
            sources.get(script_index, None) is not None
            and sinks.get(script_index, None) is not None
        ):
            suspicious_scripts[script_index] = all_scripts[script_index][1]

    return suspicious_scripts
