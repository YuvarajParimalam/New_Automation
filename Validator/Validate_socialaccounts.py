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



def validate_social_accounts(website, twitterHandle, facebookLink, linkedinLink, companyName):

    global scrapedTwitterHandle,twitterStatus,scrapedFacebookLink,facebookStatus,scrapedLinkedinLink,linkedinStatus
	
    scrapedSocialAccounts = get_social_accounts(website,companyName)
    twitterHandle = twitterHandle.lower().strip() if twitterHandle else None
    twitterStatus, facebookStatus, linkedinStatus = ["UnMatched"] * 3
    scrapedTwitterHandle, scrapedFacebookLink, scrapedLinkedinLink = [None] * 3
    twitterLinks = scrapedSocialAccounts.get("twitter")
    facebookLinks = scrapedSocialAccounts.get("facebook")
    linkedinLinks = scrapedSocialAccounts.get("linkedin")

    if len(twitterLinks) >= 1 and twitterHandle is not None:
        for link in twitterLinks:
            if (
                twitterHandle.replace("@", "") in link.lower()
                and twitterStatus == "UnMatched"
            ):
                twitterStatus = "Matched"
                scrapedTwitterHandle = twitterHandle
                break
    if len(twitterLinks) == 1 and twitterStatus == "UnMatched":
        scrapedTwitterHandle = (
            twitterLinks[0]
            .replace("http://", "")
            .replace("https://", "")
            .replace("www.", "")
            .replace("twitter.com/", "")
            .split("/")[0]
        )
        scrapedTwitterHandle = "@" + scrapedTwitterHandle
        twitterStatus = "Matched"


    if len(facebookLinks) >= 1 and facebookLink is not None:
        for link in facebookLinks:
            if (
                Url(facebookLink.lower()) == Url(link.lower())
                and facebookStatus == "UnMatched"
            ):
                facebookStatus = "Matched"
                scrapedFacebookLink = link
                break
    if len(facebookLinks) == 1 and facebookStatus == "UnMatched":
        scrapedFacebookLink = facebookLinks[0]
        facebookStatus = "Matched"

    if len(linkedinLinks) >= 1 and linkedinLink is not None:
        for link in linkedinLinks:
            if (
                Url(linkedinLink.lower()) == Url(link.lower())
                and linkedinStatus == "UnMatched"
            ):
                linkedinStatus = "Matched"
                scrapedLinkedinLink = link
                break
    if len(linkedinLinks) == 1 and linkedinStatus == "UnMatched":
        scrapedLinkedinLink = linkedinLinks[0]
        linkedinStatus = "Matched"

    

    if linkedinStatus == "UnMatched":
        referenceUrl, content = get_search_results_site(
            '"{}"'.format(get_domain(website)), "linkedin.com/company/", True
        )
        if content is not None and get_domain(website) in content.lower():
            scrapedLinkedinLink = referenceUrl
            linkedinStatus = "Matched"
    return [
        scrapedTwitterHandle,
        twitterStatus,
        scrapedFacebookLink,
        facebookStatus,
        scrapedLinkedinLink,
        linkedinStatus,
    ]

