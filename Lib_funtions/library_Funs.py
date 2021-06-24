
import requests
import time
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import unquote
import tldextract
import pandas as pd
from urllib.parse import (
    urlparse,
    urlsplit,
    parse_qs,
    urlunsplit,
    urlencode,
    parse_qsl,
    unquote_plus
)
from urllib.parse import unquote
from selenium import webdriver
from random import choice, randint
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
import configparser
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType

config = configparser.RawConfigParser()
configPath = 'configuration.ini'
fileDirectory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fileDirectory = os.path.join(fileDirectory,"configuration.ini")
config.read(fileDirectory)
proxy = config.get("Proxy", "proxy")
print(proxy)
proxies = {"http": proxy, "https": proxy}


class Url(object):
    """A url object that can be compared with other url orbjects
    without regard to the vagaries of encoding, escaping, and ordering
    of parameters in query strings."""

    def __init__(self, url):
        parts = urlparse(url)
        _query = frozenset(parse_qsl(parts.query))
        _path = unquote_plus(parts.path)
        parts = parts._replace(query=_query, path=_path)
        self.parts = parts

    def __eq__(self, other):
        return self.parts.path in other.parts.path or other.parts.path in self.parts.path

    def __hash__(self):
        return hash(self.parts)


def clean_telephone(telephone):
    if telephone:
        telephone = (
            telephone.replace(" ", "")
            .replace(".", "")
            .replace(")", "")
            .replace("(", "")
            .replace("-", "")
            .replace("+", "")
            .strip()
        )
        if re.findall(r'\d+',telephone):
           telephone = re.findall(r'\d+',telephone)[0]
        if len(telephone) == 12:
            telephone = telephone[2:]
        return telephone


def get_domain(website):
    url = urlparse(website)
    domain = url.hostname
    if domain is None:
        url = urlparse("http://" + website)
        domain = url.hostname
    domain = domain.replace("www.", "").replace("www2.", "")
    return domain.lower()


def regex(pattern, string, default=None, get_one=False):
    matches = re.findall(pattern, string)
    if matches:
        if get_one is True:
            return matches[0]
        return matches
    else:
        return default


def get_search_results_site(address, website, full_content=False):
    domain = get_domain(website)
    url = form_google_query(address, directory=domain)
    response = google_get(url)
    content = response.content.decode("utf-8")
    soup = BeautifulSoup(content, "lxml")
    referenceUrl, content = None, None
    for row in soup.select("div.g"):
        referenceUrl = row.select_one(".r a")
        referenceUrl = referenceUrl["href"] if referenceUrl else None
        contents = row.select("span.st") if full_content else row.select("span.st em")
        if contents:
            contents = [content.get_text() for content in contents]
        content = ", ".join(pd.Series(contents).drop_duplicates().tolist())
        break
    return referenceUrl, content


def get_search_results(url):
    response = google_get(url)
    content = response.content.decode("utf-8")
    soup = BeautifulSoup(content, "lxml")
    #print('usop',soup)
    for row in soup.select("div.g"):
        referenceUrl = row.select_one(".rc a")
        referenceUrl = referenceUrl["href"] if referenceUrl else None
        contents = row.select("span em")
        #print('c1',contents)
        if contents:
            contents = [content.get_text() for content in contents]
        content = ", ".join(pd.Series(contents).drop_duplicates().tolist())
        print('ru',referenceUrl)
        print('c',content)
        return referenceUrl, content



def google_get(url):

    proxies = {"http": proxy, "https": proxy}

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
        "image/apng,*/*;q=0.8",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,tr;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
    }
    return requests.get(url, headers=headers,proxies=proxies)

def get_google_telephone(query,gmap,tel_no,cn):
    global telephone, url
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,tr;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://safer.fmcsa.dot.gov",
        "pragma": "no-cache",
        "referer": "https://safer.fmcsa.dot.gov/CompanySnapshot.aspx",
        "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
        }
    proxies = {"http": proxy, "https": proxy}

    company_name=cn
    tel_no=tel_no
    print('tel_no',tel_no)
    if tel_no is None:
        telephone=''
        url=''
    else:
        
        tel_url=form_google_tel_query(company_name,tel_no)
        req = requests.get(tel_url,headers=headers,proxies=proxies)
        rep=req.text
        soup = BeautifulSoup(req.text,'lxml')
        no_results=soup.find_all('div',attrs={'class':'s card-section rQUFld'})
        if no_results==[]:
            print('MATCH')
            try:
                link=re.findall(r'class="yuRUbf"><a href="(.*?)"',str(rep))
                for li in link:
                    req1 = requests.get(li,headers=headers,proxies=proxies)
                    rep1=req1.text
                    soup1 = BeautifulSoup(req1.text,'lxml')
                    fullstring = str(soup1)
                    substring = str(tel_no)
                    if substring in fullstring:
                        f='FOUND'
                        telephone=str(tel_no)
                        url=li
                        break
                        
                    else:
                        f='NOT FOUND'
                        telephone=''
                        url=''
                    
            except:
                telephone=''
                url=''
                
        else:
            telephone=''
            url=''
    return telephone, url

def get_google_address(query,gmap,tel_no):
    headers = {


                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
                                  "image/apng,*/*;q=0.8",
                        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,tr;q=0.7",
                        "cache-control": "no-cache",
                        "pragma": "no-cache",
                        "upgrade-insecure-requests": "1",
                        "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 "
                                      "(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
                    }
    proxies = {"http": proxy, "https": proxy}
    url = form_google_query(query)
    g_url=gmap
    search_url=url
    response = google_get(url)
    content = response.content.decode("utf-8")
    soup = BeautifulSoup(content, "lxml")
    address = soup.select_one('[data-attrid="kc:/location/location:address"] span.aCOpRe')
    address = address.get_text() if address else None
    if address is None:
        address=soup.find('div',attrs={'class':'MWXBS'})
        if  address is not None:
            address=address.text
    
        else:
            address=soup.find('span',attrs={'class':'LrzXr'})
            if  address is not None:
                address=address.text
            elif address is None:
                address=soup.find('span',attrs={'class':'hgKElc'})
                if  address is not None:
                    address=address.text
                
                elif address is None:
                
                    queryString=g_url
                    url = "https://www.google.com/maps/search/?api=1&query=" + str (query)
                    RegexList = []
                    
                    response = requests.get (url, headers=headers,proxies=proxies )
                    responseContent = response.content.decode ('utf-8', errors='ignore')
                    addressRegex=r'google.com\/maps\/preview\/place\/([^>]*?)\/@'
                    addressBlock   = re.findall(addressRegex,responseContent,re.I)
                    if len(addressBlock)>=1:

                            address= unquote(addressBlock[0].replace("+"," "), encoding='utf-8', errors='ignore')
                            

                    else:
                        address=''
                        url=search_url
                        response = requests.get (url, headers=headers,proxies=proxies)
                        soup = BeautifulSoup(response.text,'lxml')
                        try:

                            df=soup.find('span',attrs={'class':'aCOpRe'})
                            for sd in df:
                                address=sd.text
                        except:
                            address=''

                        
    return address, url

def get_directory_details(pageSource, directory):
    data = dict()
    parentRegex = config.get(directory, "parentRegex", fallback=None)
    employeeRegex = config.get(directory, "employeeRegex", fallback=None)
    if parentRegex:
        ultimateParentCompany = regex(parentRegex, pageSource, default=None, get_one=True)
        data["ultimateParentCompany"] = ultimateParentCompany
    if employeeRegex:
        employeeCount = regex(employeeRegex, pageSource, default=None, get_one=True)
        if employeeCount:
            data["employeeCount"] = employeeCount.replace(",", "").replace(" ", "")
    return data


def form_google_query(*args, **kwargs):
    query = []
    quoted = kwargs.get("quoted")
    directory = kwargs.get("directory")
    if directory is not None:
        query.append("site:{}".format(get_domain(directory)))
    if quoted is not None:
        query.append('"{}"'.format(quoted))
    query = query + [field.strip() for field in args if field is not None]
    query = ", ".join(query)
    url = "https://www.google.co.uk/search?q=&ie=UTF-8"
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    query_params["q"] = [query]
    new_query_string = urlencode(query_params, doseq=True)
    url = urlunsplit((scheme, netloc, path, new_query_string, fragment))
    return url

def form_google_tel_query(*args, **kwargs):
    query = []
    quoted = kwargs.get("quoted")
    directory = kwargs.get("directory")
    if directory is not None:
        query.append("site:{}".format(get_domain(directory)))
    if quoted is not None:
        query.append('"{}"'.format(quoted))
    query = query + [field.strip() for field in args if field is not None]
    query = ", ".join(query)
    url = "https://www.google.com/search?q="
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)
    query_params["q"] = [query]
    new_query_string = urlencode(query_params, doseq=True)
    url = urlunsplit((scheme, netloc, path, new_query_string, fragment))
    return url


def get_social_accounts(website,companyName):
    headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,tr;q=0.7",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://safer.fmcsa.dot.gov",
    "pragma": "no-cache",
    "referer": "https://safer.fmcsa.dot.gov/CompanySnapshot.aspx",
    "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
}
    socialAccounts = {"twitter": [], "facebook": [], "linkedin": []}
    website = website.strip()
    print('website1;',website)

    if len(website) > 4 and website[0:4] != "http":
        website = "http://" + website

    try:
        response = requests.get(website, headers=headers,proxies=proxies)
        content = response.content
        print('content',content)
        status_code=response.status_code
        print('status_code',status_code)
        
    
    
    except Exception as e:
        content = str(e)

    soup = BeautifulSoup(content, "html5lib")

    links = soup.find_all("a", href=True)
    smSites = ["twitter", "facebook", "linkedin"]
    for smSite in smSites:
        accounts = []
        if smSite=="linkedin" :
            urll="https://www.google.com/search?api=1&query=" +str(companyName)+ ' '+ 'linkedin'
            print(urll)
            
            req = requests.get(urll,headers=headers,proxies=proxies)
            soup1 = BeautifulSoup(req.text,'lxml')
            #print(soup1)
            rep=req.text
            #print(rep)
    
            df=soup1.find('div',attrs={'class':'yuRUbf'})
            #print(df)
            if df is not None:
                link=df.find('a').get('href')
                accounts.append(link)
                print('gh',accounts)

        if smSite=="twitter" :
            urll="https://www.google.com/search?api=1&query=" +str(companyName)+ ' '+ 'twitter'
            print(urll)
            
            req = requests.get(urll,headers=headers,proxies=proxies)
            soup1 = BeautifulSoup(req.text,'lxml')
            rep=req.text
            df=soup1.find('div',attrs={'class':'yuRUbf'})
            if df is not None:
                link=df.find('a').get('href')
                accounts.append(link)
                print('gh',accounts)

        if smSite=="facebook" :
            urll="https://www.google.com/search?api=1&query=" +str(companyName)+ ' '+ 'facebook'
            print(urll)
            
            req = requests.get(urll,headers=headers,proxies=proxies)
            soup1 = BeautifulSoup(req.text,'lxml')
            rep=req.text
            df=soup1.find('div',attrs={'class':'yuRUbf'})
           
            if df is not None:
                link=df.find('a').get('href')
                accounts.append(link)
               
        if accounts:
            socialAccounts[smSite] = list(set(accounts))
            print('social',socialAccounts)
           
    return socialAccounts


class Driver:
    browser = "chrome"

    def __enter__(self):
        self.resetCount = randint(1, 3)
        self.currentCount = 0
        self.driver = self.initialize_driver(self.browser)
        return self

    def initialize_driver(self, browser):
        if browser == "chrome":
            options = Options()
            #options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("start-maximized")
            options.add_argument("disable-infobars")
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_experimental_option(
                "excludeSwitches", ["ignore-certificate-errors"]
            )
            proxy = choice(["172.27.140.48:3128", "172.27.140.48:3128"])
            prox = Proxy()
            prox.proxy_type = ProxyType.MANUAL
            prox.http_proxy = proxy
            prox.ssl_proxy = proxy
            capabilities = webdriver.DesiredCapabilities.CHROME
            prox.add_to_capabilities(capabilities)
            driver = webdriver.Chrome(
                chrome_options=options,
                desired_capabilities=capabilities,
                service_log_path="NULL",
            )
        else:

            
            binary = (r'C:\Program Files\Mozilla Firefox\firefox.exe')
            options = Options()
            PROXY = "172.27.140.48:3128"
            options.add_argument("--headless")
            #options.set_headless(headless=True)
            options.binary = binary
			
			
            PROXY = "172.27.140.48:3128"
            desired_capability = webdriver.DesiredCapabilities.FIREFOX
            desired_capability["proxy"] = {
				"proxyType": "manual",
				"httpProxy": PROXY,
				"ftpProxy": PROXY,
				"sslProxy": PROXY,
			}
            firefox_profile = webdriver.FirefoxProfile()
            firefox_profile.set_preference("browser.privatebrowsing.autostart", True)
            driver = webdriver.Firefox(firefox_profile=firefox_profile, firefox_binary=binary,firefox_options=options,capabilities=desired_capability)
            return driver

    def reset(self):
        self.quit()
        self.driver = self.initialize_driver(self.browser)
        self.resetCount = randint(1, 3)
        self.currentCount = 0

    def get(self, url):
        if self.currentCount >= self.resetCount:
            self.reset()
        self.driver.get(url)
        self.currentCount += 1
        time.sleep(randint(1, 3))
        return self.driver.page_source

    def quit(self):
        self.driver.quit()



    def __exit__(self, type, value, traceback):
        self.quit()
