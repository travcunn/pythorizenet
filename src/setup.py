#! /usr/bin/env python

import os, string, sys
from distutils.core import setup

PACKAGE = "pythorizenet"

def main():
    setup(
        name                    = "%s" % PACKAGE,
        version                 = "1.0",
        description             = "Python classes for the Authorize.net AIM and ARB APIs.",
        author                  = "Ben Timby",
        author_email            = "btimby@ftphosting.net",
        maintainer              = "Ben Timby",
        maintainer_email        = "btimby@ftphosting.net",
        url                     = "http://www.ftphosting.net/",
        license                 = "GPL",
        platforms               = "UNIX",
        long_description        = "AIM and ARB API interfaces for performing real-time credit card authorizations/captures as well as automated recurring billing.",
        packages                = ['pythorizenet']
    )

if __name__ == "__main__":
	main()