# import os
# from qgis.core import *
#
#
# #Read input parameters from GP dialog
# def add_layer(username):
#     QgsApplication.setPrefixPath(r"C:\Program Files\QGIS 3.24.3\apps\qgis", True)
#     qgs = QgsApplication([], False)
#     qgs.initQgis()
#     QgsProject.instance().setFileName(fr'C:\Users\jyothy\Desktop\New folder\geoflask_multi_user\{username}\data_input\map.qgs')
#
# # C:\Users\jyothy\Desktop\TestingforGQIS
# # C:\Users\jyothy\Desktop\New folder\geoflask_multi_user
# def changing(username, workspace):
#     for subdir, dirs, files in os.walk(fr"C:/Users/jyothy/Desktop/New folder/geoflask_multi_user/{username}/data_input"):
#         for file in files:
#             if (file.endswith(".shp")):
#                 layer = QgsVectorLayer(fr"C:/Users/jyothy/Desktop/New folder/geoflask_multi_user/{username}/data_input"
#                                        + r"\\" + file, file, "ogr")
#                 # if layer.isValid():
#                 QgsProject.instance().addMapLayer(layer)
#     QgsProject.instance().write(
#         fr'C:\Users\jyothy\Desktop\New folder\geoflask_multi_user\{username}\data output\{workspace}.qgs')
#     QgsApplication.exitQgis()
#     add_layer(username)
#     return {
#         "status": 200
#     }
