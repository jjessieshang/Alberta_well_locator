# :earth_americas: Alberta_well_locator

## Project Description
The Alberta Well Locator Program is a data visualisation tool that allows the user to interact with BitCan’s directory of well sites. Given any input [Unique Well Identifier](https://www.rigworker.com/well/appendix-unique-well-identifier.html) (UWI), the web app maps the point of interest, calculates the distance between the input UWI and all existing well sites, and displays rock lithology, in-situ, and mechanical properties associated with each well.

**Tools Used:** Flask, Folium, Python (Pandas, NumPy), SQLite

## :ballot_box_with_check: Data
Using Pandas and NumPy, I plotted the [Alberta Dominion Land Survey Grid](https://chinookpetroleum.com/alberta-township-system/) as a planar projection and utilized the [Alberta Township System (ATS) version 4.1 (NAD83)](https://open.alberta.ca/opendata/property-alberta-township-system-ats) dataset to convert the entire set of Unique Well Identifier Numbers to geographical coordinates. This mapping tool then computes the distance between well locations by applying the [Haversine Formula](https://www.geeksforgeeks.org/haversine-formula-to-find-distance-between-two-points-on-a-sphere/) for great-circle distance. 


## The Map
The input UWI is displayed as a blue marker and a circle with a radius representing 50 km on the map. Each green marker represents a well location from the database, the name is displayed when the user hovers over it.

<img width="900" alt="Screen Shot 2022-10-08 at 1 00 39 PM" src="https://user-images.githubusercontent.com/105069660/194726200-ab1a18fe-36db-47f8-ae84-11f874604b73.png">

## Map Features
Map Tiles            |  Scrollable Popup
:-------------------------:|:-------------------------:
![Screen Shot 2022-10-08 at 1 12 34 PM](https://user-images.githubusercontent.com/105069660/194726245-01260241-30ec-4fc1-bf81-6f839bb6b15c.png  ) |  <img width="558" alt="Screen Shot 2022-10-08 at 1 21 47 PM" src="https://user-images.githubusercontent.com/105069660/194726548-11512bbe-1593-46d2-857b-dc1870625048.png">

| Feature  | Description |
| :--------------------- | :------------- |
| Distance               | Distance between searched UWI and the well, measured in kilometers.|
| Depth                  | Data entries are sorted in ascending order based on depth.|
| Rock Lithology         | Rock type, description, and additional notes |
| In-Situ                | Stress (minimum and maximum horizontal stress, vertical stress), temperature, and pore pressure.|
| Mechanical Properties  | Static (Young’s modulus, Bulk’s modulus, Shear modulus, Poisson’s ratio, cohesive strength, friction angle), and dynamic (P-wave, S-wave).|

## Database Manipulation

The Alberta Well Locator Program uses a SQLite file database which is connected to the front-end of the web application. From the front end you can interact with the database in the following ways:

1.	View BitCan’s directory of well locations
2.	Add new well locations
3.	Add/Edit/Delete properties of each well location

<img width="600" alt="Screen Shot 2022-10-08 at 1 20 44 PM" src="https://user-images.githubusercontent.com/105069660/194726516-34a14c1f-6a3f-484d-980a-d862f0898fc5.png">

## Future Developments
Expanding the Well Locator to BitCan's well sites in an Indonesia-based project. 
Tasks
1. Find comprehensive geographical coordinate dataset to create planar model of Indonesia
2. Work with stakeholders to determine well properties of interest
3. Develop tangential mapping tool
