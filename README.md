check_netapp
============
Check netapp is a nagios plugin written in python that aims to interact simply with the NetApp ONTAPI via its SDK.

Version
-------

0.1

Dependencies
------------

This plugin depends on a couple of python modules:
* [NetApp SDK] login required for this one
* [optparse] Although it looks like I may need to move to argparse

[NetApp SDK]:http://mysupport.netapp.com/NOW/cgi-bin/software
[optparse]: https://docs.python.org/2/library/optparse.html

Installation
------------

```sh
git clone https://github.com/champain/check_netapp.git
cp check_netapp.py /usr/lib64/nagios/plugins
chmod +x /usr/lib64/nagios/plugins/check_netapp.py
```

License
-------

MIT
