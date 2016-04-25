# -*- coding: utf-8 -*-
import os
import argparse
import sqlite3
import xml.etree.cElementTree as ET
import math

parser = argparse.ArgumentParser(description='Testing argparser')
parser.add_argument('-EPSG', type=int, help='UTM EPSG for data', required=True)
parser.add_argument('-i', help='input file destination', required=True)
parser.add_argument('-o', help='output db-file destination')

args = parser.parse_args()
EPSG = args.EPSG
infile = args.i
outfile = args.o

if not os.path.exists(infile):
    print "Coudn't find input file"
    raise SystemExit

if outfile is None:
    outfile = infile + '.sqlite'

LinkType = {}

LinkType['trunk'] = 'FREEWAY'
LinkType['motorway'] = 'EXPRESSWAY'  # у нас нет таких дорог
LinkType['primary'] = 'MAJOR'
LinkType['secondary'] = 'MINOR'
LinkType['track'] = 'LOCAL'
LinkType['tertiary'] = 'LOCAL'
LinkType['living_street'] = 'LOCAL'
LinkType['residential'] = 'LOCAL'
LinkType['service'] = 'LOCAL'
LinkType['services'] = 'LOCAL'  # почему то не service

LinkType['primary_link'] = 'RAMP'
LinkType['motorway_link'] = 'RAMP'  # у нас нет таких дорог
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

# LinkType['railway'] = 'HEAVYRAIL'#у нас нет таких дорог почему то
# еще есть: 'construction', - строящиеся дороги,
# 'platform' - площадки для посадки людей

print 'Parsing OSM data for nodes and ways ...'
Nodes = {}
Ways = {}

# -------------------------------АС-------------------
AC = {}
AcWay = {}
# AmenityType = ['bank','library']
# ShopType = ['hairdresser','travel_agency', 'convenience']


# ----------------------------------------------------
# ----------------------------------------------------
# print data in csv
def incsv(Nodes, Links, Ways):
    """
    print main data in csv
    debug procedure for manage troubles with db
    """
    print 'Creating the text-base ...'
    with open(outfile + ".nodes.txt", "w") as out:
        out.write("%s\t%s\t%s\n" % ('node', 'x', 'y'))
        for Node in Nodes:
            Lon, Lat, Count, Id = Nodes[Node]
            out.write("%d\t%f\t%f\n" % (Id, float(Lon), float(Lat)))
    out.close()
    with open(outfile + ".links.txt", "w") as out:
        out.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ('link', 'name', 'node_a', 'node_b', 'type', 'lanes_ab', 'lanes_ba'))
        for Link in Links:
            NodeA, NodeB, Group, Type, GeoString = Links[Link]
            #print 'Link=',Link,'NodeA=',NodeA,'NodeId=',Nodes[NodeA][3]
            LanesAB = LanesBA = 1
            Name = ''
            SpeedAB = SpeedBA = 60 / 1.609
            if 'LANES' in Ways[Group]:
                try:
                    LanesAB = int(Ways[Group]['LANES'])
                    if LanesAB != 1:
                        LanesAB //= 2
                        LanesBA //= 2
                except ValueError:
                    print 'Please, check data for way with OSM id ', Group, ' you have something strange' \
                                                                            ' in lanes: ', Ways[Group]['LANES']
                    LanesAB = int(Ways[Group]['LANES'].split(';', 1)[0])
                    if LanesAB != 1:
                        LanesAB //= 2
                        LanesBA //= 2
            if 'ONEWAY' in Ways[Group]:
                LanesBA = 0
                CapBA = 0
            if 'SPEED' in Ways[Group]:
                try:
                    SpeedAB = SpeedBA = float(Ways[Group]['SPEED']) / 1.609
                except:
                    print 'Please, check data for way with OSM id ', Group, ' you have something strange' \
                                                                            ' in speed: ', Ways[Group]['SPEED']
            if ('ONEWAY' in Ways[Group]) & ('LANES' in Ways[Group]):
                try:
                    LanesAB = int(Ways[Group]['LANES'])
                    if LanesAB != 1:
                        LanesAB //= 2
                        LanesBA //= 2
                except ValueError:
                    print 'Please, check data for way with OSM id ', Group, ' you have something strange' \
                                                                            ' in lanes: ', Ways[Group]['LANES']
                    LanesAB = int(Ways[Group]['LANES'].split(';', 1)[0])
                    if LanesAB != 1:
                        LanesAB //= 2
                        LanesBA //= 2
            if 'NAME' in Ways[Group]:
                Name = Ways[Group]['NAME'].encode('utf-8')
            if Type in LinkType.keys():
                out.write("%d\t%s\t%d\t%d\t%s\t%d\t%d\n" % (
                Link, Name, int(NodeA), int(NodeB), LinkType[Type], LanesAB, LanesBA))
    out.close()

def indb(Nodes, Links, Ways, AllNodes, AC, AcWay):
    """
    import data in database
    """
    print 'Creating the database ...'

    if os.path.exists(outfile):
        os.remove(outfile)
    dbcon = sqlite3.connect(outfile)
    dbcon.execute('pragma journal_mode = off;')
    dbcon.execute('pragma synchronous = 0;')
    dbcon.enable_load_extension(1)

    dbcon.isolation_level = None

    dbcur = dbcon.cursor()
    dbcur.execute("select load_extension('mod_spatialite');")

    dbcur.execute("begin ;")
    dbcur.execute("select InitSpatialMetadata();")
    dbcur.execute("commit ;")

    print 'Creating the Node table ...'
    dbcur.execute("""
    CREATE TABLE "Node" (
    "node" INTEGER NOT NULL PRIMARY KEY,
    "osmid" BIGINT NOT NULL,
    "x" REAL DEFAULT 0,
    "y" REAL DEFAULT 0,
    "z" REAL DEFAULT 0);
    """)
    dbcur.execute("select AddGeometryColumn ( 'Node', 'GEO', ?, 'POINT', 2 );", [4326])
    dbcur.execute("select CreateMbrCache ( 'Node', 'GEO' );")

    print 'Creating the Link table ...'
    dbcur.execute("""
    CREATE TABLE "Link" (
    "link" INTEGER NOT NULL PRIMARY KEY,
    "osmid" BIGINT NOT NULL,
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
    """)

    dbcur.execute("select AddGeometryColumn ( 'LINK', 'GEO', ?, 'LINESTRING', 2 );", [4326])
    dbcur.execute("select CreateMbrCache ( 'LINK', 'GEO' );")

    print 'Creating the AC Nodes table ...'
    dbcur.execute("""
    CREATE TABLE "AcNodes" (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "osmid" BIGINT NOT NULL,
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
    """)

    dbcur.execute("select AddGeometryColumn ( 'AcNodes', 'GEO', ?, 'POINT', 2 );", [4326])
    dbcur.execute("select CreateMbrCache ( 'AcNodes', 'GEO' );")

    print 'Creating the AC Links table ...'
    dbcur.execute("""
    CREATE TABLE "AcLinks" (
    "id" INTEGER NOT NULL PRIMARY KEY,
    "osmid" BIGINT NOT NULL,
    "type" TEXT NOT NULL,
    "tag" TEXT NOT NULL);
    """)
    dbcur.execute("select AddGeometryColumn ( 'AcLinks', 'GEO', ?, 'POLYGON', 'XY' );", [4326])
    dbcur.execute("select CreateMbrCache ( 'AcLinks', 'GEO' );")

    print 'Loading the Node table ...'
    dbcon.commit()
    dbcur.execute("begin")

    for Node in NewNodes:
        Lon, Lat, Count, GId = NewNodes[Node]
        GeoString = 'POINT(' + str(Lon) + ' ' + str(Lat) + ')'
        SqlString = 'insert into Node values ( ?, ?, ?, ?, 0.0, Transform ( GeomFromText ( ?, 4326 ), 4326 ) );'
        dbcur.execute(SqlString, [GId, Node, Lon, Lat, GeoString])
    dbcur.execute("commit")

    print 'Updating X and Y coordinates of the Node table ...'
    SqlString = "update Node set X = X ( ST_Transform(GEO,?) ), Y = Y ( ST_Transform(GEO,?) );"
    dbcur.execute(SqlString, [EPSG, EPSG])
    dbcon.commit()

    print 'Loading the Link table ...'
    Counter = 0
    for Link in NewLinks:
        NodeA, NodeB, Group, Type, GeoString = NewLinks[Link]
        LanesAB = LanesBA = 1
        CapAB = CapBA = 500
        Name = ''
        SpeedAB = SpeedBA = 60 / 1.609
        if 'LANES' in Ways[Group]:
            try:
                LanesAB = int(Ways[Group]['LANES'])
                if LanesAB != 1:
                    LanesAB //= 2
                    LanesBA //= 2
            except ValueError:
                print 'Please, check data for way with OSM id ', Group, ' you have something strange' \
                                                                        ' in lanes: ', Ways[Group]['LANES']
                LanesAB = int(Ways[Group]['LANES'].split(';', 1)[0])
                if LanesAB != 1:
                    LanesAB //= 2
                    LanesBA //= 2
        if 'SPEED' in Ways[Group]:
            try:
                SpeedAB = SpeedBA = float(Ways[Group]['SPEED']) / 1.609
            except:
                print 'Please, check data for way with OSM id ', Group, ' you have something strange' \
                                                                        ' in speed: ', Ways[Group]['SPEED']
        if 'ONEWAY' in Ways[Group]:
            LanesBA = 0
            CapBA = 0
            SpeedBA = 0
            if (LanesAB != 1) & ('LANES' in Ways[Group]):
                try:
                    LanesAB = int(Ways[Group]['LANES'])
                except ValueError:
                    print 'Please, check data for way with OSM id ', Group, ' you have something strange' \
                                                                            ' in lanes: ', Ways[Group]['LANES']
                    LanesAB = int(Ways[Group]['LANES'].split(';', 1)[0])
        if 'NAME' in Ways[Group]:
            Name = Ways[Group]['NAME']
        SqlString = "insert into LINK values ( ?, ?, ?, ?, ?, 0.0, 0.0, 0.0, 0, 0, ?, 'ANY', ?, ?, 25.0," \
                    " ?, ?, ?, 25.0, ?, 0, 0, 0, 0, Transform ( GeomFromText ( ?, 4326 ), 4326 ) );"
        dbcur.execute(SqlString,
                      [Link, Group, Name, Nodes[NodeA][3], Nodes[NodeB][3], LinkType[Type], LanesAB, SpeedAB, CapAB,
                       LanesBA, SpeedBA, CapBA, GeoString])
        Counter += 1
    dbcon.commit()

    print 'Updating the Length fields in the Link table ...'
    dbcur.execute("update LINK set LENGTH = GLength ( GEO, 1 );")
    dbcon.commit()

    #AC locations
    print 'Loading the AcNodes table ...'
    for node in AC:
        Lon, Lat, Tag, Type, GId = AC[node]
        GeoString = 'POINT(' + str(Lon) + ' ' + str(Lat) + ')'
        SqlString = "insert into AcNodes values ( ?, ?, 0, 0, 0.0, 'AUTO/BUS/WALK', ?, ?, 0.0, ?, ?, 'POI', Transform ( GeomFromText ( ?, 4326 ), 4326 ) );"
        dbcur.execute(SqlString, [GId, node, Lon, Lat, Type, Tag, GeoString])

    print 'Loading the AcLinks table ...'
    for link in AcWay:
        GeoString = 'POLYGON(('
        for Node in AcWay[link]['NODES']:
            Lon, Lat = AllNodes[Node][0:2]
            GeoString += str(Lon) + ' ' + str(Lat) + ','
        GeoString = GeoString[:-1] + '))'
        Type = AcWay[link]['Type']
        Tag = AcWay[link]['Tag']
        GId = AcWay[link]['Id']
        SqlString = "insert into AcLinks values ( ?, ?, ?, ?, Transform ( GeomFromText ( ?, 4326 ), 4326 ) );"
        try:
            dbcur.execute(SqlString, [GId, link, Type, Tag, GeoString])
        except:
            print 'Error with:', link, Type, Tag, GeoString
    dbcon.commit()

    print 'Updating AcNodes from centroids of AcLinks'

    # dbcur.execute("SELECT max(id) FROM AcNodes;")
    #for row in dbcur.fetchall():
    #    MAX_N = int(row[0])

    dbcur.execute("SELECT id, osmid, type, tag, ST_Centroid(GEO) FROM AcLinks;")
    for row in dbcur.fetchall():
        #MAX_N += 1
        GId = row[0]
        OSMId = row[1]
        Type = row[2]
        Tag = row[3]
        GeoString = row[4]
        SqlString = "insert into AcNodes values ( ?, ?, 0, 0, 0.0, 'AUTO/BUS/WALK', 0.0, 0.0, 0.0, ?, ?, 'Centroid', ? );"
        dbcur.execute(SqlString, [GId, OSMId, Type, Tag, GeoString])
    dbcon.commit()

    print 'Updating easting and northing coordinates of the AcNode tables ...'
    SqlString = "update AcNodes set easting = X ( ST_Transform(GEO,?) ), northing = Y ( ST_Transform(GEO,?) );"
    dbcur.execute(SqlString, [EPSG, EPSG])
    dbcon.commit()

    print 'Finding the nearest neighbourhood of AC Nodes and Links'
    dbcur.execute("begin ;")
    query = 'select t1.id, t2.node_a, t2.link, Min(Distance(t1.GEO, t2.GEO)) from AcNodes as t1, Link as t2 group by t1.id;'
    dbcur.execute(query)

    result = dbcur.fetchall()
    dbcur.execute("commit ;")
    dbcur.execute("begin ;")
    for row in result:
        SqlString = 'UPDATE AcNodes SET node = ?, link = ? WHERE id = ? ;'
        dbcur.execute(SqlString, [row[1], row[2], row[0]])
    dbcur.execute("commit")

    print 'Updating the offset of AC Nodes'
    query = 'select t1.node, t1.x, t1.y, t2.ROWID, t2.node, t2.easting, t2.northing from AcNodes as t2, Node as t1 where t1.node=t2.node  order by t1.node;'
    dbcur.execute(query)
    result = dbcur.fetchall()
    for row in result:
        SqlString = 'UPDATE AcNodes SET offset = ? WHERE ROWID = ? ;'
        dbcur.execute(SqlString, [math.sqrt((row[5] - row[1]) ** 2 + (row[6] - row[2]) ** 2), row[3]])

    #print results
    print 'Obtain TRANSIMS nodes file'
    SqlString = "Select node, x, y, z from Node;"
    dbcur.execute(SqlString)
    dbcon.commit()
    with open(outfile + ".nodes.txt", "w") as out:
        out.write("%s\t%s\t%s\t%s\n" % ('node', 'x', 'y', 'z'))
        for row in dbcur.fetchall():
            out.write("%d\t%f\t%f\t%f\n" % (row[0], row[1], row[2], row[3]))
    out.close()
    print 'Obtain TRANSIMS links file'
    SqlString = "Select link, name, node_a, node_b, length, type, lanes_ab, speed_ab, cap_ab, " \
                "lanes_ba, speed_ba, cap_ba, use from Link;"
    dbcur.execute(SqlString)
    dbcon.commit()
    with open(outfile + ".links.txt", "w") as out:
        out.write(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format('LINK', 'STREET', 'ANODE', 'BNODE', 'LENGTH',
                                                                          'type', 'lanes_ab', 'speed_ab', 'cap_ab',
                                                                          'lanes_ba', 'speed_ba', 'cap_ba', 'use'))
        for row in dbcur.fetchall():
            out.write(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(row[0], row[1].encode('utf-8'), row[2],
                                                                              row[3], row[4], row[5], row[6], row[7],
                                                                              row[8], row[9], row[10], row[11], row[12]))
    out.close()
    print 'Obtain TRANSIMS AL file'
    SqlString = "Select id, node, link, layer, offset, easting, northing, elevation, tag, notes from AcNodes;"
    dbcur.execute(SqlString)
    dbcon.commit()
    with open(outfile + ".al.txt", "w") as out:
        out.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
        'id', 'node', 'link', 'layer', 'offset', 'easting', 'northing', 'elevation', 'tag', 'notes'))
        for row in dbcur.fetchall():
            out.write("%d\t%d\t%d\t%s\t%f\t%f\t%f\t%f\t%s\t%s\n" % (
            row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
    out.close()
# ----------------------------------------------------
# parsing procedure
# ----------------------------------------------------
Counter = 0
NodeErrors = 0
# стандартная штука из мануала
# http://effbot.org/zone/element-iterparse.htm
Context = ET.iterparse(infile)
Conext = iter(Context)
Event, Root = Context.next()
GlobalId = 0
# узлы, третий параметр - чтобы понять скольким линкам принадлежит узел
for Event, Child in Context:
    GlobalId +=1
    if Child.tag == 'node':
        # Subs = [Sub.tag for Sub in Child]
        Id = int(Child.attrib['id'])
        Lon = Child.attrib['lon']
        Lat = Child.attrib['lat']
        Nodes[Id] = [Lon, Lat, 0, GlobalId]  # 3 параметр для УДС
        for Sub in Child:
            if Sub.tag == 'tag':
                # if Sub.attrib['k'] == 'amenity' and Sub.attrib['v'] in AmenityType:
                if Sub.attrib['k'] == 'amenity':
                    AC[Id] = [Lon, Lat, 'Amenity', Sub.attrib['v'], GlobalId]
                # if Sub.attrib['k'] == 'shop' and Sub.attrib['v'] in ShopType:
                if Sub.attrib['k'] == 'shop':
                    AC[Id] = [Lon, Lat, 'Shop', Sub.attrib['v'], GlobalId]
                if Sub.attrib['k'] == 'leisure':
                    AC[Id] = [Lon, Lat, 'Leisure', Sub.attrib['v'], GlobalId]
                if Sub.attrib['k'] == 'office':
                    AC[Id] = [Lon, Lat, 'Office', Sub.attrib['v'], GlobalId]
                if Sub.attrib['k'] == 'shop':
                    AC[Id] = [Lon, Lat, 'Shop', Sub.attrib['v'], GlobalId]
        Child.clear()
        Subs = []
    # линии - пока еще не линки графа, а просто osm way
    if Child.tag == 'way':
        Id = int(Child.attrib['id'])
        Ways[Id] = {}
        Ways[Id]['NODES'] = []
        for Sub in Child:
            if Sub.tag == 'nd':
                Node = int(Sub.attrib['ref'])
                try:
                    Nodes[Node][2] += 1  # отмечаем ноды в линках.
                    Ways[Id]['NODES'].append(Node)
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
                    Ways[Id]['ONEWAY'] = Sub.attrib['v']  # может быть no вместо null
                if Sub.attrib['k'] == 'name':
                    Ways[Id]['NAME'] = Sub.attrib['v']
                if Sub.attrib['k'] == 'lanes':
                    Ways[Id]['LANES'] = Sub.attrib['v']
                if Sub.attrib['k'] == 'maxspeed':
                    Ways[Id]['SPEED'] = Sub.attrib['v']
                    # if Sub.attrib['k'] == 'shop' and Sub.attrib['v'] in ShopType:
                if Sub.attrib['k'] == 'shop':
                    AcWay[Id] = {}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Shop'
                    AcWay[Id]['Id'] = GlobalId
                # if Sub.attrib['k'] == 'amenity' and Sub.attrib['v'] in AmenityType:
                if Sub.attrib['k'] == 'amenity':
                    AcWay[Id] = {}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Amenity'
                    AcWay[Id]['Id'] = GlobalId
                if Sub.attrib['k'] == 'leisure':
                    AcWay[Id] = {}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Leisure'
                    AcWay[Id]['Id'] = GlobalId
                if Sub.attrib['k'] == 'office':
                    AcWay[Id] = {}
                    AcWay[Id]['NODES'] = Ways[Id]['NODES']
                    AcWay[Id]['Type'] = Sub.attrib['v']
                    AcWay[Id]['Tag'] = 'Office'
                    AcWay[Id]['Id'] = GlobalId
        if 'TYPE' not in Ways[Id]:
            del Ways[Id]
        Child.clear()
Root.clear()

print 'Removing unused nodes from the network ...'
UnusedNodes = []
for Node in Nodes:
    Lon, Lat, Count = Nodes[Node][0:3]
    if Count == 0:
        UnusedNodes.append(Node)
for Node in UnusedNodes:
    del Nodes[Node]
del UnusedNodes

print 'Splitting ways into links as needed ...'
Groups = {}
Links = {}
NewNodes = {}
#LinkId = 10001  # просто случайное число)) нужно аналогично придумать для нодов, а то не влазим в диапазон Int

for Id in Ways:
    ShapeCount = len(Ways[Id]['NODES'])
    if ShapeCount < 2:  # одна нода в way
        continue
    SegPos = 0
    Links[GlobalId] = {}
    Links[GlobalId]['NODES'] = []
    Links[GlobalId]['TYPE'] = Ways[Id]['TYPE']
    # настраиваем перелинковку Группа-Way-Link
    Links[GlobalId]['GROUP'] = Id
    Groups[Id] = [GlobalId]
    # здесь разбиваем way на отдельные сегменты.
    for Index in range(ShapeCount):
        Node = Ways[Id]['NODES'][Index]
        Lon, Lat, Count, GId = Nodes[Node][0:4]
        Links[GlobalId]['NODES'].append(Node)  # каждую ноду из вей добавляем в линкс
        if Index == 0 or Index == ShapeCount - 1:  # крайние точки
            if Node not in NewNodes:
                NewNodes[Node] = [Lon, Lat, 0, GId]  # пропускаем транзитные ноды (не добавляем в nodes)
            NewNodes[Node][2] += 1
        elif Count > 1:  # если нода в нескольких way - создаем новый way
            if SegPos > 0 and Index < ShapeCount - 1:
                SegPos = 0
                # создаем новый линк
                GlobalId += 1
                Links[GlobalId] = {}
                Links[GlobalId]['NODES'] = [Node]
                Links[GlobalId]['TYPE'] = Ways[Id]['TYPE']
                Links[GlobalId]['GROUP'] = Id
                Groups[Id].append(GlobalId)
                if Node not in NewNodes:
                    NewNodes[Node] = [Lon, Lat, 0, GId]
                NewNodes[Node][2] += 1
        SegPos += 1
    GlobalId += 1

print 'Checking the sanity of Node and Link relationships ...'
for Link in Links:
    Count = len(Links[Link]['NODES'])
    if Links[Link]['NODES'][0] not in NewNodes:
        print 'A-Node not found!', Link, Links[Link]['NODES'][0]
    elif Links[Link]['NODES'][Count - 1] not in NewNodes:
        print 'B-Node not found!', Link, Links[Link]['NODES'][-1]
    for Id in Links[Link]['NODES'][1:Count - 1]:
        if Id in NewNodes:
            print 'Shape point is also a node!', Link, Id

# финальная обработка
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
        GeoString += str(Lon) + ' ' + str(Lat) + ','
    GeoString = GeoString[:-1] + ')'
    NewLinks[Link] = [NodeA, NodeB, Group, Type, GeoString]
    if len(Links[Link]['NODES']) < 2:
        print '==> ERROR!', Link, NodeA, NodeB, Group, Type, GeoString

print 'OSM Ways:', len(Ways), '; OSM Nodes:', len(Nodes), '; Nodes:', len(NewNodes), '; NewLinks:', len(
    NewLinks), '; Groups:', len(Groups)

#incsv(NewNodes, NewLinks, Ways)

indb(NewNodes, NewLinks, Ways, Nodes, AC, AcWay)