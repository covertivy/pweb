import colors
import Data

COLOR_MANAGER = colors.Colors()

def charr_to_string(arr: list) -> str:
    to_ret = ""
    for item in arr:
        to_ret += str(item)
    return to_ret


def get_final_args(args) -> Data.Data:
    output_obj = Data.Data()

    if type(args.login) != None:
        if len(args.login) == 2:
                output_obj.username = charr_to_string(args.login[0])
                output_obj.password = charr_to_string(args.login[1])
            # Username. Password.
    
    output_obj.ip = args.ip
    output_obj.address = args.url

    if args.port < 1 or args.port > 65535:
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + "[!] Invalid port number, using default port 80."
            + COLOR_MANAGER.ENDC
        )
        output_obj.port = 80
    else:
        output_obj.port = args.port

    output_obj.all_ports = args.ALL_PORTS
    output_obj.max_pages = args.number_of_pages
    output_obj.folder = args.output
    
    return output_obj