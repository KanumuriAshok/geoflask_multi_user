"""
Model exported as python.
Name : sndry_snboundry
Group : 
With QGIS : 31616
"""

import sys

from qgis.core import *
from qgis.analysis import QgsNativeAlgorithms

QgsApplication.setPrefixPath('C:/Program Files/QGIS 3.20.0/apps/qgis', True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Add the path to processing so we can import it next
# sys.path.append(r'C:/OSGeo4W64/apps/qgis/python/plugins')
sys.path.append('C:/Program Files/QGIS 3.20.0/apps/qgis/python/plugins')
# Imports usually should be at the top of a script but this unconventional
# order is necessary here because QGIS has to be initialized first

import processing
from processing.core.Processing import Processing
from processing.script import ScriptUtils
from config import *

class Sndry_snboundry(QgsProcessingAlgorithm):

   

    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiFeedback()
        results = {}
        outputs = {}

        # snboundary
        alg_params = {
            'Landboundary': parameters['landboundary'],
            'aerialdp': parameters['aerialdp'],
            'gaistdata': parameters['gaistdata'],
            'streetcenterline': parameters['streetlines'],
            'topographiclines': parameters['topographiclines'],
            'undergrounddp': parameters['ugdp'],
            'model:dp_clusters_1:new_clusters': parameters['New_clusters'],
            'native:deleteholes_1:final_boundaries': parameters['Nodeboundary']
        }
        outputs['Snboundary'] = processing.run('model:snboundary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['New_clusters'] = outputs['Snboundary']['model:dp_clusters_1:new_clusters']
        results['Nodeboundary'] = outputs['Snboundary']['native:deleteholes_1:final_boundaries']
        return results

obj = Sndry_snboundry()
res = obj.processAlgorithm({
    'Nodeboundary': fr"{HOME_DIR}/{sys.argv[1]}/data output/nodeboundary.shp",
    'New_clusters': fr"{HOME_DIR}/{sys.argv[1]}/data output/new_clusters.shp",
    'Landboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/landboundary.shp",
    'aerialdp':fr"{HOME_DIR}/{sys.argv[1]}/data_input/aerialdp.shp",
    'gaistdata':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaistdata.shp",
    'streetlinese':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetlines.shp",
    'topographiclines':fr"{HOME_DIR}/{sys.argv[1]}/data_input/topographiclines.shp",
    'undergrounddp':fr"{HOME_DIR}/{sys.argv[1]}/data_input/undergrounddp.shp"
})
print(res)