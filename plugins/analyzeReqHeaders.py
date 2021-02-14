import Data

def csp_check(page: Data.Page):
    res_dict = {'allow_scripts': {}, 'allow_images': {}}
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
    else: 
        return None

def analyzeScriptSrcParams(param_args: list):
    res_dict = {'*': False, 'unsafe_eval': False, 'unsafe_inline': False, 'unsafe_hashes': False}
    for arg in param_args[1:]:
        if arg == '*':
            res_dict['*'] = True
        elif arg == 'unsafe_eval': 
            res_dict['unsafe_eval'] = True
        elif arg == 'unsafe_inline':
            res_dict['unsafe_inline'] = True
        elif arg == 'unsafe_hashes':
            res_dict['unsafe_hashes'] = True
    return res_dict

def analyzeImageSrcParams(param_args: list):
    res_dict = {'*': False}
    for arg in param_args[1:]:
        if arg == '*':
            res_dict['*'] = True
    return res_dict