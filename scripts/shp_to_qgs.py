from xml.dom.minidom import Document
import string
import os
import sys

import requests
from qgis.core import *
from qgis.gui import *
from config import *
import geopandas
# from PyQt4.QtCore import *
# from PyQt4.QtGui import QApplication
# from PyQt4.QtXml import *


#Read input parameters from GP dialog
# from python.qgis import core

qgs = QgsApplication([], False)
QgsApplication.setPrefixPath('C:/Program Files/QGIS 3.20.3/apps/qgis', True)
QgsApplication.initQgis()

strProjetName = fr"{HOME_DIR}/{sys.argv[1]}/data output/qgs_output.qgs"

try:
    os.remove(strProjetName)
except Exception as msg:
    print(msg)
project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:27700"))

for shpfile in os.listdir(fr"{HOME_DIR}/{sys.argv[1]}/data output"):
    if(shpfile.endswith(".shp")):
        #data = geopandas.read_file(shpfile)
        # change CRS to epsg 4326
        #data = data.to_crs(epsg=27700)
        # write shp file
        #data.to_file(shpfile)
        vlayer = QgsVectorLayer(fr"{HOME_DIR}/{sys.argv[1]}/data output/{shpfile}", shpfile[:-4], "ogr")
        vlayer.loadSldStyle(fr"{HOME_DIR}/data output/sld/sample_flask_{shpfile[:-4]}.sld")

        project.addMapLayer(vlayer)

service_url = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
service_uri = "type=xyz&zmin=0&zmax=21&url=" + requests.utils.quote(service_url)
tms_layer = QgsRasterLayer(service_uri, "Google Hybrid", "wms")
project.addMapLayer(tms_layer)
project.write(strProjetName)