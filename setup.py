#! /usr/bin/env python

import os, string, sys
from setuptools import setup

PACKAGE = "pythorizenet"

def main():
    kwargs = {
        'name'                    : "%s" % PACKAGE,
        'version'                 : "2.0",
        'description'             : "Python classes for the Authorize.net AIM and ARB APIs.",
        'author'                  : "Ben Timby",
        'author_email'            : "btimby@ftphosting.net",
        'maintainer'              : "Travis Cunningham",
        'maintainer_email'        : "tech@smartfile.com",
        'url'                     : "https://www.smartfile.com",
        'license'                 : "GPL",
        'platforms'               : "UNIX",
        'long_description'        : "AIM and ARB API interfaces for performing real-time credit card authorizations/captures as well as automated recurring billing.",
        'packages'                : ['pythorizenet'],
        'install_requires'        : ['lxml >= 1.3.4'],
    }
    setup(**kwargs)

if __name__ == "__main__":
	main()
