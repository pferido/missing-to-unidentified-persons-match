import sys
import sqlite3
from bs4 import BeautifulSoup
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import numpy as np
import matplotlib.pyplot as plt
from math import sin, cos, sqrt, atan2, radians
import urllib
import scraper as scraper

#### Scrape Data ####
if __name__=='__main__':
    if len(sys.argv)==1:
        print("### Full scrape of data ###")
        scraper.default_function()
    elif sys.argv[1]=='--static':
        print("### Using static database for analysis ###")
        scraper.static_function()
        
#### Data Cleaning ####
# Bringing together the two missing persons datasets
print('### Merging together the missing persons files, dropping duplicates ###')
conn=sqlite3.connect('../data/missing_static.db')
cur=conn.cursor()

# Identifying duplicates by merging on name, race, and age within 10 years 
cur.execute('DROP TABLE IF EXISTS missing_dup')
cur.execute('CREATE TABLE missing_dup AS SELECT x.name, x.currentage, x.sex, REPLACE(x.race,",","") as race_ca, x.sex, x.hair, x.eyes, x.height, x.weight, x.marks, REPLACE(y.race,",","") as race_namus, y.sex as sex_namus, y.hair as hair_namus, y.eyes as eyes_namus, y.height as height_namus, y.weight as weight_namus, y.marks as marks_namus, y.currentage as currentage_namus FROM missing_ca AS x INNER JOIN namus_missing_CA AS y ON REPLACE(x.name," ","")=REPLACE(y.name," ","") AND ABS(x.currentage-currentage_namus)<=10 AND (INSTR(race_ca,race_namus)>0 OR INSTR(race_namus,race_ca)>0)')
            
cur.execute('SELECT * FROM missing_dup')
ck=cur.fetchall()
print('Check # missing duplicates:',len(ck))

# Will keep the duplicates from the namus data but drop them from the missing ca data
cur.execute('DROP TABLE IF EXISTS missing_ca_nodup')
cur.execute('CREATE TABLE missing_ca_nodup AS SELECT x.name, x.race, x.sex, x.hair, x.eyes, x.height, x.weight, x.marks, x.currentage, x.img, NULL as missingdesc, NULL as clothing, NULL as lastseenlat, NULL as lastseenlon, NULL as lastseendate, x.aka, x.dob FROM missing_ca AS x LEFT JOIN missing_dup AS y ON x.name=y.name WHERE y.name IS NULL')

cur.execute('SELECT * FROM missing_ca_nodup')
ck=cur.fetchall()
print('Check # missing ca after dropping dups:', len(ck))

# Stacking the namus_missing_ca and missing_ca_nodup which should now not have duplicates
cur.execute('DROP TABLE IF EXISTS missing_all')
cur.execute('CREATE TABLE missing_all AS SELECT *, NULL as aka, NULL as dob FROM namus_missing_ca UNION ALL SELECT * FROM missing_ca_nodup')

conn.commit()
cur.execute('SELECT * FROM missing_all')
ck=cur.fetchall()
print('Check total # missing obs:', len(ck))
      
cur.close()

# Make a dataframe for ease of analysis on missing and unidentified data
missing_sql=pd.read_sql_query("SELECT * FROM missing_all",conn)
missing=pd.DataFrame(missing_sql)

unidentified_sql=pd.read_sql_query("SELECT * FROM namus_unidentified_ca", conn)
unidentified=pd.DataFrame(unidentified_sql)

# adding columns that checks for valid birthday
missing['dobck']=missing['dob'].isna()

# Writing functions to code race in cleaner categories
def racecat(row):
    if row['race'].count(',')>1 or row['race'].find('Biracial')>=0 or (row['dobck']==False and row['race'].find('/')>=0):
        return 'Multiracial'
    elif row['race'].find('White')>=0:
        return 'White'
    elif row['race'].find('Black')>=0:
        return 'Black'
    elif row['race'].find('Hispanic')>=0:
        return 'Hispanic'
    elif row['race'].find('Asian')>=0 or row['race'].find('Pacific Islander')>=0 or row['race'] in['Chinese','Japanese','Vietnamese','Filipino','Middle Eastern','Egyptian','Laotian','Samoan','Cambodian','Korean','Indian']:
        return 'Asian/Pacific Islander'
    elif row['race'].find('American Indian')>=0 or row['race'].find('American-Indian')>=0:
        return 'American Indian/Alaska Native'
    elif row['race'].find('Uncertain')>=0:
        return 'Uncertain'
    else:
        return 'Other'

def racecat_unidentified(row):
    if row['race'].count(',')>1:
        return 'Multiracial'
    elif row['race'].find('White')>=0:
        return 'White'
    elif row['race'].find('Black')>=0:
        return 'Black'
    elif row['race'].find('Hispanic')>=0:
        return 'Hispanic'
    elif row['race'].find('Asian')>=0 or row['race'].find('Pacific Islander')>=0 or row['race'] in['Chinese','Japanese','Vietnamese','Filipino','Middle Eastern','Egyptian','Laotian','Samoan','Cambodian','Korean','Indian']:
        return 'Asian/Pacific Islander'
    elif row['race'].find('American Indian')>=0 or row['race'].find('American-Indian')>=0:
        return 'American Indian/Alaska Native'
    elif row['race'].find('Uncertain')>=0:
        return 'Uncertain'
    else:
        return 'Other'

# Adding a clean categorical race variable
missing['racecat']=missing.apply(lambda row: racecat(row),axis=1)
unidentified['racecat']=unidentified.apply(lambda row: racecat_unidentified(row),axis=1)

# Performing checks on the race category 
pd.set_option('display.max_rows',None)
pd.crosstab(missing['race'],missing['racecat'])
pd.crosstab(unidentified['race'],unidentified['racecat'])

#### Comparison Analysis ####
# Comparing missing and unidentified data, trying to understand patterns
print('### Analysis on Missing and Unidentified Persons ###')
print('Number of Missing Persons by Race')
print(missing['racecat'].value_counts())

x_axis=np.arange(8)
x_labels=missing['racecat'].value_counts().index.array
#x_labels=['White','Hispanic','Black','Asian/Pacific Islander','Multiracial','Other','American Indian/Alaska Native','Uncertain']
plt.clf()
plt.bar(x_axis-0.2,missing['racecat'].value_counts(),0.4,label="Missing Race")
plt.bar(x_axis+0.2,unidentified['racecat'].value_counts(),0.4,label="Unidentified Race")
plt.xticks(x_axis,x_labels,rotation='vertical')
plt.xlabel('Race')
plt.ylabel('Count')
plt.title('Number of Persons by Race')
plt.legend()
plt.savefig('../output/numbyrace.png',bbox_inches='tight')
print('Output graph numbyrace.png')

# Percent would be much more helpful to compare
print('Distribution of Missing Persons by Race')
print(missing['racecat'].value_counts(normalize=True)*100)
plt.clf()
plt.bar(x_axis-0.2,missing['racecat'].value_counts(normalize=True)*100,0.4,label="Missing Race")
plt.bar(x_axis+0.2,unidentified['racecat'].value_counts(normalize=True)*100,0.4,label="Unidentified Race")
plt.xticks(x_axis,x_labels,rotation='vertical')
plt.xlabel('Race')
plt.ylabel('Percent')
plt.title('Percent of Persons by Race')
plt.legend()
plt.savefig('../output/pctbyrace.png',bbox_inches='tight')
print('Output graph pctbyrace.png')

# Comparison of sex distribution
print('Percent of Missing Persons by Sex')
print(missing['sex'].value_counts(normalize=True)*100)
print('Percent of Unidentified Persons by Sex')
print(unidentified['sex'].value_counts(normalize=True)*100)
x_labels_sex=missing['sex'].value_counts().index.array
x_axis_sex=np.arange(3)
plt.clf()
plt.bar(x_axis_sex-0.2,missing['sex'].value_counts(normalize=True)*100,0.4,label="Missing")
plt.bar(x_axis_sex+0.2,unidentified['sex'].value_counts(normalize=True)*100,0.4,label="Unidentified")
plt.xticks(x_axis_sex,x_labels_sex,rotation='vertical')
plt.xlabel('Sex')
plt.ylabel('Percent')
plt.title('Percent of Persons by Sex')
plt.legend()
plt.savefig('../output/pctbysex.png',bbox_inches='tight')
print('Output graph pctbysex.png')

# Comparison of age distribution
unidentified['currentageto']=pd.to_numeric(unidentified['currentageto'],errors='coerce')
unidentified_age=unidentified['currentageto'].value_counts(normalize=True).sort_index()
missing_age=missing['currentage'].value_counts(normalize=True).sort_index()
unidentified_age=unidentified_age.to_frame()
missing_age=missing_age.to_frame()
age=missing_age.join(unidentified_age,how="outer")

# dropping outlier ages
age=age[:197]

#plotting
plt.clf()
unidentified_age_labels=age.index.array
x_axis_age=np.arange(len(unidentified_age_labels))
plt.bar(x_axis_age-0.2,age['currentage'],0.4,label="Missing")
plt.bar(x_axis_age+0.2,age['currentageto'],0.4,label="Unidentified")
plt.xlabel('Age')
plt.ylabel('Percent')
plt.title('Percent of Persons by Age')
plt.legend()
plt.savefig('../output/pctbyage.png',bbox_inches='tight')
print('Output graph pctbyage.png')

# Adding geometric data so that we can map cases
missinggeo=[Point(xy) for xy in zip(missing["lastseenlon"],missing["lastseenlat"])]
unidentifiedgeo=[Point(xy) for xy in zip(unidentified["foundlon"],unidentified["foundlat"])]
crs={"init":"epsg:4326"}
missinggeodf=gpd.GeoDataFrame(missing,crs=crs,geometry=missinggeo)
unidentifiedgeodf=gpd.GeoDataFrame(unidentified,crs=crs,geometry=unidentifiedgeo)

# Comparison of locations
ca_map=gpd.read_file('../shpfiles/CA_Counties_TIGER2016.shp')
ca_map=ca_map.to_crs(crs=crs)
fig,ax=plt.subplots()
ca_map.plot(ax=ax,alpha=0.4,color='grey')
missinggeodf.plot(ax=ax,markersize=2,color='blue',marker='o',label='Missing')
unidentifiedgeodf.plot(ax=ax,markersize=2,color='orange',marker='*',label='Unidentified')
ax.set_xlim(left=-125,right=-110)
ax.set_ylim(top=43)
plt.legend()
plt.savefig('../output/CAmap.png')
print('Output figure CAmap.png')

#### Start creation of function to match unidentified persons with missing persons ####
print("### Creating function to match missing and unidentified persons ###")

# Create new SQL tables with clean new variables for queries
missing_new=missing.drop(['geometry'],axis=1)
missing_new.to_sql('missing_racecat',conn,if_exists='replace')
unidentified_new=unidentified.drop(['geometry'],axis=1)
unidentified_new.to_sql('unidentified_racecat',conn,if_exists='replace')

# Function to get distance between two points
def distmi(point1, point2):
    # approximate radius of earth in miles
    R = 3963.0
    lat1 = radians(point1[1])
    lon1 = radians(point1[0])
    lat2 = radians(point2[1])
    lon2 = radians(point2[0])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance
    
# Function for searching unidentified persons database for missing person
# Matching on the following variables when available: 
# date lost <= date found
# race, sex, eyes, hair 
# and the following with a buffer: height, weight, age
# Finally limiting matches to those within the mile radius specified

def find(name,distance=50,ageyrs_buffer=10,height_buffer=6,weight_buffer=20):
    
    distance=float(distance)
    ageyrs_buffer=float(ageyrs_buffer)
    height_buffer=float(height_buffer)
    weight_buffer=float(weight_buffer)
    
    conn=sqlite3.connect('../data/missing_static.db')
    cur=conn.cursor()
    
    # Print missing persons info
    cur.execute('SELECT * FROM missing_racecat WHERE REPLACE(name," ","")="'
                +name.replace(" ","")
                +'"')
    missfound=cur.fetchall()
    if len(missfound)>0:
        misslatlon=(missfound[0][13],missfound[0][14])
        print('Missing Info:',missfound[0])
        # Show image of missing person
        missimg=missfound[0][10]
    else:
        print('No Missing Person with this name in database')
        
    
    # Run query to search for unidentified persons with matching characteristics
    cur.execute('SELECT y.* FROM unidentified_racecat AS y INNER JOIN (SELECT * FROM missing_racecat WHERE REPLACE(name," ","")="'
                +name.replace(" ","")
                +'") AS X ON (x.racecat=y.racecat or y.race="") AND (x.sex=y.sex or y.sex="Unsure") AND (instr(y.hair,x.hair)>0 or y.hair="" or y.hair="Unknown") AND (x.eyes=y.eyes or y.eyes="" or y.eyes="Unknown") AND ((y.currentagefrom-'
                +str(ageyrs_buffer)
                +'<=x.currentage AND x.currentage<=y.currentageto+'
                +str(ageyrs_buffer)
                +') or y.currentageto is Null or y.currentagefrom is Null) AND ((y.heightfrom-'
                +str(height_buffer)
                +'<=x.height and x.height<=y.heightto+'
                +str(height_buffer)
                +') or y.heightfrom is Null or y.heightto is Null) AND ((y.weight-'
                +str(weight_buffer)
                +'<=x.weight and x.weight<=y.weight+'
                +str(weight_buffer)
                +') or y.weight is Null) AND x.lastseendate<=y.founddate')
    
    found=cur.fetchall()
    potentialmatch=[]
    matchcnt=0
    for i in found:
        unidentifiedlatlon=[i[14],i[15]]
        dist=distmi(misslatlon,unidentifiedlatlon)
        if dist<=distance:
            matchcnt+=1
            print('Potential Match',matchcnt)
            potentialmatch.append(i)
            print('Dist:',dist,i)
        
    print('Total Potential Matches:',len(potentialmatch))
    # create an image for the print
    if len(potentialmatch)>0:
        plt.clf()
        fig=plt.figure(figsize=(4*len(potentialmatch)+1,3*len(potentialmatch)+1))
        rows=len(potentialmatch)+1
        columns=1

        f=urllib.request.urlretrieve(missimg)
        a=plt.imread(f[0])
        fig.add_subplot(rows,columns,1)
        plt.imshow(a)
        plt.axis('off')
        plt.title('Missing Person:'+missfound[0][1],fontsize='x-large')
        
        count=0
        imgcount=0
        for person in potentialmatch:
            count+=1
            if person[11]!='':
                imgcount+=1
                unidentifiedimg=person[11]
                f=urllib.request.urlretrieve(unidentifiedimg)
                plt.subplot(rows,columns,imgcount+1)
                plt.imshow(plt.imread(f[0]))
                plt.axis('off')
                plt.title('Potential Match '+str(count),fontsize='x-large')
        plt.savefig('../output/PotentialMatches_'+missfound[0][1]+'.png',bbox_inches='tight')
        print('Output images of potential matches for',missfound[0][1])  
    
    cur.close()
    
find('Abraham Volker',distance=100)
find('Eddie Gonzalez',distance=300)
find('Anita Qvist')

