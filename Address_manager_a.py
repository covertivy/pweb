#!/usr/bin/python3
import nmap
import Data
import colors

    """
    if not validIPAddress(args.ip):
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + "[!] Invalid IP address, using default localhost."
            + COLOR_MANAGER.ENDC
        )
        args.ip = "127.0.0.1"
    """
def url_port(url: str, existing_port: int):
    try:
        token = urllib.parse.urlparse(url)
        port = token.port
    except ValueError as e:
        print(
            COLOR_MANAGER.BRIGHT_YELLOW
            + f"[!] {e}, using port {existing_port}."
            + COLOR_MANAGER.ENDC
        )
        return existing_port
    if not port:
        return existing_port
    return port


def validIPAddress(IP: str) -> bool:
    """
      :type IP: str
      :rtype: str
      """

    def isIPv4(s):
        try:
            return str(int(s)) == s and 0 <= int(s) <= 255
        except:
            return False

    if IP.count(".") == 3 and all(isIPv4(i) for i in IP.split(".")):
        return True
    return False


def valid_url(url: str) -> bool:
    token = urllib.parse.urlparse(url)

    min_attributes = ("scheme", "netloc")  # protocol and domain
    if not all([getattr(token, attr) for attr in min_attributes]):
        return False
    elif "." not in str(getattr(token, "netloc")):
        return False
    else:
        return True


def scan(data: Data.Data, url=False):
    nm = nmap.PortScanner()  # instantiate nmap.PortScanner object
    nm.scan(hosts=data.address, ports=str(data.port))  # scan host, ports from 22 to 443
    # print("Command: " + nm.command_line())  # get command line used for the scan

    if len(nm.all_hosts()) == 0:
        raise Exception("[!] Error! No hosts found!")

    for host in nm.all_hosts():
        for proto in nm[host].all_protocols():
            lport = list(nm[host][proto].keys())
            lport.sort()

            for port in lport:
                # print(nm[host][proto][port])
                print('┌----------------------------------------------------')
                print('|\tPort: {} | Protocol: {}'.format(port, nm[host][proto][port]['name']))
                print(f"|\tState:   {nm[host][proto][port]['state']}")
                print(f"|\tService: {nm[host][proto][port]['product']}")
                # print(f"|\tVersion: {nm[host][proto][port]['version']}")
                # print(f"|\tSystem:  {nm[host][proto][port]['extrainfo']}")

        print('└----------------------------------------------------')
    return nm


def check_for_http(nm, data: Data.Data) -> bool:
    if data.address not in nm.all_hosts() or nm[data.address]['status']['state'] != 'up':
        return False
    host = nm[data.address]
    proto_list = host.all_protocols()
    for proto in proto_list:
        ports = list(host[proto].keys())
        ports.sort()
        for port in ports:
            port_obj = host[proto][port]
            if port == data.port and port_obj['name'] == 'http':
                return True
            else:
                pass
    return False



"""
chain of options:

if there is no url:
1. default port: 80
1.1. port 80 not found


"""
if __name__ == '__main__':
    try:
        data = Data.Data(address="192.168.56.102", username="admin", password="admin", max_pages=30)
        nm_scan = scan(data=data)
        if check_for_http(nm_scan, data):
            print("HTTP Port exists!")
        else:
            print("HTTP port specified doesn't exist!")
    except Exception as e:
        print(e)