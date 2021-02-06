import Data

def csp_check(page: Data.Page) -> dict:
    res_dict = {'allow_scripts': False, 'allow_images': False}
    headers: dict = page.request.response.headers
    print(headers)
    if headers.get('Content-Security-Policy', None) is not None:
        csp_params = headers.get('Content-Security-Policy').split('; ')
        print(csp_params)
        for param in csp_params:
            if param.startswith('script_src'):
                res_dict['allow_scripts'] = analyzeScriptSrcParams(param)
            elif param.startswith('img_src'):
                res_dict['allow_images'] = analyzeImageSrcParams(param)
    return res_dict

def analyzeScriptSrcParams(param: str) -> bool:
    param_args = param.split(' ')
    # TODO:
    # Finish parameter checking for csp.
    pass

def analyzeImageSrcParams(param: str) -> bool:
    param_args = param.split(' ')
    # TODO:
    # Finish parameter checking for csp.
    pass