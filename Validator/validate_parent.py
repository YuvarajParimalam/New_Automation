import re
import os
import sys
from fuzzywuzzy import fuzz
from cleanco import cleanco
from bs4 import BeautifulSoup
import requests
import random
import pandas as pd
from ALF.DB_processor import database
import configparser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from random import randint
from bs4 import BeautifulSoup
import pickle
import codecs
from time import sleep
import math
import random
import configparser
from tabulate import tabulate

from ALF.Lib_funtions.library import (
    clean_telephone,
    get_search_results_site,
    get_google_address,
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
config = configparser.RawConfigParser()
configPath = 'configuration.ini'
fileDirectory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fileDirectory = os.path.join(fileDirectory,"configuration.ini")
config.read(fileDirectory)
proxy = config.get("Proxy", "proxy")
print(proxy)
proxies = {"http": proxy, "https": proxy}


def validate_other_details(companyName, address1, website, directory):

    ''' To Validate thether details'''
    searchUrl = form_google_query(
        companyName,
        address1,
        directory=config.get(directory, "location"),
        quoted=get_domain(website),
    )
    response = get_search_results(searchUrl)
    if response is not None:
        referenceUrl, desc = response
        pageSource = ""
        data = dict()
        if referenceUrl is not None and config.get(directory, "location") in referenceUrl:
          
            try:
                pageSource = browser.get(referenceUrl)
            except:
                print("error occured when requesting page {}".format(referenceUrl))
                pass
            
            if pageSource:
                if directory == "Endole":
                    find_site = re.findall(website,str(pageSource))
                    if find_site:
                        data = get_directory_details(pageSource, directory=directory)
                    
                else:
                    data = get_directory_details(pageSource, directory=directory)
                if data:
                     data["referenceUrl"] = referenceUrl
                return data
            
    return {}


def get_parent_company_from_google(companyName):

    '''Fetch the parent company form google'''
	
    cleanedCompanyName = cleanco(companyName).clean_name()
    referenceUrl = form_google_query(cleanedCompanyName + ' Parent Company')
    #pageSource = browser.get(referenceUrl)
    response = google_get(referenceUrl)
    pageSource = response.text
    sel = Selector(text = pageSource)
    
    scrapedParentCompany = ""
    if sel.xpath('//div[contains(@class,"title")]/text()'):
        scrapedParentCompany = ', '.join(sel.xpath('//div[contains(@class,"title")]/text()').extract())
    else:
        scrapedParentCompany = sel.xpath('//div[contains(@class,"Z0LcW")]/a/text()').extract()
        if not scrapedParentCompany:
            scrapedParentCompany = sel.xpath('//div[contains(@class,"Z0LcW")]/text()').extract()
        if scrapedParentCompany:
            scrapedParentCompany = scrapedParentCompany[0]
        else:
            scrapedParentCompany = ""

    return scrapedParentCompany,referenceUrl   
    



def validate_parent_emp(companyName, address1, immediateParent, ultimateParent, employeeCount, website,linkedinUrl):

    ''' Validate the immediateParent and ultimateParent'''
    global   scrapedImmediateParent,scrapedUltimateParent, scrapedEmployeeCount,immediateParentUrl, ultimateParentUrl, employeeCountUrl,immediateParentStatus, ultimateParentStatus, employeeCountStatus
	
    immediateParentUrl, ultimateParentUrl, employeeCountUrl = [None] * 3
    scrapedImmediateParent, scrapedUltimateParent, scrapedEmployeeCount = [None] * 3
    immediateParentStatus, ultimateParentStatus, employeeCountStatus = ["UnMatched"] * 3
	
    if immediateParent is not None:
        queryUrl = form_google_query(
            directory=get_domain(website), quoted=immediateParent
        )
        results = get_search_results(queryUrl)
        if results:
            scrapedImmediateParent = results[1]
            if (
                fuzz.ratio(
                    cleanco(immediateParent).clean_name().lower(),
                    cleanco(scrapedImmediateParent).clean_name().lower(),
                )
                >= 85
            ):
                immediateParentUrl = results[0]
                immediateParentStatus = "Matched"

    if ultimateParent is not None:
        queryUrl = form_google_query(directory=get_domain(website), quoted=ultimateParent)
        results = get_search_results(queryUrl)
		
        if results:
            scrapedUltimateParent = results[1]
            
            if (
                fuzz.ratio(
                    cleanco(ultimateParent).clean_name().lower(),
                    cleanco(scrapedUltimateParent).clean_name().lower(),
                )
                >= 85
            ):
                ultimateParentUrl = results[0]
                ultimateParentStatus = "Matched"
                
    scrapedParentCompany, scrapedParentUrl = get_parent_company_from_google(companyName)    
    if scrapedParentCompany and (ultimateParent or immediateParent):
        if (ultimateParent
            and fuzz.ratio(
                    cleanco(ultimateParent).clean_name().lower(),
                    cleanco(scrapedParentCompany).clean_name().lower(),
                ) >= 65
           ):
           ultimateParentUrl =  scrapedParentUrl
           ultimateParentStatus = "Matched"
        if (immediateParent
            and ultimateParentStatus == "UnMatched"
            and fuzz.ratio(
                    cleanco(immediateParent).clean_name().lower(),
                    cleanco(scrapedParentCompany).clean_name().lower(),
                ) >= 65
           ):
           immediateParentUrl =  scrapedParentUrl
           immediateParentStatus = "Matched"
    elif(not scrapedParentCompany):
        scrapedParentUrl = None
        
   
    username='chandrasekar.siva@meritgroup.co.uk'
    password='Qw3rty@789'
    driver = webdriver.Chrome()      
    driver.maximize_window()
    url="https://www.linkedin.com/sales/"
    if os.path.exists('linkedin_session.pkl') is True:
        cookies = pickle.load(open("linkedin_session.pkl", "rb"))
        driver.get("https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin")
        for cookie in cookies:
                driver.add_cookie(cookie)
        sleep(randint(10,15))
        
    #----------------------if session is not available------------------------------------		
    else:
        driver.get (url)
        sleep(randint(10,15))
        elementID = driver.find_element_by_id('username')
        elementID.send_keys(username)
        sleep(randint(10,15))
        elementID = driver.find_element_by_id('password')
        elementID.send_keys(password)
        elementID.submit()
        pickle.dump( driver.get_cookies() , open("linkedin_session.pkl","wb"))
        print("login with user name")
        sleep(randint(10,15))
        
    print("login with user name")
    sleep(3)
  
    try:
        employeeUrl=linkedinUrl+ '/about/'
        driver.get(employeeUrl)
        sleep(5)
        
        source= driver.page_source
        print('source',source)
        soup = BeautifulSoup(source, 'lxml')
        try:
            df=soup.find('dl',attrs={'class':'overflow-hidden'})
            print(df)
            ## Avg employees
            scrapedEmployeeCountValidated=df.find('dd',attrs={'class':'org-about-company-module__company-size-definition-text t-14 t-black--light mb1 fl'})
            scrapedEmployeeCountValidated= scrapedEmployeeCountValidated.get_text() if scrapedEmployeeCountValidated else None
            if scrapedEmployeeCountValidated is not None:
                emplo=re.findall(r'[\d^,]+',str(scrapedEmployeeCountValidated))
                length_emp=len(emplo)
                if length_emp==2:
                    for x  in emplo:
                        first=emplo[0]
                        first=first.replace(',','')
                        second=emplo[1]
                        second=second.replace(',','')
                        scrapedEmployeeCountValidated=(int(first)+int(second))//2
                        print('avg size',scrapedEmployeeCountValidated)
                        
                        
                else:
                    for x in emplo:
                        x=x.replace(',','')
                        scrapedEmployeeCountValidated=int(x)//2
                        print('avg size',scrapedEmployeeCountValidated)
                        
            ## Actual linkedin count
            scrapedEmployeeCount=df.find('dd',attrs={'class':'org-page-details__employees-on-linkedin-count t-14 t-black--light mb5'})
            scrapedEmployeeCount= scrapedEmployeeCount.get_text() if scrapedEmployeeCount else None
            print('scrapedEmployeeCount',scrapedEmployeeCount)
            
            if scrapedEmployeeCount is not None:
                emplo1=re.findall(r'[\d^,]+',str(scrapedEmployeeCount))
                x=emplo1[0]
                x=x.replace(',','')
                scrapedEmployeeCount=x
                print('lin size',scrapedEmployeeCount)
            
                    
                    
            ##  employees size in range
            employeeCountUrl=df.find('dd',attrs={'class':'org-about-company-module__company-size-definition-text t-14 t-black--light mb1 fl'})
            employeeCountUrl= employeeCountUrl.get_text() if employeeCountUrl else None
            print('e size',employeeCountUrl)
        except:
            scrapedEmployeeCount=''
            employeeCountUrl=''
            scrapedEmployeeCountValidated=''
    except:

        scrapedEmployeeCount=''
        employeeCountUrl=''
        scrapedEmployeeCountValidated=''
             
                
    driver.quit()
                
                                 
    return [
        scrapedImmediateParent,
        immediateParentUrl,
        immediateParentStatus,
        scrapedUltimateParent,
        ultimateParentUrl,
        ultimateParentStatus,
        scrapedEmployeeCount,
        employeeCountUrl,
        scrapedEmployeeCountValidated,
        scrapedParentCompany, 
        scrapedParentUrl
    ]
