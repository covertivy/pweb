import nmap
import Data


def scan(data: Data.Data):
    nm = nmap.PortScanner()  # instantiate nmap.PortScanner object
    nm.scan(hosts=data.address, ports=str(data.port))  # scan host, ports from 22 to 443
    print("Command: " + nm.command_line())  # get command line used for the scan

    if len(nm.all_hosts()) == 0:
        raise Exception("[!] Error! No hosts found!")
    
    return nm


def print_scan(nm: nmap.PortScanner):
    for host in nm.all_hosts():
        print('┌----------------------------------------------------')
        print('|Host : {} | Name: {} | State : {}\t|'.format(host, nm[host].hostname(), nm[host].state()))

        for proto in nm[host].all_protocols():
            lport = list(nm[host][proto].keys())
            lport.sort()
            
            for port in lport:
                print(nm[host][proto][port])
                print('├----------------------------------------------------')
                print('|\tPort: {} | Protocol: {}'.format(port, nm[host][proto][port]['name']))
                print(f"|\tState:   {nm[host][proto][port]['state']}")
                print(f"|\tService: {nm[host][proto][port]['product']}")
                print(f"|\tVersion: {nm[host][proto][port]['version']}")
                print(f"|\tSystem:  {nm[host][proto][port]['extrainfo']}")
                
        print('└----------------------------------------------------')


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


if __name__ == '__main__':
    data = Data.Data(address="http://192.168.56.102/dvwa/", username="admin", password="admin", max_pages=30)
    nm_scan = scan(data)
    if check_for_http(nm_scan, data):
        print("HTTP Port exists!")
    else:
        print("HTTP port specified doesn't exist!")