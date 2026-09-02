import sys
import sqlite3
import matplotlib.pyplot as plt
from math import sin, cos, sqrt, atan2, radians
import urllib
import urllib.request

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
    
if __name__=='__main__':
    find(*sys.argv[1:])