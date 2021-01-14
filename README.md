# PWEB
A pentesting tool for Web Servers
```
This is a tool for pentesting web security flaws in sites and web servers.
Instructions:
later ;)
```

# **CREATED BY RAZ KISSOS AND DROR WEISS**

# Usage
| flag  |  description  |  foramt |  usage  | 
|:-----:|:--------------|:--------|:--------|
| -i | Specify an `ip address` to be scanned for http ports.| python MainCore.py -i \<ip address\> | python MainCore.py -i 192.168.52.101 |
| -p | Specify a `port` on which a http web server is hosted. <br/> If no port is specified with ip or url, default port 80 will be selected.| python MainCore.py -i \<ip address\> -p \<port\> | python MainCore.py -i 192.168.52.101 -p 8888 | 
| -P | Specify an `all port scan` which in return will allow the user to <br/>see which http ports are available and pick one to be scanned. | python MainCore.py -i <ip_address> -P | python MainCore.py -i 192.168.52.101 -P | 
| -u | Specify a `url address` to be scanned instead of an <br/>ip address (if you specify both, the url will be dominant).<br/>The url protocol must be http and can contain a port specifier within it | python MainCore.py -u \<url\> | python MainCore.py -u "http://mylocalwebsite.com"<br/>python MainCore.py -u "http://192.168.52.101:8888"|
| -L | Specify a `username and password` to be used<br/>in any login form on the site.<br/>This could be useful when the tool might need to scan pages that require a logged in session. | python MainCore.py -u \<url\> -L \<username\> \<password\> | python MainCore.py -u "http://192.168.52.101:8888" -L "admin" "password" |
| -n | `Limit the amount of pages` the tool harvests. The tool will <br/> stop harvesting when it reaches the limit or when it cannot <br/> find more accessible pages recursively. | python MainCore.py -u \<url\> -n \<max amount\> | python MainCore.py -i 192.168.52.101 -n 3 |
| -R | Specify if the scan will be `recursive` or not, if not selected the scan <br/> will find all accessible pages from within the first page specified and<br/> then stops. (This may cause the run to take a lot of time <br/>depending on the size of your website). | python MainCore.py -u \<url address\> -R | python MainCore.py -u "http://192.168.52.101" -R |
| -v | `Verbose flag`, if specified the tool will not display it's banner and startup information. |  python MainCore.py -u \<url address\> -v |  python MainCore.py -u "http://192.168.52.101" -v|
| -b | Specify if blacklist should be used to prevent specific <br/> pages from being scanned (blacklist type must be `.txt`). | python MainCore.py -i \<ip address\> -b \<blacklist path\> | python MainCore.py -i 192.168.52.101 -b ./myblacklist.txt |
| -o | Specify an `xml output file` to which the data from the scan will <br/>be dumped to in xml format. if file does not exist the tool will create <br/>it and if the file already exists the tool will override the data in the file. | python MainCore.py -i \<ip address\> -o \<output file path\> | python MainCore.py -i 192.168.52.101 -o ./pweb_output.xml |
| -A | The user agrees to allow the tool to use potentially agressive <br/> functions to recognize breaches in security. (some functions<br/> may not work without this being activated). | python MainCore.py -i \<ip address\> -A | python MainCore.py -i 192.168.52.101 -A |
