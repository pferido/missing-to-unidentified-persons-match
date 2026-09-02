#dependencies
import sys
import sqlite3 
from bs4 import BeautifulSoup
import requests
import json
import default_scrape as scrape

#default mode
def default_function():

    #NAMUS unidentified
    print('Default scrape NAMUS Unidentified Data')
    scrape.default_unidentified('../data/missing.db',start=4,end=5)
    
    #NAMUS missing
    print('Default scrape NAMUS Missing Data')
    scrape.default_missing('../data/missing.db',start=4,end=5)
    
    #CA missing
    print('Default scrape CA Missing DATA')
    scrape.default_missingca('../data/missing.db')
    
    
#scrape mode
def scrape_function():
    
    #NAMUS unidentified
    print('Scrape NAMUS Unidentified Data')
    scrape.default_unidentified('../data/missing_scrape.db',start=4,end=5,limit=5)
    
    #NAMUS missing
    print('Scrape NAMUS Missing Data')
    scrape.default_missing('../data/missing_scrape.db',start=4,end=5,limit=5)
    
    #CA missing
    print('Scrape CA Missing Data')
    scrape.default_missingca('../data/missing_scrape.db',start=1901,end=1904)
    

#static mode
def static_function():

    # connect to static database
    conn=sqlite3.connect('../data/missing_static.db')
    cur=conn.cursor()
    
    #NAMUS unidentified
    print('Static NAMUS Unidentified Data')
    
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
        
    #NAMUS missing
    print('Static NAMUS Missing Data')
    
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
        
    #CA missing
    print('Static CA Missing Data')
    
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
    
if __name__=='__main__':
    if len(sys.argv)==1:
        default_function()
    elif sys.argv[1]=='--scrape':
        scrape_function()
    elif sys.argv[1]=='--static':
        static_function()