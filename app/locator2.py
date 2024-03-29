from decimal import Overflow
from enum import auto
from inspect import signature
from app import app
import folium
import re
import sqlite3
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from folium.plugins import Fullscreen, MarkerCluster
from flask import render_template, request


@app.route('/form2/mapping/')
def mapping2():

    #database to local dataframe
    conn = sqlite3.connect('ats.sqlite')

    ATS = pd.read_sql_query("SELECT * FROM ats", con=conn)
    directory = pd.read_sql_query("SELECT * FROM directory", con=conn)
    wellProperties = pd.read_sql_query("SELECT * FROM wellProperties", con=conn)
    conn.close()

    #UWI input string processing
    input_uwi = request.args.get('input_uwi')

    input_UWI = input_uwi.split('-')

    LSD = input_UWI[0]
    sc = input_UWI[1]
    twp = input_UWI[2]

    last = re.split("w", input_UWI[3], flags=re.IGNORECASE)
    rg = last[0]
    M = last[1]

    UWI_number = [int(M),int(rg),int(twp),int(sc),int(LSD)]

    display  = request.args.get('display')
    display = int(display)

    #property display selection value assignmnet
    lithology = request.args.get('lithology')
    in_situ  = request.args.get('insitu')
    mechanical  = request.args.get('mechanical')


    if lithology is None:
        lithology = 0
    else:
        lithology = int(lithology)

    if in_situ is None:
        in_situ = 0
    else:
        in_situ = int(in_situ)

    if mechanical is None:
        mechanical = 0
    else:
        mechanical= int(mechanical)

    #sectional ATS numpy matrix
    arr = np.arange(1,37)
    arr = np.sort(arr)[::-1]
    arr = arr.reshape(6,6)
    df = pd.DataFrame(arr)
    df.iloc[0::2,:] = df.iloc[0::2,::-1]

    array = df.to_numpy()

    #SOME FUNCTIONS FOR UWI STRING MANIPULATION
    def lsdToQuarter(UWI):
        """ Associate the legal subdivision to the adjacent quarter section corner. If position 
            is bottom left, print the section.
        """
        
        # sort subdivision
        lsd = UWI[4]

        if (lsd == 2 or lsd == 3 or lsd == 6):
            UWI[4] = 'S4'
        elif (lsd == 10 or lsd == 11 or lsd == 13 or lsd == 14 or lsd == 15):
            UWI[4] = 'N4'
        elif (lsd == 1 or lsd == 7 or lsd == 8 or lsd == 9):
            UWI[4] = 'E4'
        elif (lsd == 4 or lsd == 5 or lsd == 12):
            UWI[4] = 'W4'
        elif (lsd == 16):
            UWI[4] = 'NE'
            
        #sort section
        sc = UWI[4]
        
        if (sc == 'S4'):
            result = np.where(array == UWI[3])
        elif (sc == 'W4'):
            result = np.where(array == UWI[3])
        else:
            result = 100
            
        return UWI, result

    def new_coordinate(coord, UWI_):
        """ a function to rename the section of a location based input index applied to matrix of 36 sections
        """
        tp = UWI_[4]
        if coord == 100:
            y1 = 100
            x1 = 100
            
        else:
            x1 = int(coord[0])
            y1 = int(coord[1])
        
            if tp == 'S4':
                if x1 == 5:
                    tp = 'E4'
                else:
                    x1 += 1
                    tp = 'N4'

        
            elif tp == 'W4':
                if y1 == 0:
                    tp = 'N4'
            
                else:
                    y1 = y1 - 1
                    tp = 'E4'
        
        UWI_[4] = tp
        x = x1
        y = y1
        
        return UWI_, x, y

    def ListToString(list_form):
        """ A function to convert from list to string
        """
        median = str(list_form[0])

        range_str = str(list_form[1])
        UWIrg = range_str.zfill(2)
        
        township_str = str(list_form[2])
        township = township_str.zfill(3)
        
        section_str = str(list_form[3])
        section = section_str.zfill(2)
        
        qs = str(list_form[4])
        
        wellID = median + UWIrg + township + section + qs
        
        return(wellID)

    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    # #MAIN TERMINAL CODE...more uwi manipulation
    UWI_list = UWI_number

    UWI, co = lsdToQuarter(UWI_list)

    UWI, x, y = new_coordinate(co, UWI)

    # call on the matrix and output the number at that index, assign as new section
    if x == 100:
        pass

    else:
        new_sc = array[x,y]
        UWI[3] = new_sc
        
    UWI_ID = ListToString(UWI)

    ATS.loc[ATS['UWI'] == UWI_ID]

    input_coord = ATS.loc[ATS['UWI'] == UWI_ID]
    lati1 = float(input_coord.iloc[0]['Latitude'])
    long1 = float(input_coord.iloc[0]['Longitude'])

    for index, row in directory.iterrows():
        directory.loc[index, "Distance (km)"] = haversine(long1, lati1, row['Longitude'], row['Latitude'])
        
    # sort the distance values in ascending order, closest well site to furthest well site
    directory = directory.sort_values(by = ['Distance (km)'],
                        axis = 0,
                        ascending = True)

    # Implementing Folium Map
    m = folium.Map(location=[55,-115], tiles =None,
                    zoom_start=6)

    # map tiles - light map, satellite, topography, alberta geoJson
    borderStyle={
        'fillOpacity': 0.1,
        'weight': 1,
        'color': 'black'
    }

    folium.GeoJson("alberta.geojson", 
                    name="Alberta",
                    style_function=lambda x:borderStyle).add_to(m)
    folium.TileLayer("https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png", 
                 name = 'Light Map',
                 attr= 'Stadia Maps').add_to(m)
    folium.TileLayer('https://api.maptiler.com/maps/outdoor/{z}/{x}/{y}.png?key=D1R440GkNxYWsQt9rTf3', 
                 name = 'Topography',
                 attr= 'OpenTopo').add_to(m)
    folium.TileLayer('https://api.maptiler.com/maps/hybrid/256/{z}/{x}/{y}.jpg?key=D1R440GkNxYWsQt9rTf3', 
                 name = 'Satellite',
                 attr= 'Esri_WorldImagery').add_to(m)


    #df column with rounded numbers and units
    directory['Print Distance']=directory['Distance (km)']
    directory['Print Distance']=directory['Print Distance'].round(decimals=2)
    directory['Print Distance']=directory['Print Distance'].astype(str) + ' km'
    directory

    df_well_locations = directory.copy()
    df_well_locations['Longitude']*= -1
    df_well_locations = df_well_locations.drop(columns=['Directory', 'LSD','SC','TWP','RG','W','M','adjusted_UWI','Distance (km)','Print Distance', 'stress'])
    
    # df_well_locations
    well_location_list = df_well_locations.values.tolist()
    well_location_list_size = len(well_location_list)
    
    # depths = []

    #MARKERS, if over a threshold, start clustering well markers
    if display <= 30:
        for point in range(0, display):
            #Creating a new dataframe that is a subset of a well site, just different properties at different depths
            wellInformation = wellProperties[wellProperties["Directory"]==directory.iloc[point]['Directory']]
            wellInformation = wellInformation.assign(A = lambda x: x['Depth'].str.extract('(\d+)'))
            wellInformation = wellInformation.reset_index()
            wellInformation = wellInformation.drop('index',axis = 1)

            wellInformation['A'] = wellInformation['A'].astype('int') 
            wellInformation = wellInformation.sort_values(by = ['A'],
                            axis = 0,
                            ascending = True)  

            dist=True
            print_dist=directory.iloc[point]['Print Distance']

            lith=False
            situ=False
            mech=False
            depth = 0
            index = 0
            type = 0
            description = 0
            add_notes = 0
            shmin =0
            shmax =0
            sv = 0
            temp = 0
            pp = 0 
            youngs = 0
            shear = 0
            bulk = 0
            poisson = 0
            cohesive = 0
            friction = 0
            pWave = 0
            sWave = 0

            nm=directory.iloc[point]['Directory']

            if (mechanical==1 or lithology==1 or in_situ==1):
                depth = wellInformation['Depth'].tolist()
                index = len(depth)

            if lithology==1:
                lith=True
                type = wellInformation['Type'].tolist()
                description = wellInformation['Description'].tolist()
                add_notes = wellInformation['AdditionalNotes'].tolist()

            if in_situ==1:
                situ=True
                shmin = wellInformation['Shmin'].tolist()
                shmax = wellInformation['Shmax'].tolist()
                sv = wellInformation['VerticalStress'].tolist()
                temp = wellInformation['Temperature'].tolist()
                pp = wellInformation['PorePressure'].tolist()

            if mechanical==1:
                mech=True
                youngs = wellInformation['YoungsModulus'].tolist()
                shear = wellInformation['ShearModulus'].tolist()
                bulk = wellInformation['BulkModulus'].tolist()
                poisson = wellInformation['PoissonsRatio'].tolist()
                cohesive = wellInformation['CohesiveStrength'].tolist()
                friction = wellInformation['FrictionAngle'].tolist()
                pWave = wellInformation['pWave'].tolist()
                sWave = wellInformation['sWave'].tolist()

            html = render_template("popupTable.html", nm=nm, dist=dist, print_dist=print_dist, index=index,
                lith=lith, depth=depth, type=type, description=description, add_notes=add_notes,
                situ=situ, shmin=shmin, shmax=shmax, sv=sv, temp=temp, pp=pp,
                mech=mech, youngs=youngs, shear=shear, bulk=bulk, poisson=poisson, cohesive=cohesive, friction=friction, pWave=pWave, sWave=sWave)
            popup_table = folium.Popup(folium.Html(html, script=True), max_width=500)
            folium.Marker(well_location_list[point],
                        icon=folium.Icon(icon='glyphicon-star', icon_color='white', color='green'),
                        tooltip=directory.iloc[point]['Directory'],
                        popup=popup_table).add_to(m)
    
    else:
        marker_cluster = MarkerCluster(name="Clusters").add_to(m)
        for point in range(0, well_location_list_size):
            #Creating a new dataframe that is a subset of a well site, just different properties at different depths
            wellInformation = wellProperties[wellProperties["Directory"]==directory.iloc[point]['Directory']]
            wellInformation = wellInformation.assign(A = lambda x: x['Depth'].str.extract('(\d+)'))
            wellInformation = wellInformation.reset_index()
            wellInformation = wellInformation.drop('index',axis = 1)

            wellInformation['A'] = wellInformation['A'].astype('int') 
            wellInformation = wellInformation.sort_values(by = ['A'],
                            axis = 0,
                            ascending = True)         

            dist=True
            print_dist=directory.iloc[point]['Print Distance']

            lith=False
            situ=False
            mech=False
            depth = 0
            index = 0
            type = 0
            description = 0
            add_notes = 0
            shmin =0
            shmax =0
            sv = 0
            temp = 0
            pp = 0 
            youngs = 0
            shear = 0
            bulk = 0
            poisson = 0
            cohesive = 0
            friction = 0
            pWave = 0
            sWave = 0

            nm=directory.iloc[point]['Directory']

            if (mechanical==1 or lithology==1 or in_situ==1):
                depth = wellInformation['Depth'].tolist()
                index = len(depth)

            if lithology==1:
                lith=True
                type = wellInformation['Type'].tolist()
                description = wellInformation['Description'].tolist()
                add_notes = wellInformation['AdditionalNotes'].tolist()

            if in_situ==1:
                situ=True
                shmin = wellInformation['Shmin'].tolist()
                shmax = wellInformation['Shmax'].tolist()
                sv = wellInformation['VerticalStress'].tolist()
                temp = wellInformation['Temperature'].tolist()
                pp = wellInformation['PorePressure'].tolist()

            if mechanical==1:
                mech=True
                youngs = wellInformation['YoungsModulus'].tolist()
                shear = wellInformation['ShearModulus'].tolist()
                bulk = wellInformation['BulkModulus'].tolist()
                poisson = wellInformation['PoissonsRatio'].tolist()
                cohesive = wellInformation['CohesiveStrength'].tolist()
                friction = wellInformation['FrictionAngle'].tolist()
                pWave = wellInformation['pWave'].tolist()
                sWave = wellInformation['sWave'].tolist()

            html = render_template("popupTable.html", nm=nm, dist=dist, print_dist=print_dist, index=index,
                lith=lith, depth=depth, type=type, description=description, add_notes=add_notes,
                situ=situ, shmin=shmin, shmax=shmax, sv=sv, temp=temp, pp=pp,
                mech=mech, youngs=youngs, shear=shear, bulk=bulk, poisson=poisson, cohesive=cohesive, friction=friction, pWave=pWave, sWave=sWave)
            popup_table = folium.Popup(folium.Html(html, script=True), max_width=300)
            folium.Marker(well_location_list[point],
                        icon=folium.Icon(icon='glyphicon-star', icon_color='white', color='green'),
                        tooltip=directory.iloc[point]['Directory'],
                        popup=popup_table).add_to(marker_cluster)

    inputLong =long1*-1

    #circular area marker for location of interest
    folium.Circle(
        radius=50000,
        location=[lati1,inputLong],
        tooltip="50km radius",
        color="cadetblue",
        fill=True,
    ).add_to(m)

    folium.Marker(location=[lati1,inputLong],
                    tooltip=UWI_ID,
                    icon=folium.Icon(icon='glyphicon-star', color='cadetblue'),
                    ).add_to(m)

    folium.LayerControl().add_to(m) #add layer selection ability
    fs = Fullscreen()
    m.add_child(fs)  # adding fullscreen button to map

    return m._repr_html_()