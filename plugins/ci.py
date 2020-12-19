#!/usr/bin/python3
from colors import COLOR_MANAGER
import Data
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests


COLOR = COLOR_MANAGER.rgb(255, 255, 0)
#  chars_to_filter = ["&", "&&", "|", "||", ";", "\n"]


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
    pages = filter_forms(pages)  # [(page object, form dict),...]
    for page, form in pages:
        result = command_injection(page, form)
        if result:
            # If there is a problem with the page
            ci_results.page_results.append(result)

    data.mutex.acquire()
    data.results.append(ci_results)  # Adding the results to the data object
    data.mutex.release()


def filter_forms(pages: list) -> list:
    """
    Function filters the pages that has an action form
    @param pages:List of pages
    @return: List of pages that has an action form
    """
    filtered_pages = list()
    for page in pages:
        if "html" not in page.type.lower():
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
                if len(get_text_inputs(form_details)) != 0:
                    # If there are no text inputs, it can't be command injection
                    filtered_pages.append((page, form_details))
            except:
                continue
    return filtered_pages


def command_injection(page, form: dict):
    """

    @param page:
    @param form:
    @return:
    """
    print(f"{page.url} : {non_blind(page, form)}")
    return None


def get_text_inputs(form) -> list:
    text_inputs = list()
    for input_tag in form["inputs"]:
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            if input_tag["type"] and input_tag["type"] == "text":
                text_inputs.append(input_tag)
    return text_inputs


def non_blind(page, form: dict):
    """

    @param page:
    @param form:
    @return:
    """
    chars_to_filter = ["&", "&&", "|", "||", ";", "\n"]
    # Join the url with the action (form request URL)
    action_url = urljoin(page.url, form["action"])  # Getting action URL
    text_inputs = get_text_inputs(form)  # Getting the text inputs
    results = dict()
    for text_input in text_inputs:
        # Setting keys for the results
        results[text_input["name"]] = list()
    for char in chars_to_filter:
        for curr_text_input in text_inputs:  # In case of more than one text input
            # Setting session for connection
            session = requests.Session()
            if type(page) == Data.SessionPage:
                # In case of session page
                session.cookies = page.cookies
            # The arguments body we want to submit
            args = dict()
            for input_tag in form["inputs"]:
                # Using the specified value
                if "name" in input_tag.keys():
                    # Only if the input has a name
                    # args[input_tag["name"]] = input_tag["value"]
                    if input_tag["name"] == curr_text_input["name"]:
                        args[input_tag["name"]] = f"{char} echo 'checkcheck'"
                    else:
                        args[input_tag["name"]] = input_tag["value"]
            # Sending the request
            content = str()
            if form["method"] == "post":
                content = session.post(action_url, data=args).text
            elif form["method"] == "get":
                content = session.get(action_url, params=args).text

            if "checkcheck" in content and "echo" not in content and "'checkcheck'" not in content:
                results[curr_text_input["name"]].append(char)
    return results


def blind(page, form: dict):
    """

    @param page:
    @param form:
    @return:
    """
    chars_to_filter = ["&", "&&", "|", "||", ";", "\n"]
    # Join the url with the action (form request URL)
    action_url = urljoin(page.url, form["action"])  # Getting action URL
    # Setting session for connection:
    session = requests.Session()
    if type(page) == Data.SessionPage:
        # In case of session page
        session.cookies = page.cookies
    # The arguments body we want to submit
    args = dict()
    for input_tag in form["inputs"]:
        # Using the specified value
        if "name" in input_tag.keys():
            # Only if the input has a name
            # args[input_tag["name"]] = input_tag["value"]
            if input_tag["type"] and input_tag["type"] == "text":
                args[input_tag["name"]] = "| echo checkcheck"
            else:
                args[input_tag["name"]] = input_tag["value"]
    # Sending the request
    if form["method"] == "post":
        content = session.post(action_url, data=args).text
    elif form["method"] == "get":
        content = session.get(action_url, params=args).text
    else:
        return None