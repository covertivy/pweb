# PWEB

<p align="center">
  <a href="https://gitlab.com/sparroweiss/Kineret-206-pweb">
    <img src="https://cdn.discordapp.com/attachments/742134324786102382/745359388608430221/hollow.png" alt="Logo" width="320" height="320">
  </a>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About](#about)
* [Usage](#usage)
  * [Flags, Usage and Description](#flags-usage-and-description)
  * [Flag Aliases](#flag-aliases)
  * [Whitelists and Blacklists](#whitelists-and-blacklists).
  * [Cookie Json Files](#cookies)
* [Installation](#installation-and-setup)
* [Plugins and Config](#plugins-and-config)
  * [The Config File](#the-config-file)
  * [Creating Plugins](#creating-plugins)
  * [XSS Plugin Information](#xss-information)


## About
**Created by Raz Kissos and Dror Weiss**

This is a tool for pentesting web security flaws in sites and web servers.  
The tool is a command line tool that is designed as a plugin based system, each test script  
is a plugin and so you can create you own test scripts and add them as plugins.
>**NOTE:** The website must be on your `local network` which means no more than one jump from you to your target (on the same subnet) to ensure it is used for ethical causes only.


## Usage
### Flags, Usage and Description:
| FLag  |  Description  |  Foramt |  Usage  | 
|:-----:|:--------------|:--------|:--------|
| **-i** | Specify an `ip address` to be scanned for http ports.| python MainCore.py -i \<ip address\> | python MainCore.py -i 192.168.52.101 |
| **-p** | Specify a `port` on which a http web server is hosted. <br/> If no port is specified with ip or url, default port 80 will be selected.| python MainCore.py -i \<ip address\> -p \<port\> | python MainCore.py -i 192.168.52.101 -p 8888 | 
| **-u** | Specify a `url address` to be scanned instead of an <br/>ip address (if you specify both, the url will be dominant).<br/>The url protocol must be http and can contain a port <br/>specifier within it | python MainCore.py -u \<url\> | python MainCore.py -u "http://mylocalwebsite.com"<br/>python MainCore.py -u "http://192.168.52.101:8888"|
| **-b** | Specify if blacklist should be used to prevent specific <br/> pages from being scanned (blacklist type must be `.txt`), Read more about the file format [here](#whitelists-and-blacklists). | python MainCore.py -i \<ip address\> -b \<blacklist path\> | python MainCore.py -i 192.168.52.101 -b ./myblacklist.txt |
| **-w** | Specify if whitelist should be used to prevent specific <br/> pages from being scanned (whitelist type must be `.txt`), Read more about the file format [here](#whitelists-and-blacklists). | python MainCore.py -i \<ip address\> -w \<whitelist path\> | python MainCore.py -i 192.168.52.101 -w ./mywhitelist.txt |
| **-n** | `Limit the amount of pages` the tool harvests. The tool will <br/> stop harvesting when it reaches the limit or when it cannot <br/> find more accessible pages recursively. | python MainCore.py -u \<url\> -n \<max page amount\> | python MainCore.py -i 192.168.52.101 -n 3 |
| **-o** | Specify an `output folder` to which the data from the scan <br/>will be dumped to. If the folder does not exist the <br/>tool will create it and if it already exists then the tool will override the data in the folder. | python MainCore.py -i \<ip address\> -o \<output folder path\> | python MainCore.py -i 192.168.52.101 -o ./pweb_output |
| **-c** | Specify a `cookie json file` to be added to the requests. Read more about the file format [here](#cookies). | python MainCore.py -i \<ip address\> -c \<cookie json file path\> | python MainCore.py -i 192.168.52.101 -o ./cookie.json |
| **-L** | Specify a `username and password` to be used in any login form<br/> on the site. This could be useful when the tool might need to <br/>scan pages that require a logged in session. | python MainCore.py -u \<url\> -L \<username\> \<password\> | python MainCore.py -u "http://192.168.52.101:8888" -L "admin" "password" |
| **-R** | Specify if the scan will be `recursive` or not, if not selected the <br/>scan will find all accessible pages from within the first page <br/>specified and then stops. (This may cause the run to take a lot <br/>of time depending on the size of your website). | python MainCore.py -u \<url address\> -R | python MainCore.py -u "http://192.168.52.101" -R |
| **-P** | Specify an `all port scan` which in return will allow the user to <br/>see which http ports are available and pick one to be scanned. | python MainCore.py -i <ip_address> -P | python MainCore.py -i 192.168.52.101 -P | 
| **-V** | `Verbose flag`, if specified the tool will not display it's banner and startup information. |  python MainCore.py -u \<url address\> -V |  python MainCore.py -u "http://192.168.52.101" -V|
| **-A** | The user agrees to allow the tool to use potentially agressive <br/> functions to recognize breaches in security. (some functions<br/> may not work without this being activated). | python MainCore.py -i \<ip address\> -A | python MainCore.py -i 192.168.52.101 -A |

### Flag Aliases

| Flag   | Aliases      |
|:------:|:-------------|
| **-P** | --all_ports  |
| **-R** | --recursive  |
| **-V** | --verbose    |
| **-b** | --blacklist  |
| **-w** | --whitelist  |
| **-c** | --cookies    |
| **-A** | --aggressive |

### Whitelists and Blacklists

Each whitelist and blacklist file operate in the same manner.  
Separate each value with a comma (all spaces and newlines are ignored).  
If the file is specified as a `blacklist` then any page with a domain that contains the value specified will be excluded from the search.  
If the file is specified as a `whitelist` then only the pages whose domains contain the value specified will be included in the search.

#### Example file

```txt
default, xss,
helloworld,
pwebisawsome
```

>**NOTE:** newlines and spaces do not matter and therefor the values for this example would be ['default', 'xss', 'helloworld', 'pwebisawsome'].


### Cookies

To write a cookie file you need to create a json file in the following format:  
> *Each pair of opening and closing curly brackets indicates of a different cookie.*

```json
[
  // Cookie definition and parameters:
  {
    // Mandatory parameters:
    "name": "Cookie name.",
    "value": "Cookie value.",
    // Here add additional parameters for example:
    "domain": "Page domain.",
    "path": "Page path."
  },
  // Example cookie here:
  {
    "name": "security",
    "value": "low",
    "domain": "192.168.1.123",
    "path": "/DVWA"
  }
]
```

>**NOTE:** Some websites give the user a default cookie without the user being logged in, make sure to include **all** of the cookies to avoid problems in the future. Also, note that depending on the site the cookie might be able to replace a login form and therefor allow you to test the site without logging in and only by using the cookie, test for this to make your life a lot easier.

## Installation And Setup

The pweb tool was found compatible and was tested with both `debian` and `windows` machines.  
Here is the installation guide for both:

1. First, `clone` the repository:

```sh
git clone "https://gitlab.com/sparroweiss/Kineret-206-pweb.git"
```

2. After cloning step into the main folder, Go to the `config file` (default name is `pluginconfig.ini`) and make sure the selected plugins are the plugins you wish to use.

<img src="https://media.discordapp.net/attachments/742134324786102382/825689664496861204/unknown.png">  

>**NOTE:** you can learn more about this by reading below or clicking [this link](#plugins-and-config).

3. When you have selected all you plugins you should make sure python3 is installed: [python](https://www.python.org/downloads/)

4. After installing python use the pip command and give it the `requirements.txt` file included with the repository:

```sh
python pip install -r requirements.txt
```

>**NOTE:** make sure you are doing this in the main folder to ensure you are specifying the correct requirements.txt file path. Please also note that in some linux distributions `python` would be replaced with `python3`, please make sure to check which one is correct for you.

5. After all required modules have been installed you can finally use the tool by typing:

```sh
python pweb.py <flags and parameters>
```

>**NOTE:** we still have not implemented a way to globalize the tool, this will be coming soon. In the meantime make sure you are using this tool from it's directory only to prevent errors. To learn about the usage and the flags [click here](#usage).

## Plugins And Config

### The Config File

Our tool operates on a plugin based system, each check script is a plugin that is being fetched from the `pluginconfig.ini` file.  
The config file is formatted in a very specific manner, each of the attributes can be modified in the `PluginManager.py` file (category name, paths variable name, etc...)

```ini
# Category name is defaulted to `plugins` so make sure to name it accordingly.
[plugins]
# To add or remove plugins simply add/remove the path of the desired file and
# the comma after it, the last path does not require a comma after it.

# It should look something like this:
# paths = ./plugins/domxss.py,
#         ./plugins/server_security_check.py,
#         ./plugins/sql.py
# IMPORTANT: DO NOT FORGET THE `./` in the beginning of the file path!

# Non of the plugins are mandatory!
# Make sure to align them nicely so we all have a nice day :)

# Plugin paths variable name is default `paths` so make sure to name it accordingly.
paths = <plugin paths as described in comments>

# This file is used by the `PluginManager.py` file, to make any changes you should probably go over it.
```

> **NOTE**:You can create your own plugins if you wish. Read below for more inforamtion or [click on this link](#creating-plugins).

### Creating Plugins

You can create your own plugins if you wish, each plugin follows the same principals, all of the have a `check` function which receivs a `Data` object.  

```python
import Data
from colors import COLOR_MANAGER

COLOR = COLOR_MANAGER.RED
# This is an example of a domxss plugin:

def check(data: Data.Data):
    dom_xss_results = Data.CheckResults("DOMXSS", COLOR)
    
    # Use mutexes to avoid race conditions.
    data.mutex.acquire()
    pages = data.pages # get pages of the site.
    data.mutex.release()

    #
    #   ADD RESULTS TO OUR `CheckResults` OBJECT.
    #

    # Save results to the data object.
    data.mutex.acquire()
    data.results.put(dom_xss_results)
    data.mutex.release()
```

### XSS Information

The xss check file is using different methods to determine wheter a page is vulnerable to xss or not, The most accurate yet most aggressive method is the `brute_force_alert` method. This method is using payloads and tries to inject them to the page and raise an alert with them.  

##### The Payloads File

By default the payloads file is configured to be named `xsspayloads.txt` and to be stored in the same directory as the `xss.py` script, Please make sure you do so.
The payloads are completely customizable to your liking and you can add or remove payloads as you wish. 
> **NOTE**: Fewer payloads will result in better runtimes.
The payloads file should look something like this:

```txt
<script>alert(##~##)</script>
<img src=x onerror=alert(##~##)>
<img src=x onerror=javascript:alert(##~##)>
```

The string `##~##` is a special string that will be replaced within the `xss.py` script and will contain a special random string which will serve as a form of an id of a specific alert. Make sure you place this special string in the payload inside the alert text otherwise the `xss.py` script will ignore your payload.
> **NOTE**: Each payload is separated by a newline and must contain the special character which is by default `##~##`.
