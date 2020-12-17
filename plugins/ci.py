#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests


COLOR = COLOR_MANAGER.rgb(255, 255, 0)
problematic = list()


def check(data: Data.Data):
    """

    @param data:
    @return:
    """
    ci_results = Data.CheckResults("Command Injection", COLOR)

    data.mutex.acquire()
    pages = data.pages  # Achieving the pages
    data.mutex.release()
    # Filtering the pages list
    pages = filter_forms(pages)

    results = list()
    for page, form in pages:
        ci_results.page_results.append(Data.PageResult(page, form, ""))

    for page, form in results:
        ci_results.page_results.append(page)

    data.mutex.acquire()
    data.results.append(ci_results)  # Adding the results to the data object
    data.mutex.release()


def filter_forms(pages: list) -> list:
    """

    @param pages:
    @return:
    """
    filtered_pages = list()
    for page in pages:
        if "html" not in page.type:
            # If it is a non-html page we can not check for command injection
            continue
        forms = BeautifulSoup(page.content, "html.parser").find_all("form")  # Getting page forms
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
                form_details["action"] = action
                form_details["method"] = method
                form_details["inputs"] = inputs
                # Adding the page and it's form to the list
                filtered_pages.append((page, form_details))
            except:
                continue
    return filtered_pages


def command_injection(page: Data.Page, form: dict) -> Data.PageResult:
    """

    @param page:
    @param form:
    @return:
    """
    # Join the url with the action (form request URL)
    action_url = urljoin(page.url, form["action"])  # Getting action URL
    pass
    return None
