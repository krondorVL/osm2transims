# -*- coding: utf-8 -*-
EPSG = 4326
#very important parameter-depends on geo
#This is confusing - it seems that Google Maps and OpenStreetMap
#use EPSG3857 but they use WGS84 which 'is' EPSG4326
#http://gis.stackexchange.com/questions/48949/epsg-3857-or-4326-
#for-googlemaps-openstreetmap-and-leaflet

import os
import sys

import xml.etree.cElementTree as ET


LinkType = {}


LinkType['trunk'] = 'FREEWAY'
LinkType['motorway'] = 'EXPRESSWAY' #у нас нет таких дорог
LinkType['primary'] = 'MAJOR'
LinkType['secondary'] = 'MINOR'
LinkType['track'] = 'LOCAL'
LinkType['tertiary'] = 'LOCAL'
LinkType['living_street'] = 'LOCAL'
LinkType['residential'] = 'LOCAL'
LinkType['service'] = 'LOCAL'
LinkType['services'] = 'LOCAL'#почему то не service

LinkType['primary_link'] = 'RAMP'
LinkType['motorway_link'] = 'RAMP' #у нас нет таких дорог
LinkType['tertiary_link'] = 'RAMP'
LinkType['trunk_link'] = 'RAMP'
LinkType['secondary_link'] = 'RAMP'

LinkType['unclassified'] = 'OTHER'
LinkType['road'] = 'OTHER'

LinkType['footway'] = 'WALKWAY'
LinkType['pedestrian'] = 'WALKWAY'
LinkType['steps'] = 'WALKWAY'
LinkType['path'] = 'WALKWAY'
LinkType['bridleway'] = 'WALKWAY'

#LinkType['railway'] = 'HEAVYRAIL'#у нас нет таких дорог почему то
#еще есть: 'construction', - строящиеся дороги,
#'platform' - площадки для посадки людей

print 'Parsing OSM data for nodes and ways ...'
Nodes = {}
Ways = {}

#-------------------------------АС-------------------
AC = {}
AcWay = {}
#AmenityType = ['bank','library']
#ShopType = ['hairdresser','travel_agency', 'convenience']


#----------------------------------------------------

Counter = 0
NodeErrors = 0
#стандартная штука из мануала
#http://effbot.org/zone/element-iterparse.htm
Context = ET.iterparse ( 'vl.osm' )
Conext = iter ( Context )
Event, Root = Context.next ()
#узлы, третий параметр - чтобы понять скольким линкам принадлежит узел
for Event, Child in Context:
    if Child.tag == 'node':
        #Subs = [Sub.tag for Sub in Child]
        Id = int ( Child.attrib['id'] )
        Lon = Child.attrib['lon']
        Lat = Child.attrib['lat']
        Nodes[Id] = [ Lon, Lat, 0 ] #3 параметр для УДС
        for Sub in Child:
            if Sub.tag == 'tag':
                #if Sub.attrib['k'] == 'amenity' and Sub.attrib['v'] in AmenityType:
                if Sub.attrib['k'] == 'amenity':
                    AC[Id] = [Lon, Lat, 'Amenity', Sub.attrib['v']]
                #if Sub.attrib['k'] == 'shop' and Sub.attrib['v'] in ShopType:
                if Sub.attrib['k'] == 'shop':
                    AC[Id] = [Lon, Lat, 'Shop', Sub.attrib['v']]
                if Sub.attrib['k'] == 'leisure':
                    AC[Id] = [Lon, Lat, 'Leisure', Sub.attrib['v']]
                if Sub.attrib['k'] == 'office':
                    AC[Id] = [Lon, Lat, 'Office', Sub.attrib['v']]
                if Sub.attrib['k'] == 'shop':
                    AC[Id] = [Lon, Lat, 'Shop', Sub.attrib['v']]
        Child.clear ()
        Subs=[]
    #линии - пока еще не линки графа, а просто osm way
    if Child.tag == 'way':
        Id = int ( Child.attrib['id'] )
        Ways[Id] = {}
        Ways[Id]['NODES'] = []
        for Sub in Child:
            if Sub.tag == 'nd':
                Node = int ( Sub.attrib['ref'] )
                try:
                    Nodes[Node][2] += 1 #отмечаем ноды в линках.
                    Ways[Id]['NODES'].append ( Node )
                except:
                    NodeErrors += 1
                    if Sub.tag == 'tag' and Sub.attrib['k'] != 'highway':
                        print 'ERROR in WayID:', Id, ' in ', Node
                    Ways[Id] = {}
                    break
            if Sub.tag == 'tag':
                if Sub.attrib['k'] == 'highway' and Sub.attrib['v'] in LinkType:
                    Ways[Id]['TYPE'] = Sub.attrib['v']
                if Sub.attrib['k'] == 'oneway':
                    Ways[Id]['ONEWAY'] = Sub.attrib['v'] #может быть no вместо null
                if Sub.attrib['k'] == 'name':
                    Ways[Id]['NAME'] = Sub.attrib['v']
                if Sub.attrib['k'] == 'lanes':
                    Ways[Id]['LANES'] = Sub.attrib['v']
                if Sub.attrib['k'] == 'maxspeed':
                    Ways[Id]['SPEED'] = Sub.attrib['v']               
                #if Sub.attrib['k'] == 'shop' and Sub.attrib['v'] in ShopType:
                if Sub.attrib['k'] == 'shop':
                    AcWay[Id]={}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Shop'
                #if Sub.attrib['k'] == 'amenity' and Sub.attrib['v'] in AmenityType:
                if Sub.attrib['k'] == 'amenity':
                    AcWay[Id]={}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Amenity'
                if Sub.attrib['k'] == 'leisure':
                    AcWay[Id]={}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Leisure'
                if Sub.attrib['k'] == 'office':
                    AcWay[Id]={}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Office'
        if 'TYPE' not in Ways[Id]:
            del Ways[Id]
        Child.clear()
Root.clear ()


print 'Removing unused nodes from the network ...'
UnusedNodes = []
for Node in Nodes:
        Lon, Lat, Count = Nodes[Node][0:3]
        if Count == 0:
                UnusedNodes.append ( Node )
for Node in UnusedNodes:
        del Nodes[Node]
del UnusedNodes

print 'Splitting ways into links as needed ...'
Groups = {}
Links = {}
NewNodes = {}
LinkId = 10001 #просто случайное число)) нужно аналогично придумать для нодов, а то не влазим в диапазон Int

for Id in Ways:
                ShapeCount = len ( Ways[Id]['NODES'] )
                if ShapeCount < 2: #одна нода в way
                        continue
                SegPos = 0
                Links[LinkId] = {}
                Links[LinkId]['NODES'] = []
                Links[LinkId]['TYPE'] = Ways[Id]['TYPE']
                #настраиваем перелинковку Группа-Way-Link
                Links[LinkId]['GROUP'] = Id
                Groups[Id] = [ LinkId ]
                #здесь разбиваем way на отдельные сегменты.
                for Index in range ( ShapeCount ):
                        Node = Ways[Id]['NODES'][Index]
                        Lon, Lat, Count= Nodes[Node][0:3]
                        Links[LinkId]['NODES'].append ( Node )  #каждую ноду из вей добавляем в линкс
                        if Index == 0 or Index == ShapeCount - 1: #крайние точки
                                if Node not in NewNodes:
                                        NewNodes[Node] = [ Lon, Lat, 0 ]#пропускаем транзитные ноды (не добавляем в nodes)
                                NewNodes[Node][2] += 1
                        elif Count > 1: #если нода в нескольких way - создаем новый way
                                if SegPos > 0 and Index < ShapeCount - 1:
                                        SegPos = 0
                                        #создаем новый линк
                                        LinkId += 1
                                        Links[LinkId] = {}
                                        Links[LinkId]['NODES'] = [ Node ]
                                        Links[LinkId]['TYPE'] = Ways[Id]['TYPE']
                                        Links[LinkId]['GROUP'] = Id
                                        Groups[Id].append ( LinkId )
                                        if Node not in NewNodes:
                                                NewNodes[Node] = [ Lon, Lat, 0 ]
                                        NewNodes[Node][2] += 1
                        SegPos += 1
                LinkId += 1


print 'Checking the sanity of Node and Link relationships ...'
for Link in Links:
        Count = len ( Links[Link]['NODES'] )
        if Links[Link]['NODES'][0] not in NewNodes:
                print 'A-Node not found!', Link, Links[Link]['NODES'][0]
        elif Links[Link]['NODES'][Count-1] not in NewNodes:
                print 'B-Node not found!', Link, Links[Link]['NODES'][-1]
        for Id in Links[Link]['NODES'][1:Count-1]:
                if Id in NewNodes:
                        print 'Shape point is also a node!', Link, Id


#финальная обработка
print 'Creating the final Link data ...'
NewLinks = {}
for Link in Links:
        GeoString = 'LINESTRING('
        NodeA = Links[Link]['NODES'][0]
        NodeB = Links[Link]['NODES'][-1]
        Type = Links[Link]['TYPE']
        Group = Links[Link]['GROUP']
        for Node in Links[Link]['NODES']:
                Lon, Lat = Nodes[Node][0:2]
                GeoString += str(Lon) + ' ' +str(Lat) + ','
        GeoString = GeoString[:-1] + ')'
        NewLinks[Link] = [ NodeA, NodeB, Group, Type, GeoString ]
        if len ( Links[Link]['NODES'] ) < 2:
                print '==> ERROR!', Link, NodeA, NodeB, Group, Type, GeoString

print 'OSM Ways:', len ( Ways ), '; OSM Nodes:', len ( Nodes ), '; Nodes:', len ( NewNodes ), '; NewLinks:', len ( NewLinks ), '; Groups:', len ( Groups )

print 'Creating the database ...'


import sqlite3
import os
import platform

if os.path.exists('network_vl.sqlite'):
    os.remove('network_vl.sqlite')  
dbcon = sqlite3.connect ( 'network_vl.sqlite' )
dbcon.execute('pragma journal_mode = off;')
dbcon.execute('pragma synchronous = 0;')
dbcon.enable_load_extension(1)

dbcon.isolation_level = None



dbcur = dbcon.cursor ()
if platform.system() == 'Windows':
    dbcur.execute ( "select load_extension('mod_spatialite');" ) #for windows
else:
    dbcur.execute ( "select load_extension('libspatialite');" )


dbcur.execute("begin ;")
dbcur.execute("select InitSpatialMetadata();")
dbcur.execute("commit ;")


#dbcur.execute ( 'drop table if exists NODE;' )
#dbcur.execute ( 'drop table if exists LINK;' )
#dbcur.execute ( 'drop table if exists AcNodes;' )
#dbcur.execute ( 'drop table if exists AcLinks;' )

print 'Creating the Node table ...'
dbcur.execute ( """
CREATE TABLE "Node" (
"node" INTEGER NOT NULL PRIMARY KEY,
"x" REAL DEFAULT 0,
"y" REAL DEFAULT 0,
"z" REAL DEFAULT 0);
""" )
dbcur.execute ( "select AddGeometryColumn ( 'Node', 'GEO', ?, 'POINT', 2 );", [ EPSG ] )
dbcur.execute ( "select CreateMbrCache ( 'Node', 'GEO' );" )


print 'Creating the Link table ...'
dbcur.execute ( """
CREATE TABLE "Link" (
"link" INTEGER NOT NULL PRIMARY KEY,
"name" TEXT DEFAULT '',
"node_a" INTEGER NOT NULL,
"node_b" INTEGER NOT NULL,
"length" REAL DEFAULT 0,
"setback_a" REAL DEFAULT 0,
"setback_b" REAL DEFAULT 0,
"bearing_a" INTEGER DEFAULT 0 NOT NULL,
"bearing_b" INTEGER DEFAULT 0 NOT NULL,
"type" TEXT NOT NULL,
"use" TEXT DEFAULT '' NOT NULL,
"lanes_ab" INTEGER DEFAULT 0 NOT NULL,
"speed_ab" REAL DEFAULT 0,
"fspd_ab" REAL DEFAULT 0,
"cap_ab" INTEGER DEFAULT 0 NOT NULL,
"lanes_ba" INTEGER DEFAULT 0 NOT NULL,
"speed_ba" REAL DEFAULT 0,
"fspd_ba" REAL DEFAULT 0,
"cap_ba" INTEGER DEFAULT 0 NOT NULL,
"left_ab" INTEGER DEFAULT 0 NOT NULL,
"right_ab" INTEGER DEFAULT 0 NOT NULL,
"left_ba" INTEGER DEFAULT 0 NOT NULL,
"right_ba" INTEGER DEFAULT 0 NOT NULL);
""" )


dbcur.execute ( "select AddGeometryColumn ( 'LINK', 'GEO', ?, 'LINESTRING', 2 );", [ EPSG ] )
dbcur.execute ( "select CreateMbrCache ( 'LINK', 'GEO' );" )

print 'Creating the AC Nodes table ...'
dbcur.execute ( """
CREATE TABLE "AcNodes" (
"id" INTEGER NOT NULL PRIMARY KEY,
"node" INTEGER NOT NULL,
"link" INTEGER NOT NULL,
"offset" REAL DEFAULT 0,
"layer" TEXT NOT NULL,
"easting" REAL DEFAULT 0,
"northing" REAL DEFAULT 0,
"elevation" REAL DEFAULT 0,
"notes" TEXT NOT NULL,
"tag" TEXT NOT NULL,
"source" TEXT NOT NULL);
""" )

dbcur.execute ( "select AddGeometryColumn ( 'AcNodes', 'GEO', ?, 'POINT', 2 );", [ EPSG ] )
dbcur.execute ( "select CreateMbrCache ( 'AcNodes', 'GEO' );" )

print 'Creating the AC Ways table ...'
dbcur.execute ( """
CREATE TABLE "AcLinks" (
"id" INTEGER NOT NULL PRIMARY KEY,
"type" TEXT NOT NULL,
"tag" TEXT NOT NULL);
""" )
dbcur.execute ( "select AddGeometryColumn ( 'AcLinks', 'GEO', ?, 'POLYGON', 'XY' );", [ EPSG ] )
dbcur.execute ( "select CreateMbrCache ( 'AcLinks', 'GEO' );" )

print 'Loading the Node table ...'
Counter = 0

dbcon.commit ()
dbcur.execute("begin")

for Node in NewNodes:
        Lon, Lat, Count = NewNodes[Node]
        GeoString = 'POINT(' + str(Lon) + ' ' + str(Lat) + ')'
        SqlString = 'insert into Node values ( ?, ?, ?, 0.0, Transform ( GeomFromText ( ?, 4326 ), ? ) );'
        dbcur.execute ( SqlString, [ Node, Lon, Lat, GeoString, EPSG ] )
        Counter += 1
dbcur.execute("commit")

print 'Loading the AcNodes table ...'
for node in AC:
    Lon, Lat, Tag, Type = AC[node]
    GeoString = 'POINT(' + str(Lon) + ' ' + str(Lat) + ')'
    SqlString = "insert into AcNodes values ( ?, 0, 0, 0.0, 'AUTO/BUS/WALK', ?, ?, 0.0, ?, ?, 'POI', Transform ( GeomFromText ( ?, 4326 ), ? ) );"
    dbcur.execute ( SqlString, [ node, Lon, Lat, Type, Tag, GeoString, EPSG ] )
#dbcur.execute("commit")

print 'Updating X and Y coordinates of the Node and AcNode tables ...'
dbcur.execute ( "update Node set X = X ( ST_Transform(GEO,32652) ), Y = Y ( ST_Transform(GEO,32652) );" )
#dbcur.execute ( "update AcNodes set easting = X ( GEO ), northing = Y ( GEO );" )
dbcon.commit ()


print 'Loading the Link table ...'
Counter = 0
for Link in NewLinks:
        NodeA, NodeB, Group, Type, GeoString = NewLinks[Link]
        LanesAB = LanesBA = 1
        CapAB = CapBA = 500
        Name = ''
        if 'LANES' in Ways[Group]:
                LanesAB = LanesBA = int ( Ways[Group]['LANES'] )
        if 'ONEWAY' in Ways[Group]:
                LanesBA = 0
                CapBA = 0
        if 'NAME' in Ways[Group]:
                Name = Ways[Group]['NAME']
        SqlString = "insert into LINK values ( ?, ?, ?, ?, 0.0, 0.0, 0.0, 0, 0, ?, 'ANY', ?, 10.0, 10.0, ?, ?, 10.0, 10.0, ?, 0, 0, 0, 0, Transform ( GeomFromText ( ?, 4326 ), ? ) );"
        #if Type in LinkType.keys():
        dbcur.execute ( SqlString, [ Link, Name, NodeA, NodeB, LinkType[Type], LanesAB, CapAB, LanesBA, CapBA, GeoString, EPSG ] )
        Counter += 1
#        if Counter == int ( Counter / 100000 ) * 100000:
#                print 'COMMIT', Counter, Link
#                dbcon.commit ()
dbcon.commit ()

print 'Loading the AcLinks table ...'
Cc = 0
for link in AcWay:
    GeoString = 'POLYGON(('
    for Node in AcWay[link]['NODES']:
        Lon, Lat = Nodes[Node][0:2]
        GeoString += str(Lon) + ' ' +str(Lat) + ','
    GeoString = GeoString[:-1] + '))'
    Type = AcWay[link]['Type']
    Tag = AcWay[link]['Tag']
    SqlString = "insert into AcLinks values ( ?, ?, ?, Transform ( GeomFromText ( ?, 4326 ), ? ) );"
    dbcur.execute ( SqlString, [ link, Type, Tag, GeoString, EPSG ] )


print 'Updating the Length fields in the Link table ...'
dbcur.execute ( "update LINK set LENGTH = GLength ( GEO, 1 );" )
dbcon.commit ()

import math
def Bearing ( AX, AY, BX, BY ):
        if AX == BX and AY == BY:
                return 0
        Alpha = math.atan2 ( BY - AY, BX - AX ) / math.pi * 180.0
        if Alpha < 0.0: Alpha += 360.0
        C = 90.0 - Alpha
        if C < 0.0: C += 360.0
        return int ( round ( C, 0 ) )


print 'Updating the Bearing fields in the Link table ...'
dbcon.create_function ( 'Bearing', 4, Bearing )
dbcur.execute ( "update LINK set BEARING_A = Bearing ( X(PointN(GEO,1)), Y(PointN(GEO,1)), X(PointN(GEO,2)), Y(PointN(GEO,2)) );" )
dbcur.execute ( "update LINK set BEARING_B = Bearing ( X(PointN(ST_Reverse(GEO),2)), Y(PointN(ST_Reverse(GEO),2)), X(PointN(ST_Reverse(GEO),1)), Y(PointN(ST_Reverse(GEO),1)) );" )
dbcon.commit ()

print 'Updating AcNodes from centroids of AcLines'

rs = dbcur.execute( "SELECT max(id) FROM AcNodes;" )
for row in rs:
    MAX_N = int(row[0])


#rs = dbcur.execute( "SELECT type, tag, ST_AsText(ST_Centroid(GEO)) FROM AcLinks;" )
rs = dbcur.execute( "SELECT type, tag, ST_Centroid(GEO) FROM AcLinks;" )

for row in rs.fetchall():
    MAX_N += 1
    Type = row[0]
    Tag =row[1]
    GeoString = row[2]
    #SqlString = "insert into AcNodes values ( ?, 0, 0.0, 'ANY', 0.0, 0.0, 0.0, ?, ?, 'Centroid', Transform ( GeomFromText ( ?, 4326 ), ? ) );"
    #dbcur.execute ( SqlString, [ MAX_N, Type, Tag, GeoString, EPSG ] )
    SqlString = "insert into AcNodes values ( ?, 0, 0, 0.0, 'AUTO/BUS/WALK', 0.0, 0.0, 0.0, ?, ?, 'Centroid', ? );"
    dbcur.execute ( SqlString, [ MAX_N, Type, Tag, GeoString ] )
dbcon.commit ()

dbcur.execute ( "update AcNodes set easting = X ( ST_Transform(GEO,32652) ), northing = Y ( ST_Transform(GEO,32652) );" )
dbcon.commit ()


print 'Finding the nearest neighbourhood of AC Nodes and Links'
#http://gis.stackexchange.com/questions/155725/nearest-neighbor-query-in-spatialite
#http://gis.stackexchange.com/questions/136403/postgis-nearest-point-with-st-distance
#http://gis.stackexchange.com/questions/15574/how-to-find-nearest-neighbors-between-two-tables-with-point-locations-in-spatial?rq=1

'''
возвращает Null
sql_md = "SELECT A.link, A.node_a, B.id, MIN(ST_Distance(A.GEO, B.GEO)) AS distance FROM Link AS A, AcNodes AS B WHERE A.ROWID IN ( SELECT ROWID FROM SpatialIndex WHERE f_table_name = 'Link' AND search_frame = BuildCircleMbr(ST_X(B.GEO), ST_Y(B.GEO), 10000));"

кучу времени думает и возвращает одну строку с нулевым расстоянием
sql_md = "SELECT A.link, A.node_a, B.id, min(ST_Distance(A.GEO, B.GEO)) FROM Link AS A, AcNodes AS B;"
rs = dbcur.execute(sql_md)
for row in rs.fetchall():
    print row

http://gis.stackexchange.com/questions/155725/nearest-neighbor-query-in-spatialite
http://gis.stackexchange.com/questions/15574/how-to-find-nearest-neighbors-between-two-tables-with-point-locations-in-spatial

sql_md = "UPDATE AcNodes SET offset=(SELECT ST_Distance(p.GEO, l.GEO) AND p.ROWID IN" \
         "(SELECT ROWID FROM SpatialIndex WHERE f_table_name= 'AcNodes'  AND search_frame=l.GEO)" \
                                                                                   "FROM Link AS l, AcNodes AS p" \
                                                                                   "WHERE p.id = AcNodes.id" \
                                                                                   "ORDER BY ST_Distance(p.geometry, l.geometry) LIMIT 1);"

sql_md = "SELECT l.link, l.node_a, p.id, ST_Distance(p.GEO, l.GEO) " \
         "FROM Link as l, AcNodes AS p WHERE p.ROWID IN " \
         "(SELECT ROWID FROM SpatialIndex WHERE f_table_name= 'AcNodes'  AND search_frame=l.GEO) " \
         "ORDER BY ST_Distance(p.GEO, l.GEO) LIMIT 1;"
no such module: VirtualSpatialIndex


rs = dbcur.execute(sql_md)
for row in rs.fetchall():
    print row
http://gis.stackexchange.com/questions/143175/sqlite-db-with-fdo-geometries-how-to-assign-id-of-point-in-layer-a-to-closest-p?rq=1
Попробовать (вроде работает):
SELECT t1.id1 AS id1, t2.id2 AS id2, Min(Distance(t1.GEOMETRY,t2.GEOMETRY)) AS DIST FROM fc1 AS t1, fc2 AS t2 GROUP BY t1.id1 ORDER BY id1;

SELECT t1.id AS id1, t2.id AS id2,
Min(Distance(t1.GEOMETRY,t2.GEOMETRY)) AS DIST
FROM spl_fc1 AS t1, spl_fc2 AS t2
GROUP BY t1.id
ORDER BY id1;

Возвращает одну запись??? - попробовать с мин и без мин: это не то
SELECT t1.id1 AS id1, t2.id2 AS id2, Min(Distance(t1.GEOMETRY,t2.GEOMETRY)) AS DIST FROM fdo_fc1 AS t1, fdo_fc2 AS t2 GROUP BY t1.id1 ORDER BY id1;
как то работает, но надо покурить дистанс - чтобы мерил в метрах
'''
'''
#dbcur.execute("begin ;")
dbcur.execute ("CREATE TABLE PreUpAcNodes AS SELECT p.id AS pid, l.link AS lid, l.node_a AS lnd, Min(ST_Distance(p.GEO, l.GEO, 1)) AS Dist FROM AcNodes AS p, Link AS l GROUP BY p.id ORDER BY p.id;")
dbcon.commit()
#data = dbcur.execute ("SELECT p.id AS pid, l.link AS lid, l.node_a AS lnd, Min(ST_Distance(p.GEO,l.GEO)) AS Dist FROM AcNodes AS p, Link AS l GROUP BY p.id ORDER BY p.id;")
#dbcur.execute("commit ;")

#print 'Updating the node of AC Nodes'
print 'Print results'
dbcur.execute("SELECT lid, Dist FROM PreUpAcNodes")
for row in dbcur.fetchall():
    print row
'''
'''
print 'Print results'
dbcur.execute("begin ;")
data = dbcur.execute("Select * from PreUpAcNodes")

with open("ac_nodes.txt", "wb") as out:
    out.write("%s\t%s\t%s\t%s\n" % ('pid','lid','lnd','Dist'))
    for row in data.fetchall():
        out.write("%d\t%d\t%d\t%f\n" % (row[0], row[1], row[2], row[3]))
dbcur.execute("commit ;")
'''
#rs = dbcur.execute ("SELECT pid, lid, lnd, Dist FROM PreUpAcNodes;")
#for row in rs.fetchall():
#    print row
#dbcur.execute("begin ;")
#dbcur.execute ("UPDATE AcNodes SET node=(SELECT lnd FROM PreUpAcNodes WHERE id=pid), link=(SELECT lid FROM PreUpAcNodes WHERE id=pid), offset=(SELECT Dist FROM PreUpAcNodes WHERE id=pid);")
#dbcur.execute ("UPDATE AcNodes SET node=(SELECT lnd FROM PreUpAcNodes WHERE), link=(SELECT lid FROM PreUpAcNodes), offset=(SELECT Dist FROM PreUpAcNodes);")
#dbcur.execute ("UPDATE AcNodes SET link=(SELECT lid FROM PreUpAcNodes WHERE pid=AcNodes.id);")
#dbcur.execute("commit ;")
