#dependencies
import sys
import sqlite3 
from bs4 import BeautifulSoup
import requests
import json

# Scrape unidentified persons data from NAMUS

# Getting list of all states from NAMUS API
states=requests.get("https://www.namus.gov/api/CaseSets/NamUs/States")
statesjson=states.json()
    
def default_unidentified(database,start=None,end=None,limit=10000):
    
    # Search headers
    headers = {
        'Origin': 'https://www.namus.gov',
        'Content-Type': 'application/json;charset=UTF-8',
        'Referer': 'https://www.namus.gov/UnidentifiedPersons/Search',
        'Connection': 'keep-alive',
    }

    # Create a jsondata set
    unidentifiedjson={}
    unidentifiedjson['people']=[]
    
    # Initiate counter to follow process
    count=0
    
    for state in statesjson[start:end]:
        
        # Printing state
        print('Pulling persons from',state['name'])
        
        data = json.dumps({"predicates":[{"field":"stateOfRecovery","operator":"IsIn","values":[state["name"]]}],"take":limit,"skip":0,"projections":["idFormatted","caseNumber","dateFound","estimatedAgeFrom","estimatedAgeTo","cityOfRecovery","countyDisplayNameOfRecovery","stateOfRecovery","sex","raceEthnicity","modifiedDateTime","namus2Number","stateDisplayNameOfRecovery"],"orderSpecifications":[{"field":"dateFound","direction":"Descending"}]})

        # Send request to get all case numbers in each state
        response = requests.post('https://www.namus.gov/api/CaseSets/NamUs/UnidentifiedPersons/Search', headers=headers, data=data)

        # Parse request
        cases = json.loads(response.content)
        casesdata = cases["results"]
        print('Total persons:',len(casesdata))

        # Looping through all the cases and append to a json dataset
        for case in casesdata:
            
            # count to follow process
            count+=1
            print('Parsing person:',count)
            
            caseid=case['namus2Number']

            # get data by id
            page=requests.get('https://www.namus.gov/api/CaseSets/NamUs/UnidentifiedPersons/Cases/'+str(caseid))

            parsecase=json.loads(page.content.decode('utf-8'))
            #print(json.dumps(parsecase,indent=4,sort_keys=True))

            unidentifiedjson['people'].append(parsecase)

    # create a static dataset - only the first time
    # initiate a database
    conn=sqlite3.connect(database)
    cur=conn.cursor()

    # creating a table for missing_ca
    cur.execute('DROP TABLE IF EXISTS namus_unidentified_ca')
    cur.execute('CREATE TABLE namus_unidentified_ca (race TEXT,sex TEXT,hair TEXT,eyes TEXT,heightfrom INT,heightto INT,weight INT,marks TEXT,currentagefrom TEXT,currentageto TEXT,img TEXT,founddesc TEXT,clothing TEXT,foundlat FLOAT,foundlon FLOAT,founddate DATE)')
    
    # cleaning up the variables to put into the sql database
    for people in unidentifiedjson['people']:
        
        info=[]

        currentagefrom=None
        currentageto=None
        if 'estimatedYearOfBirthTo' in people['subjectDescription']:
            currentageto=2021-people['subjectDescription']['estimatedYearOfBirthFrom']
            currentagefrom=2021-people['subjectDescription']['estimatedYearOfBirthTo']
        heightfrom=None
        heightto=None
        if 'heightFrom' in people['subjectDescription']:
            heightfrom=(people['subjectDescription']['heightFrom'])
        if 'heightTo' in people['subjectDescription']:
            heightto=(people['subjectDescription']['heightTo'])
        weight=None
        if 'weightFrom' in people['subjectDescription']:
            weight=people['subjectDescription']['weightFrom']
        hair=''
        eyes=''
        if 'physicalDescription' in people:
            if 'hairColor' in people['physicalDescription']:
                hair=people['physicalDescription']['hairColor']['name']
            if 'leftEyeColor' in people['physicalDescription']:
                eyes=people['physicalDescription']['leftEyeColor']['name']
        if 'subjectDescription' in people:
            if 'sex' in people['subjectDescription']:
                sex=people['subjectDescription']['sex']['name']
        marks=''
        for m in range(len(people['physicalFeatureDescriptions'])):
            if 'description' in people['physicalFeatureDescriptions'][m]:
                marks+=people['physicalFeatureDescriptions'][m]['description']+','
        img=''
        if len(people['images'])>0:
            if 'files' in people['images'][0]:
                img='https://namus.gov'+people['images'][0]['files']['thumbnail']['href']
        race=''
        for r in range(len(people['subjectDescription']['ethnicities'])):
            race+=people['subjectDescription']['ethnicities'][r]['name']+','
        if 'circumstances' in people:
            if 'circumstancesOfRecovery' in people['circumstances']:
                founddesc=people['circumstances']['circumstancesOfRecovery']
            if 'dateFound' in people['circumstances']:
                founddate=people['circumstances']['dateFound']
            if 'publicGeolocation' in people['circumstances']:
                foundlat=people['circumstances']['publicGeolocation']['coordinates']['lat']
                foundlon=people['circumstances']['publicGeolocation']['coordinates']['lon']
        clothing=''
        for c in range(len(people['clothingAndAccessoriesArticles'])):
            if 'description' in people['clothingAndAccessoriesArticles'][c]:
                clothing+=people['clothingAndAccessoriesArticles'][c]['description']+','

        info=[race,sex,hair,eyes,heightfrom,heightto,weight,marks,currentagefrom,currentageto,img,founddesc,clothing,foundlat,foundlon,founddate]
        
        cur.execute('INSERT INTO namus_unidentified_ca (race,sex,hair,eyes,heightfrom,heightto,weight,marks,currentagefrom,currentageto,img,founddesc,clothing,foundlat,foundlon,founddate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', info)

    conn.commit()

    #print dimensions
    cur.execute('SELECT * FROM namus_unidentified_ca')
    rowcount=len(cur.fetchall())
    cur.execute('PRAGMA table_info(namus_unidentified_ca)')
    colcount=len(cur.fetchall())
    print('Table dimensions:',rowcount,'x',colcount)
    
    #print the first 5 as a check
    print('Sample')
    cur.execute('SELECT * FROM namus_unidentified_ca')
    for row in cur.fetchall()[0:5]:
        print(row)

    cur.close()
    
# Scrape unidentified persons data from NAMUS

def default_missing(database,start=None,end=None,limit=10000):
    
    # Search headers
    headers = {
        'Origin': 'https://www.namus.gov',
        'Content-Type': 'application/json;charset=UTF-8',
        'Referer': 'https://www.namus.gov/MissingPersons/Search',
        'Connection': 'keep-alive',
    }

    # Create a jsondata set
    missingjson={}
    missingjson['people']=[]
    
    # initiate count
    count=0

    for state in statesjson[start:end]:
        
        # Printing state
        print('Pulling persons from',state['name'])
        
        data = json.dumps({"predicates":[{"field":"stateOfLastContact","operator":"IsIn","values":[state["name"]]}],"take":limit,"skip":0,"projections":["namus2Number"]})

        # Send request to get all case numbers in each state
        response = requests.post('https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Search', headers=headers, data=data)

        # Parse request
        cases = json.loads(response.content)
        casesdata = cases["results"]
        print('Total persons:',len(casesdata))
        
        # Looping through all the cases and append to a json dataset
        for case in casesdata:
            
            # Count to show progress
            count+=1
            print('Parsing person:',count)

            caseid=case['namus2Number']

            # get data by id
            page=requests.get('https://www.namus.gov/api/CaseSets/NamUs/MissingPersons/Cases/'+str(caseid))

            parsecase=json.loads(page.content.decode('utf-8'))
            #print(json.dumps(parsecase,indent=4,sort_keys=True))

            missingjson['people'].append(parsecase)

    # create a SQL database with cleaned info - only the first time, commented out for subsequent runs
    conn=sqlite3.connect(database)
    cur=conn.cursor()

    # creating a table for missing_ca
    cur.execute('DROP TABLE IF EXISTS namus_missing_ca')
    cur.execute('CREATE TABLE namus_missing_ca (name TEXT, race TEXT, sex TEXT, hair TEXT, eyes TEXT, height FLOAT, weight INT,marks TEXT, currentage INT, img TEXT,missingdesc TEXT, clothing TEXT, lastseenlat FLOAT, lastseenlon FLOAT, lastseendate DATE)')
    
    # clean up data for SQL database
    for people in missingjson['people']:
        
        race=''
        clothing=''
        img=''
        marks=''
        name=people['subjectIdentification']['firstName']+' '+people['subjectIdentification']['lastName']
        currentage=people['subjectIdentification']['currentMinAge']
        height=(people['subjectDescription']['heightFrom'])
        if 'weightFrom' in people['subjectDescription']:
            weight=people['subjectDescription']['weightFrom']
        if 'physicalDescription' in people:
            hair=people['physicalDescription']['hairColor']['name']
            eyes=people['physicalDescription']['leftEyeColor']['name']
        sex=people['subjectDescription']['sex']['name']
        for m in range(len(people['physicalFeatureDescriptions'])):
            if 'description' in people['physicalFeatureDescriptions'][m]:
                marks+=people['physicalFeatureDescriptions'][m]['description']+','
        if len(people['images'])>0:
            img='https://namus.gov'+people['images'][0]['files']['thumbnail']['href']
        for r in range(len(people['subjectDescription']['ethnicities'])):
            race+=people['subjectDescription']['ethnicities'][r]['name']+','
        if 'circumstances' in people:
            if 'circumstancesOfDisappearance' in people['circumstances']:
                missingdesc=people['circumstances']['circumstancesOfDisappearance']
        for c in range(len(people['clothingAndAccessoriesArticles'])):
            if 'description' in people['clothingAndAccessoriesArticles'][c]:
                clothing+=people['clothingAndAccessoriesArticles'][c]['description']+','
        if 'sighting' in people:
            if 'publicGeolocation' in people['sighting']:
                lastseenlat=people['sighting']['publicGeolocation']['coordinates']['lat']
                lastseenlon=people['sighting']['publicGeolocation']['coordinates']['lon']
            lastseendate=people['sighting']['date']
        
        info=[name,race,sex,hair,eyes,height,weight,marks,currentage,img,missingdesc,clothing,lastseenlat,lastseenlon,lastseendate]
            
        cur.execute('INSERT INTO namus_missing_ca (name,race,sex,hair,eyes,height,weight,marks,currentage,img,missingdesc,clothing,lastseenlat,lastseenlon,lastseendate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', info)

    conn.commit()

    #print dimensions
    cur.execute('SELECT * FROM namus_missing_ca')
    rowcount=len(cur.fetchall())
    cur.execute('PRAGMA table_info(namus_missing_ca)')
    colcount=len(cur.fetchall())
    print('Table dimensions:',rowcount,'x',colcount)
    
    #print the first 5 as a check
    print('Sample')
    cur.execute('SELECT * FROM namus_missing_ca')
    for row in cur.fetchall()[0:5]:
        print(row)
        
    cur.close()
    
# Scrape the California missing persons website

def default_missingca(database,start=1901,end=2022):
    
    # initiate a database
    conn=sqlite3.connect(database)
    cur=conn.cursor()
    
    # creating a table for missing_ca
    cur.execute('DROP TABLE IF EXISTS missing_ca')
    cur.execute('CREATE TABLE missing_ca (name TEXT, dob DATE, race TEXT, sex TEXT, hair TEXT, eyes TEXT, height FLOAT, weight INT,aka TEXT, marks TEXT, currentage INT, img TEXT)')
    
    # initiate count
    count=0
        
    # starting scrape from the CA missing website, looping through years in search to get all entries
    for yr in range(start,end):
        
        # Printing year being processed
        print('Pulling persons from 1st half of',yr)
        
        year=str(yr)
        content = requests.get('https://oag.ca.gov/missing/detailed-search-results?combine=&field_missing_person_sex_value=All&field_missing_person_hair_value=&field_missing_person_eye_color_value=&field_missing_person_county_value=All&field_missing_person_dob_value%5Bmin%5D%5Bdate%5D=1%2F1%2F'+year+'&field_missing_person_dob_value%5Bmax%5D%5Bdate%5D=6%2F30%2F'+year+'&field_missing_person_age_value=')
        soup = BeautifulSoup(content.content,'html.parser')
        # looping through a tags to get people info
        tags=soup('a')

        for tag in tags:
            href=tag.get('href')
            if href!=None and href.find('missing/person')>0:
                
                # initiate a list that holds all the info per person
                info_clean=[]
                
                # extract img
                if len(tag('img'))>0:
                    img=tag('img')[0].get('src')
                    
                # extract name, DOB, race, sex, hair, eye, height, weight, aka, and marks
                info=tag.get_text().replace('\r','').split('\n')
                if len(info)>1:
                    
                    # count persons
                    count+=1
                    print('Parsing person:',count)
                    
                    for i in range(len(info)):
                        if i<=8:
                            if info[i].find(':')>=0:
                                info_clean.append(info[i].split(':')[1].strip())
                            elif info[i].find(':')<0:
                                info_clean.append(info[i].strip())
                        elif i==11:
                            info_clean.append(info[i].strip())

                    # cleaning up values
                    height=float(info_clean[6].split(' ')[0])*12+(float(info_clean[6].split(' ')[1]))
                    weight=float(info_clean[7].split(' ')[0])
                    info_clean[6]=height
                    info_clean[7]=weight
                    currentage=2021-int(info_clean[1].split('/')[2])
                    info_clean.append(currentage)
                    info_clean.append(img)

                    # inserting into the database
                    if len(info_clean)==12:
                        cur.execute('INSERT INTO missing_ca (name,dob,race,sex,hair,eyes,height,weight,aka,marks,currentage,img) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', info_clean)
                    elif len(info_clean)==11:
                        cur.execute('INSERT INTO missing_ca (name,dob,race,sex,hair,eyes,height,weight,aka,currentage,img) VALUES (?,?,?,?,?,?,?,?,?,?,?)', info_clean)

        # Printing year being processed
        print('Pulling persons from 2nd half of',yr)
        
        content = requests.get('https://oag.ca.gov/missing/detailed-search-results?combine=&field_missing_person_sex_value=All&field_missing_person_hair_value=&field_missing_person_eye_color_value=&field_missing_person_county_value=All&field_missing_person_dob_value%5Bmin%5D%5Bdate%5D=7%2F1%2F'+year+'&field_missing_person_dob_value%5Bmax%5D%5Bdate%5D=12%2F31%2F'+year+'&field_missing_person_age_value=')
        soup = BeautifulSoup(content.content,'html.parser')
        # looping through a tags to get people info
        tags=soup('a')

        for tag in tags:
            href=tag.get('href')
            if href!=None and href.find('missing/person')>0:
                
                # initiate a list that holds all the info per person
                info_clean=[]
                
                # extract img
                if len(tag('img'))>0:
                    img=tag('img')[0].get('src')
                    
                # extract name, DOB, race, sex, hair, eye, height, weight, aka, and marks
                info=tag.get_text().replace('\r','').split('\n')
                if len(info)>1:
                    
                    # count persons
                    count+=1
                    print('Parsing person:',count)
                    
                    for i in range(len(info)):
                        if i<=8:
                            if info[i].find(':')>=0:
                                info_clean.append(info[i].split(':')[1].strip())
                            elif info[i].find(':')<0:
                                info_clean.append(info[i].strip())
                        elif i==11:
                            info_clean.append(info[i].strip())

                    # cleaning up values
                    height=float(info_clean[6].split(' ')[0])*12+(float(info_clean[6].split(' ')[1]))
                    weight=float(info_clean[7].split(' ')[0])
                    info_clean[6]=height
                    info_clean[7]=weight
                    currentage=2021-int(info_clean[1].split('/')[2])
                    info_clean.append(currentage)
                    info_clean.append(img)

                    # inserting into the database
                    if len(info_clean)==12:
                        cur.execute('INSERT INTO missing_ca (name,dob,race,sex,hair,eyes,height,weight,aka,marks,currentage,img) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', info_clean)
                    elif len(info_clean)==11:
                        cur.execute('INSERT INTO missing_ca (name,dob,race,sex,hair,eyes,height,weight,aka,currentage,img) VALUES (?,?,?,?,?,?,?,?,?,?,?)', info_clean)

    conn.commit()

    #print dimensions
    cur.execute('SELECT * FROM missing_ca')
    rowcount=len(cur.fetchall())
    cur.execute('PRAGMA table_info(missing_ca)')
    colcount=len(cur.fetchall())
    print('Table dimensions:',rowcount,'x',colcount)
    
    #print the first 5 as a check
    print('Sample')
    cur.execute('SELECT * FROM missing_ca')
    for row in cur.fetchall()[0:5]:
        print(row)

    cur.close()