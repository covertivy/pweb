# PWEB

<p align="center">
  <a href="https://github.com/ottomated/CrewLink">
    <img src="https://cdn.discordapp.com/attachments/742134324786102382/745359388608430221/hollow.png" alt="Logo" width="320" height="320">
  </a>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About](#about)
* [Installation](#installation)
* [Usage](#usage)
  * [Flags, Usage and Description](#flags-usage-and-description)
  * [Flag Aliases](#flag-aliases)
* [Installation](#installation-and-setup)
* [Plugins and Config](#plugins-and-config)
  * [The Config File](#the-config-file)
  * [Creating Plugins](#creating-plugins)


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
| **-P** | Specify an `all port scan` which in return will allow the user to <br/>see which http ports are available and pick one to be scanned. | python MainCore.py -i <ip_address> -P | python MainCore.py -i 192.168.52.101 -P | 
| **-u** | Specify a `url address` to be scanned instead of an <br/>ip address (if you specify both, the url will be dominant).<br/>The url protocol must be http and can contain a port <br/>specifier within it | python MainCore.py -u \<url\> | python MainCore.py -u "http://mylocalwebsite.com"<br/>python MainCore.py -u "http://192.168.52.101:8888"|
| **-L** | Specify a `username and password` to be used in any login form<br/> on the site. This could be useful when the tool might need to <br/>scan pages that require a logged in session. | python MainCore.py -u \<url\> -L \<username\> \<password\> | python MainCore.py -u "http://192.168.52.101:8888" -L "admin" "password" |
| **-n** | `Limit the amount of pages` the tool harvests. The tool will <br/> stop harvesting when it reaches the limit or when it cannot <br/> find more accessible pages recursively. | python MainCore.py -u \<url\> -n \<max amount\> | python MainCore.py -i 192.168.52.101 -n 3 |
| **-R** | Specify if the scan will be `recursive` or not, if not selected the <br/>scan will find all accessible pages from within the first page <br/>specified and then stops. (This may cause the run to take a lot <br/>of time depending on the size of your website). | python MainCore.py -u \<url address\> -R | python MainCore.py -u "http://192.168.52.101" -R |
| **-V** | `Verbose flag`, if specified the tool will not display it's banner and startup information. |  python MainCore.py -u \<url address\> -V |  python MainCore.py -u "http://192.168.52.101" -V|
| **-b** | Specify if blacklist should be used to prevent specific <br/> pages from being scanned (blacklist type must be `.txt`). | python MainCore.py -i \<ip address\> -b \<blacklist path\> | python MainCore.py -i 192.168.52.101 -b ./myblacklist.txt |
| **-w** | Specify if whitelist should be used to prevent specific <br/> pages from being scanned (whitelist type must be `.txt`). | python MainCore.py -i \<ip address\> -w \<whitelist path\> | python MainCore.py -i 192.168.52.101 -w ./mywhitelist.txt |
| **-o** | Specify an `xml output file` to which the data from the scan <br/>will be dumped to in xml format. if file does not exist the <br/>tool will create it and if the file already exists the tool will override the data in the file. | python MainCore.py -i \<ip address\> -o \<output file path\> | python MainCore.py -i 192.168.52.101 -o ./pweb_output.xml |
| **-A** | The user agrees to allow the tool to use potentially agressive <br/> functions to recognize breaches in security. (some functions<br/> may not work without this being activated). | python MainCore.py -i \<ip address\> -A | python MainCore.py -i 192.168.52.101 -A |

### Flag Aliases:
| Flag   | Aliases      |
|:------:|:-------------|
| **-P** | --all_ports  |
| **-R** | --recursive  |
| **-V** | --verbose    |
| **-b** | --blacklist  |
| **-w** | --whitelist  |
| **-A** | --aggressive |

## Installation And Setup
The pweb tool was found compatible and was tested with both `debian` and `windows` machines.  
Here is the installation guide for both:

1. First, `clone` the repository:
```sh
git clone "https://gitlab.com/sparroweiss/Kineret-206-pweb.git"
```

2. After cloning step into the main folder, Go to the `config` file and make sure the selected plugins are the plugins you wish to use.
<img src="https://cdn.discordapp.com/attachments/742134324786102382/801147487263260672/unknown.png">  

> NOTE: you can learn more about this by reading below or clicking [this link](#plugins-and-config).

3. When you have selected all you plugins you should make sure python3 is installed: [python](https://www.python.org/downloads/)

4. After installing python use the pip command and give it the `requirements.txt` file included with the repository:
```sh
python pip install -r requirements.txt
```
> NOTE: make sure you are doing this in the main folder to ensure you are specifying the correct requirements.txt file path. Please also note that in some linux distributions `python` would be replaced with `python3`, please make sure to check which one is correct for you.

5. After all required modules have been installed you can finally use the tool by typing:
```sh
python MainCore.py <flags and parameters>
```
> NOTE: we still have not implemented a whay to globalize the tool, this will be coming soon. In the meantime make sure you are using this tool from it's directory only to prevent errors. To learn about the usage and the flags [click here](#usage).

## Plugins And Config
### The Config File:
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
> You can create your own plugins if you wish. Read below for more inforamtion or [click on this link](#creating-plugins).

### Creating Plugins:
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
    data.results.append(dom_xss_results)
    data.mutex.release()
```
