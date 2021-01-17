import Data
from colors import COLOR_MANAGER
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

COLOR = COLOR_MANAGER.TURQUOISE

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


def logic(data: Data.Data):
    stored_xss_results = Data.CheckResults("Stored XSS", COLOR)
    data.mutex.acquire()
    pages = data.pages
    data.mutex.release()

    for page in pages:
        vulnerable_inputs = check_forms(page.url, page.content)
        if len(vulnerable_inputs.keys()) > 0:
            for vulnerable_input_id in vulnerable_inputs.keys():
                problem_str = f"Found xss vulnerability in input [{vulnerable_input_id}].\nThe input is: {str(vulnerable_inputs[vulnerable_input_id])}"
                result_str = "The primary rule that you must follow to prevent DOM XSS is: sanitize all untrusted data, even if it is only used in client-side scripts. If you have to use user input on your page, always use it in the text context, never as HTML tags or any other potential code.\nAvoid dangerous methods and instead use safer functions.\nCheck if sources are directly related to sinks and if so prevent them from accessing each other.\nFor more information please visit: https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html"
                res = Data.PageResult(page, problem_str, result_str)
                stored_xss_results.page_results.append(res)

    data.mutex.acquire()
    data.results.append(stored_xss_results)
    data.mutex.release()


def check_forms(page_url: str, source_html: str) -> dict:
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
    soup = BeautifulSoup(source_html, "html.parser")
    all_forms = soup.find_all("form")

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