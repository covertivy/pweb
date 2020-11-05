#!/usr/bin/python3
import nmap
import Data
from colors import COLOR_MANAGER
import urllib.parse


def url_port(url: str, existing_port: int):
    try:
        token = urllib.parse.urlparse(url)
        port = token.port
    except ValueError as e:
        COLOR_MANAGER.print_error(f"{e}, using port {existing_port}.")
        return existing_port
    if not port:
        return existing_port
    return port


def validIPAddress(ip: str) -> bool:
    """
      :type IP: str
      :rtype: str
      """

    def isIPv4(s):
        try:
            return str(int(s)) == s and 0 <= int(s) <= 255
        except:
            return False

    if ip.count(".") == 3 and all(isIPv4(i) for i in ip.split(".")):
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


def scan_ports(data: Data.Data) -> nmap.PortScanner:
    nm = nmap.PortScanner()  # instantiate nmap.PortScanner object
    nm.scan(hosts=data.ip, ports=str(data.port))  # scan host, ports from 22 to 443

    if len(nm.all_hosts()) == 0:
        raise Exception(f"No hosts found on {data.ip}")

    host = nm[nm.all_hosts()[0]]  # usually there is one host in the list, the one we want to check

    if type(data.port) is not int:
        # if the user used -P for all ports scan
        message = str()
        for proto in host.all_protocols():
            # for every protocol that the host is using
            ports = list(host[proto].keys())
            ports.sort()

            for port in ports:
                if host[proto][port]['name'] == "http":
                    # we are looking for http ports only
                    message += f"\tPort: {port} | State: {host[proto][port]['state']} " \
                                f"| Service: {nm[host][proto][port]['product']}\n"
        if len(message) != 0:
            # if there are open http ports on the host
            message = COLOR_MANAGER.UNDERLINE + \
                      "List of the open http ports on your host:\n\n" \
                      + COLOR_MANAGER.ENDC + COLOR_MANAGER.CYAN + message + COLOR_MANAGER.ENDC + \
                      "\nPlease choose one of the ports above and try again (-p <port>).\n"
            print(message)
        else:
            # if there are no open http ports on the host
            raise Exception("There are no open http ports on your host, please check the host.")
    else:
        # if the user used -p or used the default port 80
        exists = False
        proto_list = host.all_protocols()
        for proto in proto_list:
            ports = list(host[proto].keys())  # Get all port numbers as a list.
            for port in ports:
                port_obj = host[proto][port]  # Get the port object.
                if port == data.port and port_obj['name'] == 'http':
                    exists = True
                    break
        if exists:
            data.url = f"http://{data.ip}:{data.port}"
        else:
            raise Exception(f"port {data.port} isn't open on your host. please try another port or check your host.")
    return nm


def set_target(data: Data.Data):
    if validIPAddress(data.ip):
        scan_ports(data)
    else:
        COLOR_MANAGER.print_error("Invalid IP address")
