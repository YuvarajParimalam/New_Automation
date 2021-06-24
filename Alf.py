# -*- coding: utf-8 -*-

# DB Procesor is developed and maintained by the Merit Databot Team and the contributors. 
# Version 2 was created by Vidhya Priya V. The core maintainers are:
# Vidhya Priya V - Software Engineer
# Copyright � 2020 by the Merit Group.

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ALF.controller import Alf_main
from ALF.Validator import validate_parent
from ALF.Validator import Validate_socialaccounts
#from ALF.Validator import company_validator
#from ALF.Validator import Telephone_validator
import time
import re
import configparser
from fuzzywuzzy import fuzz
from cleanco import cleanco
from bs4 import BeautifulSoup
import requests
import pandas as pd
from ALF.DB_processor import database

from ALF.Lib_funtions.library import (
    clean_telephone,
    get_search_results_site,
    get_google_address,
    get_google_address1,
    google_get,
    form_google_query,
    get_domain,
    get_search_results,
    Driver,
    get_directory_details,
    config,
    get_social_accounts,
    Url,
)
from scrapy import Selector
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from urllib.parse import unquote





if __name__ == '__main__':

	if len(sys.argv)>1:
		inFileName = sys.argv[1]
		outFileName = sys.argv[2]
		inFilePath = os.path.join(os.getcwd(), "input_files", str(inFileName))
		outFilePath = os.path.join(os.getcwd(), "output_files", str(outFileName))
	
		print("outputFile:",outFilePath)
		Alf_main.main(inFilePath,outFilePath)
	
	else:	
		Alf_main.main('','')
		
