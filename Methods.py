import Data
from seleniumwire import webdriver, request as selenium_request


def new_browser(data: Data, session_page=None,
                debug: bool = False, interceptor=None) -> webdriver.Chrome:
    """
    Function creates a new browser instance for new session
    @param data: The data object of the program
    @param session_page: In case session, the browser needs the cookies and URL
    @param debug: In case of debugging, True will make the chromium window appear
    @param interceptor:
    @return: Chrome driver object
    """
    if not data.driver:
        # There is no driver file path
        raise Exception("There is no driver file path", "\t")
    options = webdriver.ChromeOptions()
    if not debug:
        # If it's not debug, the chromium will be headless
        options.add_argument("headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    try:
        browser = webdriver.Chrome(executable_path=data.driver, options=options)
    except Exception as e:
        # In case of failure, we need to try again
        return new_browser(data, session_page, debug)

    def default_interceptor(request: selenium_request):
        """
        Inner function acts like proxy, it aborts every requests that we don't want
        @param request: The current request
        @return: None
        """
        # Block PNG, JPEG and GIF images
        if request.path.endswith(('.png', '.jpg', '.gif')):
            # Save run time
            request.abort()
    # Setting request interceptor
    if interceptor:
        browser.request_interceptor = interceptor
    else:
        browser.request_interceptor = default_interceptor
    # Setting long timeout
    browser.set_page_load_timeout(60)
    if session_page:
        # In case of session page
        browser.get(session_page.parent)  # Getting parent URL
        for cookie in session_page.cookies:  # Adding cookies
            browser.add_cookie(cookie)
        # Getting the page again, with the cookies
        browser.get(session_page.url)
    return browser
