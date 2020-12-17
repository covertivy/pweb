#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
import re  # Import the Regex Module.
from threading import Lock


COLOR = COLOR_MANAGER.rgb(255, 0, 100)
SOURCES_RE = re.compile(
    """/(location\s*[\[.])|([.\[]\s*["']?\s*(arguments|dialogArguments|innerHTML|write(ln)?|open(Dialog)?|showModalDialog|cookie|URL|documentURI|baseURI|referrer|name|opener|parent|top|content|self|frames)\W)|(localStorage|sessionStorage|Database)/"""
) # The regex string used to find all dom-xss sources.
SINKS_RE = re.compile(
    """/((src|href|data|location|code|value|action)\s*["'\]]*\s*\+?\s*=)|((replace|assign|navigate|getsource_htmlHeader|open(Dialog)?|showModalDialog|eval|evaluate|execCommand|execScript|setTimeout|setInterval)\s*["'\]]*\s*\()/"""
) # The regex string used to find all dom-xss sinks.

def check(data: Data.Data):
    xss_results = Data.CheckResults("XSS", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()
    for page in pages:
        # TODO: Perform page evaluation here.
        res = Data.PageResult(page, "unknown problem", "unknown solution")
        xss_results.page_results.append(res)
    data.mutex.acquire()
    data.results.append(xss_results)
    data.mutex.release()


def find_dom(page: Data.Page):

def parse_javascript(source_html: Page.content):
    embedded_javascript = []
    linked_javascript = []
    # Parse the page for embedded_javascript javascript
    index = 0
    in_js_tag = False
    inscript = False
    insrc = False
    embedded_index = 0
    linked_index = 0

    while index <= len(source_html) - 1:
        if source_html[index : index + 7].lower() == "<script":
            in_js_tag = True
            index += 7
            continue
        if source_html[index : index + 4].lower() == "src=" and in_js_tag:
            insrc = True
            linked_javascript.append("")
            index += 4
            continue
        if (source_html[index] == '"' or source_html[index] == "'") and insrc:
            index += 1
            continue
        if (source_html[index] == '" ' or source_html[index] == "' ") and insrc:
            insrc = False
            linked_index += 1
            index += 2
            continue
        if (
            (source_html[index] == '">' or source_html[index] == "'>")
            and insrc
            and in_js_tag
        ):
            insrc = False
            in_js_tag = False
            linked_index += 1
            index += 2
            continue
        if source_html[index] == " " and insrc:
            insrc = False
            linked_index += 1
            index += 1
            continue
        if source_html[index] == ">" and insrc and in_js_tag:
            insrc = False
            in_js_tag = False
            inscript = True
            embedded_javascript.append("")
            linked_index += 1
            index += 1
            continue
        if source_html[index] == ">" and in_js_tag:
            in_js_tag = False
            inscript = True
            embedded_javascript.append("")
            index += 1
            continue
        if source_html[index : index + 9].lower() == "</script>" and inscript:
            inscript = False
            embedded_index += 1
            index += 9
            continue
        if inscript:
            embedded_javascript[embedded_index] += source_html[index]
        if insrc:
            linked_javascript[linked_index] += source_html[index]

        index += 1

    # Parse the linked_javascript javascripts
    new_linked = []
    base_url = Data.url

    if base_url.endswith('/') or base_url.endswith('\\'):
        base_url = base_url[:-1]

    for link in linked_javascript:
        if link == "":
            continue
        if link[0 : len(base_url)] == base_url:
            new_linked.append(link)
            continue
        elif (
            link[0:7] == "http://"
            or link[0:4] == "www."
            or link[0:8] == "https://"
            or link[0:2] == "//"
        ):
            if link[0:2] == "//":
                link = "http:" + link
            new_linked.append(link)
            continue
        elif link[0] == "/":
            new_linked.append(base_url + link)
            continue
        else:
            new_linked.append(base_url + "/" + link)

    # Remove duplicates
    linked_javascript = list(set(new_linked))

    # Return all javascript retrieved
    # javascript = [ [target, content], ... ]

    for link in linked_javascript:
        try:
            to = 10 if self.engine.getOption("http-proxy") is None else 20
            source_html = self.browser.open(link, timeout=to)
        except HTTPError, e:
            self._addError(e.code, link)
            continue
        except URLError, e:
            self._addError(e.reason, link)
            continue
        except:
            self._addError("Unknown", link)
            continue
        else:
            j = Javascript(link, source_html.read())
            self.javascript.append(j)

    for r in embedded_javascript:
        if r is not "":
            j = Javascript(target.getAbsoluteUrl(), r, True)
            self.javascript.append(j)
