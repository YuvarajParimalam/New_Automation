
# -*- coding: utf-8 -*-import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import re
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
from bs4 import BeautifulSoup
import pickle
import codecs
from time import sleep
import math
import random
import configparser
from tabulate import tabulate
import configparser
from scrapy import Selector
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
from urllib.parse import unquote
import time
from ALF.Validator import validate_parent
from ALF.Validator import Validate_socialaccounts
#from ALF.Validator import company_validator
from ALF.Validator import Telephone_validator


browser = Driver()
browser.browser = "firefox"
config = configparser.RawConfigParser()
configPath = 'configuration.ini'
fileDirectory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fileDirectory = os.path.join(fileDirectory,"configuration.ini")
config.read(fileDirectory)
proxy = config.get("Proxy", "proxy")
proxies = {"http": proxy, "https": proxy}


template = pd.DataFrame(
	columns=[
		'record_id','company_name','address1','address2','address3','address4','address5','postcode','website','telephone','scrapedAddress','referenceUrl','addressValidation','scrapedTelephone','telUrl','telValidation','immediateParent','scrapedImmediateParent','immediateParentUrl','immediateParentStatus','scrapedUltimateParent','ultimateParentUrl','ultimateParentStatus','employeeCount','scrapedEmployeeCount','employeeCountUrl','scrapedTwitterHandle','twitterStatus','scrapedFacebookLink','facebookStatus','scrapedLinkedinLink','linkedinStatus','companyUrl','companyMatch'])


def company_clean(name):
    if name is None:
        return None
    invalids = [
        "THE",
        "UK",
        "U.K",
        "INTERNATIONAL",
        "BRANCH",
        "PUBLIC",
        "LIMITED",
        "COMPANY",
        ",",
    ]
    for invalid in invalids:
        name = re.sub(r"\b\s*{}\s*\b".format(invalid), " ", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name)
    return name


def validate_company(sourceName):
    global companyName, companyUrl, companyMatch
    if "(REFUSED TO BE LISTED)" in sourceName:
        sourceName = sourceName.replace("(REFUSED TO BE LISTED)", "").strip()
        

    companyName, companyUrl, companyMatch = None, None, "UnMatched"
    payload = {"q": sourceName}
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image"
        "/apng,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,tr;q=0.7",
        "cache-control": "max-age=0",
        "referer": "https://beta.companieshouse.gov.uk/search",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML"
        ", like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    }

    a=payload['q']
    
    ce=browser.get("https://beta.companieshouse.gov.uk/search" + "?q=" + a)
    #print('content',content)
    #status_code=response.status_code
    #print('status_code',status_code)
    
    a1 = str(ce)
    soup = BeautifulSoup(a1, 'html.parser')
    

    block = soup.select_one(".results-list li")
    
    
    if block:
        companyUrl = block.select_one("h3 a")
        companyUrl = companyUrl.get("href") if companyUrl else None
        if companyUrl is not None:
            companyUrl = "https://beta.companieshouse.gov.uk" + companyUrl

        companyName = block.select_one("h3")
        companyName = companyName.get_text().strip() if companyName else None
        

        previousCompanyName = block.select_one(".inset span")
        previousCompanyName = (
            previousCompanyName.get_text().strip() if previousCompanyName else None
        )

        for tag in block.select("p.meta.crumbtrail"):
            tag.decompose()

        address = block.select_one("p")
        address = address.get_text().strip() if address else None
        

        cleanedCompanyName = (
            re.sub(r"[^a-zA-Z0-9\s]", "", company_clean(companyName))
            if companyName
            else None
        )
        cleanedSourceName = re.sub(r"[^a-zA-Z0-9\s]", "", company_clean(sourceName))
        cleanedPreviousCompanyName = (
            re.sub(r"[^a-zA-Z0-9\s]", "", company_clean(previousCompanyName))
            if previousCompanyName
            else None
        )
        previousScore, currentScore = 0, 0
        if previousCompanyName is not None:
            previousScore = fuzz.ratio(
                cleanco(sourceName).clean_name().lower(),
                cleanco(previousCompanyName).clean_name().lower(),
            )
        if companyName is not None:
            currentScore = fuzz.ratio(
                cleanco(sourceName).clean_name().lower(),
                cleanco(companyName).clean_name().lower(),
            )
        if previousScore < 95 and currentScore < 95:
            if cleanedPreviousCompanyName is not None:
                previousScore = fuzz.ratio(
                    cleanco(cleanedSourceName).clean_name().lower(),
                    cleanco(cleanedPreviousCompanyName).clean_name().lower(),
                )
            if cleanedCompanyName is not None:
                currentScore = fuzz.ratio(
                    cleanco(cleanedSourceName).clean_name().lower(),
                    cleanco(cleanedCompanyName).clean_name().lower(),
                )

        if currentScore >= 95 or previousScore >= 95:
            companyMatch = "Matched"
    return [companyName, companyUrl, companyMatch]




def get_details_from_endole(website, companyName):
    #searchUrl = form_google_query(website, directory=config.get("Endole", "location"))
    data = dict()
    companyName = company_clean(companyName)
    referenceUrl = ('https://suite.endole.co.uk/insight/search/?q=' 
                    +cleanco(str(companyName)).clean_name())
    pageSource = browser.get(referenceUrl)
    sel = Selector(text = str(pageSource))
    contents = sel.xpath('//*[@class="sr-content"]')
    for content in contents:
        contentText  = content.extract()
        if contentText:
            match = re.findall(website,contentText)
            if not match:
                cName = content.xpath('./div/a/text()').extract()
                if cName:
                    cName = cName[0]
                    if (companyName 
                        and fuzz.ratio(cName.lower(),companyName.lower()) >= 90):
                        match = True
            if match:
                link = content.xpath('./div/a/@href').extract()
                if link:
                  referenceUrl = 'https://suite.endole.co.uk/' + link[0]
                  pageSource = browser.get(referenceUrl)
                  sel = Selector(text = pageSource)
                  links = sel.xpath('//a[@class="social"]')
                  for link in links:
                        smSite = link.xpath('./@title').extract()
                        if smSite:
                            smSite = smSite[0].lower()
                        siteLink = link.xpath('./@href').extract()
                        if siteLink:
                            siteLink = siteLink[0].lower()
                        if smSite and siteLink:
                            data[smSite] = siteLink   
                  address = content.xpath('./div/span/text()').extract()
                  if address:
                    data['address'] = address[0]
                    data['referenceUrl'] = referenceUrl
                    return data
                        
    return {}

def get_parent_company_from_google(companyName):
    cleanedCompanyName = cleanco(str(companyName)).clean_name()
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
    



def validate_telephone(website, companyName, telephone, postcode,adds,address5):
    validated, referenceUrl1, content, scrapedTelephone = False, None, None, False
    if re.findall(r"\d+", telephone):
        telephone = telephone.strip()
        #telephone = telephone[1:] if telephone[0] == "0" else telephone
        url = form_google_query(telephone, directory=website)
        response = google_get(url)
        try:
            response = google_get(url)
        except (http.client.IncompleteRead) as e:
            response = e.partial
        except (requests.exceptions.ChunkedEncodingError, requests.ConnectionError,urllib3.exceptions.ProtocolError) as e:
            print('connection error')
    
        except Exception as result:
            print("Unkonw error" + str(result))
            return
        except (requests.exceptions.SSLError)as ssl_error:
            print('bad handshake')
            

        responseContent = response.content.decode("utf-8")
        soup = BeautifulSoup(responseContent, "lxml")
        
        
        telephone_list = []
        for row in soup.select("div.g"):
            url = row.select_one(".r a")
            url = url.get("href") if url else None
            content = row.select_one("span.st")
            
            content = content.get_text() if content else None
            scrapedTelephones = re.findall(
                r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]", str(content)
            )
             
            
            if scrapedTelephones:
                telephone_list = telephone_list + [
                    [scrapedTelephone, url] for scrapedTelephone in scrapedTelephones
                ]
        for scrapedTelephone, referenceUrl1 in telephone_list:
            if re.findall(
                str(clean_telephone(telephone)), str(clean_telephone(scrapedTelephone))
            ):
                validated = True
                break
    if validated is False:
         scrapedTelephone, referenceUrl1 = get_google_address1(
         "{} {} ".format(cleanco(str(companyName)).clean_name(),adds,postcode),"{} {} ".format(cleanco(str(companyName)).clean_name(),str(address5),postcode),
         str(telephone),str(companyName)
        )
         if re.findall(
            str(clean_telephone(telephone)), str(clean_telephone(scrapedTelephone))
        ):
            validated = True

    referenceUrl1 = None if validated is False else referenceUrl1
    scrapedTelephone = telephone if validated else scrapedTelephone
    return clean_telephone(scrapedTelephone), validated, referenceUrl1


def validate_other_details(companyName, address1, website, directory):
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
#            if directory == "Endole":
#                response = google_get(referenceUrl)
#                pageSource = response.text
#            else:
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



def start_processing(id,Inputfile,Outputfile,type):

	if type == 'File':
		
		data=[]
		dataPoints={}
		Input_data= pd.read_excel (Inputfile)
		dataSet = pd.DataFrame(Input_data)
		
		''' Fetching input datas from file'''
		
		for i,row in dataSet.iterrows():
		
			recordID=row[0]
			companyID=row[1]
			companyName=row[2]
			address1=row[3]
			address2=row[4]
			address3=row[5]
			address4=row[6]
			address5=row[7]
			postcode =row[8]
			website=row[12]
			telephone=row[9]
			immediateParent=row[10]
			ultimateParent=row[11]
			employeeCount=row[13]
			twitterUrl=row[14]
			linkedinUrl=row[15]
			facebookUrl=row[16]
			
			'''validate parent'''
			
			parentEmpValidation = validate_parent.validate_parent_emp(companyName, address1, immediateParent, ultimateParent, employeeCount, website)
			scrapedImmediateParent = parentEmpValidation [0]
			immediateParentUrl = parentEmpValidation [1]
			immediateParentStatus = parentEmpValidation [2]
			scrapedUltimateParent = parentEmpValidation [3]
			ultimateParentUrl = parentEmpValidation [4]
			ultimateParentStatus = parentEmpValidation [5]
			scrapedEmployeeCount = parentEmpValidation [5]
			employeeCountUrl = parentEmpValidation [6]
			scrapedParentCompany = parentEmpValidation [8]
			scrapedParentUrl = parentEmpValidation [9]
##			
			'''socialValidation'''
			
			socialValidation = Validate_socialaccounts.validate_social_accounts(website, twitterUrl, facebookUrl, linkedinUrl, companyName)

			time.sleep(5)

			
			''' parent Validation'''
		
			parentEmpValidation = validate_parent.validate_parent_emp(companyName, address1, immediateParent, ultimateParent, employeeCount, website,linkedinUrl)
			time.sleep(5)

			''' Company Validation'''
			companyValidation = validate_company(companyName)
			time.sleep(5)

			''' addresss Validation'''
			address = [address1, address2, address3, address4, address5, postcode]
			address = [str(item).strip() for item in address if item is not None]
			address = ", ".join(address)
			adds=str(address1)+ ' ' +  str(address2) +' ' + str( address3 )+' ' +  str(address4 )+' ' + str(address5 )+' ' + str( postcode)
			

			referenceUrl, scrapedAddress = get_search_results_site(address, website)
			fRatio = fuzz.ratio(str(address).lower(), str(scrapedAddress).lower())
			addressValidation = (
				False
				if (str(referenceUrl).strip() == "" and str(scrapedAddress).strip() == "")
				or fRatio <= 40
				else True
			)

			if not addressValidation:
				scrapedAddress, referenceUrl = get_google_address(
				 "{} {} ".format(cleanco(companyName).clean_name(),adds,postcode), "{} {} ".format(cleanco(companyName).clean_name(),str(address5),postcode),"{} {} ".format(cleanco(companyName).clean_name(),telephone)
				)
				fRatio = fuzz.ratio(str(address).lower(), str(scrapedAddress).lower())
				addressValidation = (
					False
					if (str(referenceUrl).strip() == "" and str(scrapedAddress).strip() == "")
					or fRatio <= 40
					else True
				)
				
			(scrapedTwitterHandle,twitterStatus,scrapedFacebookLink,
			 facebookStatus,scrapedLinkedinLink,linkedinStatus) = socialValidation
			addressValidation = "Matched" if addressValidation else "UnMatched"
			time.sleep(5)
		
			'''Telephone validation''' 
			if telephone:
				scrapedTelephone, telValidation, telUrl =validate_telephone(website, companyName, telephone, postcode,adds,address5)
			else:
				scrapedTelephone, telValidation, telUrl = None, False, None
			#scrapedTelephone, telValidation, telUrl = None, False, None	

			telValidation = "Matched" if telValidation else "UnMatched"
			


			dataPoints={}
			dataPoints['record_id'] = recordID
			dataPoints['comp_id'] = companyID
			dataPoints['company_name'] = companyName
			dataPoints['address1'] = address1
			dataPoints['address1'] = address2
			dataPoints['address3'] = address3
			dataPoints['address4'] = address4
			dataPoints['address5'] = address5
			dataPoints['postcode'] = postcode
			dataPoints['website'] = website
			dataPoints['telephone'] = telephone
			dataPoints['immediateParent'] = immediateParent
			dataPoints['ultimateParent'] = ultimateParent
			dataPoints['employeeCount'] = employeeCount
			dataPoints['twitterUrl'] = twitterUrl
			dataPoints[' linkedinUrl'] =  linkedinUrl
			dataPoints['facebookUrl'] =facebookUrl
			dataPoints['scrapedTelephone']=scrapedTelephone
			dataPoints['telUrl']=telUrl
			dataPoints['telValidation']=telValidation
			dataPoints['referenceUrl']=referenceUrl
			dataPoints['addressValidation']=addressValidation
			dataPoints['scrapedAddress']=scrapedAddress
##			dataPoints['scrapedImmediateParent']=scrapedImmediateParent
##			dataPoints['immediateParentUrl']=immediateParentUrl
##			dataPoints['immediateParentStatus']=immediateParentStatus
##			dataPoints['scrapedUltimateParent']=scrapedUltimateParent
##			dataPoints['ultimateParentUrl']=ultimateParentUrl
##			dataPoints['ultimateParentStatus']= ultimateParentStatus
##			dataPoints['scrapedEmployeeCount']=scrapedEmployeeCount
##			dataPoints['employeeCountUrl']= employeeCountUrl
##			dataPoints['scrapedTwitterHandle']= scrapedTwitterHandle
##			dataPoints['twitterStatus']= twitterStatus
##			dataPoints['scrapedFacebookLink']= scrapedFacebookLink
##			dataPoints['facebookStatus']= facebookStatus
##			dataPoints['scrapedLinkedinLink']= scrapedLinkedinLink
##			dataPoints['linkedinStatus']= linkedinStatus
			#dataPoints['companyName']= companyName
##			dataPoints['companyUrl']= companyUrl
##			dataPoints['companyMatch']= companyMatch
			data.append(dataPoints)
			print('-------------------Datapoints appended ---------------------')

			
			df = pd.DataFrame(data)
			outfile = template.append(df, sort=False)	
			outfile.to_excel(Outputfile,index=False)

	else:
	
		database.update_master(id, "Validation_in_Progress")
		dataSet = database.get_source_data(id)
		
		for row in dataSet:
			sourceID, recordID, companyID, companyName, address1 = row[0:5]
			address2, address3, address4, address5, postcode = row[5:10]
			website, telephone, immediateParent, ultimateParent = row[10:14]
			employeeCount, twitterUrl, linkedinUrl, facebookUrl = row[14:18]

			database.update_source_data(recordID, "Validation_in_Progress")
			time.sleep(5)
			
			'''socialValidation'''
			
			socialValidation = Validate_socialaccounts.validate_social_accounts(website, twitterUrl, facebookUrl, linkedinUrl, companyName)

			time.sleep(5)

			
			''' parent Validation'''
		
			parentEmpValidation = validate_parent.validate_parent_emp(companyName, address1, immediateParent, ultimateParent, employeeCount, website,linkedinUrl)
			time.sleep(5)

			''' Company Validation'''
			companyValidation = validate_company(companyName)
			time.sleep(5)

			''' addresss Validation'''
			address = [address1, address2, address3, address4, address5, postcode]
			address = [str(item).strip() for item in address if item is not None]
			address = ", ".join(address)
			adds=str(address1)+ ' ' +  str(address2) +' ' + str( address3 )+' ' +  str(address4 )+' ' + str(address5 )+' ' + str( postcode)
			

			referenceUrl, scrapedAddress = get_search_results_site(address, website)
			fRatio = fuzz.ratio(str(address).lower(), str(scrapedAddress).lower())
			addressValidation = (
				False
				if (str(referenceUrl).strip() == "" and str(scrapedAddress).strip() == "")
				or fRatio <= 40
				else True
			)

			if not addressValidation:
				scrapedAddress, referenceUrl = get_google_address(
				 "{} {} ".format(cleanco(companyName).clean_name(),adds,postcode), "{} {} ".format(cleanco(companyName).clean_name(),str(address5),postcode),"{} {} ".format(cleanco(companyName).clean_name(),telephone)
				)
				fRatio = fuzz.ratio(str(address).lower(), str(scrapedAddress).lower())
				addressValidation = (
					False
					if (str(referenceUrl).strip() == "" and str(scrapedAddress).strip() == "")
					or fRatio <= 40
					else True
				)
				
			(scrapedTwitterHandle,twitterStatus,scrapedFacebookLink,
			 facebookStatus,scrapedLinkedinLink,linkedinStatus) = socialValidation
			addressValidation = "Matched" if addressValidation else "UnMatched"
			time.sleep(5)
		
			'''Telephone validation''' 
			if telephone:
				scrapedTelephone, telValidation, telUrl =validate_telephone(website, companyName, telephone, postcode,adds,address5)
			else:
				scrapedTelephone, telValidation, telUrl = None, False, None
			#scrapedTelephone, telValidation, telUrl = None, False, None	

			telValidation = "Matched" if telValidation else "UnMatched"
			

			
			database.update_validated_details(
				
				[
					sourceID,
					recordID,
					scrapedAddress,
					website,
					scrapedTelephone,
					referenceUrl,
					telUrl,
					addressValidation,
					"Matched",
					telValidation,
				]
				+ socialValidation
				+ parentEmpValidation
				+ companyValidation
			)
			database.update_source_data(recordID, "Validation_Completed")
		database.update_master(id, "Validation_Completed")



def main(Inputfile,Outputfile):

	''' File type & Database type Process '''
	
	if len(Inputfile)>0:
		type = 'File'
		id =[1,3]
		if id:
			with browser:
				start_processing(id,Inputfile,Outputfile,type)
				
	else:
		type = 'Database'
		id = database.check_master()
		if id:
			with browser:
				start_processing(id,'','',type)
			

				
