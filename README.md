# POOPAK | TOR Hidden Service Crawler
 [![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/ellerbrock/open-source-badges/) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![Generic badge](https://img.shields.io/badge/Tor-Hidden%20Services-green.svg)](https://torproject.org/) 
 

[![Screenshot](https://raw.githubusercontent.com/thelematic/poopak/master/screenshots.jpg)](http://twitter.com/sparkmood)


This is an experimental application for crawling, scanning and data gathering from TOR hidden services.

## Features
* Multi-level in-depth crawling using CURL
* Link extractor
* Extract Emails/BTC/ETH/XMR addresses
* Extract EXIF meta data
* Screenshot (using Splash)
* Subject detector (using Spacy)
* Port Scanner
* Extract report from a hidden service (CSV/PDF)
* Fulltext search through the directory
* Language detection
* Web application security scanning (using Arachni) - [Under Developing]
* Docker based and Web UI 

## Licence
This software is made available under the GPL v.3 license. It means if you run a modified program on a server and let other users communicate with it there, your server must also allow them to download the source code corresponding to the modified version running there.


## Dependencies 

-   Docker (tested on Docker version 18.03.1)
-   Docker Compose (tested on version 1.21.1)
-   Python 3
-   pipenv

## Install
Just run application with docker-compose:

    docker-compose up -d
and next point your browser to [localhost](http://localhost/). 


# Discontinued
 
