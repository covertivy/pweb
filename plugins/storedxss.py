import Data
from colors import COLOR_MANAGER
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
        csp_info: dict= headerAnalyzer.csp_check(page)
        if not csp_info['allow_scripts'] and not csp_info['allow_images']:
            # Page is protected by csp but should be checked for content security policy bypass vulnerability.
            pass
        if not csp_info['allow_scripts']:
            # Cannot run disallowed scripts on this page.
            pass
        if not csp_info['allow_images']:
            # Cannot add disallowed images on this page. 
            pass
        
        # TODO: verify this check is working with new page manager.
        vulnerable_inputs = brute_force_alert(data, page.url, page.content)
        
        # TODO: finish delivery of analysis.

    data.mutex.acquire()
    data.results.append(stored_xss_results)
    data.mutex.release()


def brute_force_alert(data: Data.Data, page_url: str, source_html: str) -> dict:
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

    # Create a chrome web driver.
    browser = data.new_browser()

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

            payloads = ""
            with open(PAYLOADS_PATH, 'r') as file:
                payloads = file.read().split('\n')

            for xss in payloads:
                if input_id in vulnerable_inputs.keys():
                    break
                # Generate url with correct url parameters.
                response = data.submit_form([input], browser)
                
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
    
    browser.close()
    return vulnerable_inputs