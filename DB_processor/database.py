import pyodbc
#from configparser import ConfigParser
import configparser
from socket import gethostname
from platform import system
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

hostName = gethostname()

if system() == "Windows":
    sqlDriver = "{SQL SERVER}"
if system() == "Linux":
    sqlDriver = "{ODBC Driver 17 for SQL Server}"
	
config = configparser.RawConfigParser()
configPath = 'configuration.ini'
fileDirectory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fileDirectory = os.path.join(fileDirectory,"configuration.ini")
config.read(fileDirectory)
#config = ConfigParser()
#config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), "configuration.ini"))
server = config.get("DB", "server")
database = config.get("DB", "database")
username = config.get("DB", "username")
password = config.get("DB", "password")

connectionString = "DRIVER={};SERVER={};DATABASE={};UID={};PWD={}".format(
    sqlDriver, server, database, username, password
)
dbConnection = pyodbc.connect(connectionString, autocommit=True)


def get_source_data(sourceID):
    """Retrieves records from the database
    Arguments:
        sourceID {str or int} -- source_id for retrieving records
                                 from table 'VL_Source_Details'
    """
    with dbConnection.cursor() as crsr:
        query = (
            "select Source_ID, Record_ID, Company_Id, Company_Name, Address_1, "
            "Address_2, Address_3, Address_4, Address_5, Postcode, Website, Telephone, "
            "Immediate_Parent, Ultimate_Parent, Employee_Count, Twitter_URL, Linkedin_URL"
            ", Facebook_URL, Status, Created_By, Created_Date from VL_Source_Details"
            " where Status <> 'Validation_Completed' and Source_ID = ? and Website"
            " is not null"
        )
        data = crsr.execute(query, [sourceID]).fetchall()
        return data


def update_validated_details(data):
    """inserts the scraped data to database
    Arguments:
        data {tuple or list} -- inserts the scraped records in table
                                'VL_validated_details'
    """
    if data[6] is not None and len(data[6]) > 100:
        data[6] = data[6][:100]
    if data[14] is not None and len(data[14]) > 100:
        data[14] = data[14].split("?")[0]
    print(data)
    with dbConnection.cursor() as crsr:
        query = (
            "insert into VL_validated_details (Source_ID, Record_ID, Full_Address, "
            "Website, Telephone, Full_Address_URL, Telephone_URL, Full_Address_Validated,"
            "Website_Validated, Telephone_Validated, Twitter_URL, Twitter_Validated, "
            "Facebook_URL, Facebook_Validated, Linkedin_URL, Linkedin_Validated, "
            "Immediate_Parent, Immediate_Parent_URL, Parent_Company_Validated, "
            "Ultimate_Parent, Ultimate_Parent_URL, Ultimate_Parent_Validated, "
            "Employee_Count, Employee_Count_URL, Employee_Count_validated, "
             "Parent_Company_Scraped, Parent_Company_Scraped_URL, "
            "Company, Company_Url, Company_Validated ) "
            "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        )
        crsr.execute(query, data)


def check_master():
    """To check table 'VL_master' for any new jobs
    """
    with dbConnection.cursor() as crsr:
        query = (
            "select top 1 source_id from VL_master where Status <> 'Validation_Completed'"
        )
        data = crsr.execute(query).fetchone()
        return data[0] if data else None


def update_master(sourceID, status):
    """updates status in the Master table
    Arguments:
        sourceID {int or str} -- source_id of the record from VL_master
        status {str} -- Scraping status for the particular record
    """
    with dbConnection.cursor() as crsr:
        query = "update VL_master set status = ? where Source_Id = ?"
        crsr.execute(query, [status, sourceID])


def update_source_data(RecordId, status):
    """updates status in the source_details table
    Arguments:
        RecordId {int or str} -- record_id of the record from VL_master
        status {str} -- Scraping status for the particular record
    """
    with dbConnection.cursor() as crsr:
        query = "update VL_Source_Details set status = ? where Record_Id = ?"
        crsr.execute(query, [status, RecordId])
