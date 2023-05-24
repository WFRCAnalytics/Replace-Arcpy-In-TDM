# Author: Justin Culp coded and Andy Li added Toll zone functions
# Date: 12/06/2016
#
# Description: This script makes a copy of the network links and creates midpoints from these links. The link midpoints are
#              then used to spatial join with the TAZ. The spatial join is then used to update the TAZID in the network links shapefile. Next
#              the network nodes are spatial joined with the TAZ, then the spatil join in used to update the TAZID in the network nodes shapefile.
# Requires: ArcGIS 10.2 Desktop Basic
#
#
# Improvements: Josh Reynolds and Chris Day
#
# Description: We updated the script to use geopandas opposed to using the arcpy library.
#
# open cmd in this folder and run this command: C:\Users\cday\Anaconda3\python.exe 01_Update_HOT_gpd.py
#C:\Users\cday\AppData\Local\ESRI\conda\envs\arcgispro-py3-geopandas\python.exe 01_Update_HOT_gpd.py

# Import geopandas module
print("\nRunning Update HOTzone Python Script\n\n\n")
print("Importing geopandas site package...\n")
import geopandas as gpd
import sys
import os
import imp
import time
import traceback

tollz_shp = r'inputs-04-14\\Tollz_shp.shp'
Scenario_Link = r'inputs-04-14\\C2_Link.shp'
Scenario_Node = r'inputs-04-14\\C2_Node.shp'
UsedZones = '3629'
temp_folder = r'temp_gpd'
log = os.path.join(temp_folder,r'LogFile_UpdateHOT.txt')

# Print key variabls to screen
print("tollz_shp: \n    "         + tollz_shp      + "\n")
print("Scenario_Link: \n    "     + Scenario_Link     + "\n")
print("Scenario_Node: \n    "     + Scenario_Node     + "\n")
print("UsedZones: \n    "         + str(UsedZones)    + "\n")
print("Temp Folder:  \n    "      + temp_folder       + "\n")

# Open log file
logFile = open(log, 'w')
logFile.write(tollz_shp+'\n')
logFile.write(Scenario_Link+'\n')
logFile.write(Scenario_Node+'\n')
logFile.write(str(UsedZones)+'\n')
logFile.write(temp_folder+'\n')

#raw_input()


## Define Variables
# Variables: Input
tollz_shp         = str(tollz_shp)
link_shp          = str(Scenario_Link)
node_shp          = str(Scenario_Node)
UsedZones         = str(UsedZones)
temp_folder       = str(temp_folder)

# Variables: Intermediate
link_taz_sj       = os.path.join(temp_folder, "Link_TAZ_SJ_deleteTemp.shp")
node_taz_sj       = os.path.join(temp_folder, "Node_TAZ_SJ_deleteTemp.shp")

# Variables: Output
out_link2         = os.path.join(temp_folder, "C1_Link_HOT.shp")
out_node2         = os.path.join(temp_folder, "C1_Node_HOT.shp")
out_link_mp       = os.path.join(temp_folder, "C1_Link_Midponts.shp")

# Codeblock to calculate HOTzone
def calctollzoneID_Node(tazid, node, global_n):
    if node <= int(global_n):
        return 0
    else:
        return tazid
def calctollzoneID_Link(tazid, aField, bField, global_n):
    return tazid

# Geoprocessing steps
def TagLinksWithtollzoneID():
    print("\n\nImporting Highway Link data...")
    gdf_link = gpd.read_file(link_shp)

    print("\nCalculating Highway Link midpoint coord and updating X_MID & Y_MID fields...")
    gdf_link["X_MID"] = gdf_link.geometry.interpolate(0.5, normalized=True).x
    gdf_link["Y_MID"] = gdf_link.geometry.interpolate(0.5, normalized=True).y
    gdf_link.to_file(out_link2)

    print("\nMaking new point shapefile from Highway Link midpoint...")
    gdf_midpoints = gdf_link.copy()
    gdf_midpoints = gdf_midpoints.set_geometry(gdf_midpoints.geometry.centroid)
    gdf_midpoints.to_file(out_link_mp)

    print("\nSpatial joining Tollz_shp to Link midpoints (this may take a few minutes)...")
    gdf_tollz = gpd.read_file(tollz_shp)
    gdf_link_taz_sj = gpd.sjoin(gdf_midpoints, gdf_tollz, how="left", op="within")

    print("\nUpdating Highway Link HOTZONE ID...\n")
    # it seems like this creates a Link_TAZ_SJ_deleteTemp file that is different from arcpy 
    # (if I skip this step however, it is the same as the arcpy version. why is that?)
    gdf_link_taz_sj["HOT_ZONEID"] = gdf_link_taz_sj.apply(lambda row: calctollzoneID_Link(row["EL_Zone"], row["A"], row["B"], UsedZones), axis=1) 
    gdf_link_taz_sj = gdf_link_taz_sj
    gdf_link_taz_sj.to_file(link_taz_sj)



def TagNodesWithTollzoneID() :
    print("\n\nImporting Highway Node data for joining toll zone purpose..")
    gdf_node = gpd.read_file(node_shp)

    print("\nSpatial joining Tollzone shape to Highway Nodes (this may take a few minutes)...")
    gdf_tollz = gpd.read_file(tollz_shp)
    gdf_node_tollz = gpd.sjoin(gdf_node, gdf_tollz, how="left", op="within")

    print("\nUpdating Highway Node TollzoneID...\n")
    gdf_node_taz_sj = gdf_node_tollz
    gdf_node_taz_sj["HOT_ZONEID"] = gdf_node_taz_sj.apply(lambda row: calctollzoneID_Node(row["EL_Zone"], row["N"], UsedZones), axis=1) 
    gdf_node_taz_sj.to_file(node_taz_sj)


def Main():
    try:
        print("\n\nRunning script...")
        print("Start Time: " + time.strftime('%X %x %Z')+"\n")
        TagLinksWithtollzoneID()
        TagNodesWithTollzoneID()        
        print("Script End Time: " + time.strftime('%X %x %Z'))
        logFile.write("All Finished"+"\n")
        logFile.write("Script End Time: " + time.strftime('%X %x %Z'))
        logFile.close()
    except:
        print("*** There was an error running this script - Check output logfile.")
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "\nPYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info())
        msgs = "\nGeopandas ERRORS:\n" + str(sys.exc_info()[1]) + "\n"
        logFile.write(pymsg + "\n")
        logFile.write(msgs + "\n")
        sys.exit(1)

Main()




