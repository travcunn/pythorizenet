#! /usr/bin/env python

import os, string, sys
from setuptools import setup

PACKAGE = "pythorizenet"

def main():
    kwargs = {
        'name'                    : "%s" % PACKAGE,
        'version'                 : "1.1",
        'description'             : "Python classes for the Authorize.net AIM and ARB APIs.",
        'author'                  : "Ben Timby",
        'author_email'            : "btimby@ftphosting.net",
        'maintainer'              : "Ben Timby",
        'maintainer_email'        : "btimby@ftphosting.net",
        'url'                     : "http://www.ftphosting.net/",
        'license'                 : "GPL",
        'platforms'               : "UNIX",
        'long_description'        : "AIM and ARB API interfaces for performing real-time credit card authorizations/captures as well as automated recurring billing.",
        'packages'                : ['pythorizenet'],
        'install_requires'        : ['lxml >= 1.3.4'],
    }
    setup(**kwargs)

if __name__ == "__main__":
	main()