import Data

def csp_check(page: Data.Page):
    res_dict = {'allow_scripts': False, 'allow_images': False}
    headers: dict = page.request.response.headers
    print(headers)
    if headers.get('Content-Security-Policy', None) is not None:
        csp_param_str = headers.get('Content-Security-Policy').lstrip().rstrip()
        print(csp_param_str)
        for param in csp_param_str.split('; '):
            # A param string will be "<param_name> <list of args separated by spaces>"
            # A param list will be [param_name, args...]
            param_args = param.split(' ')
            if param_args[0] == 'script_src':
                res_dict['allow_scripts'] = analyzeScriptSrcParams(param_args)
            elif param_args[0] == 'img_src':
                res_dict['allow_images'] = analyzeImageSrcParams(param_args)
    return res_dict

def analyzeScriptSrcParams(param_args: list):
    if '*' in param_args[1:]:
        return True
    return False

def analyzeImageSrcParams(param_args: list):
    if '*' in param_args[1:]:
        return True
    return False