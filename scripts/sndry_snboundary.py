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
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # snboundary
        alg_params = {
            'lndbnry': parameters['lndbnry'],
            'aerialdp': parameters['aerialdp'],
            'gaistdata': parameters['gaistdata'],
            'streetcenterline': parameters['streetlines'],
            'topographiclines': parameters['topographiclines'],
            'undergrounddp': parameters['ugdp'],
            'model:dp_clusters_1:new_clusters': parameters['New_clusters'],
            'native:deleteholes_1:final_boundaries': parameters['Nodeboundary']
        }
        outputs['Snboundary'] = processing.run('model:snboundary', alg_params)
        results['New_clusters'] = outputs['Snboundary']['model:dp_clusters_1:new_clusters']
        results['Nodeboundary'] = outputs['Snboundary']['native:deleteholes_1:final_boundaries']
        return results

obj = Sndry_snboundry()
res = obj.processAlgorithm({
    'Nodeboundary':fr"{HOME_DIR}/{sys.argv[1]}/data output/final_boundaries.shp",\
    'New_clusters':fr"{HOME_DIR}/{sys.argv[1]}/data output/new_clusters.shp",\
    'lndbnry':fr"{HOME_DIR}/{sys.argv[1]}/data_input/lndbnry.shp",\
    'aerialdp':fr"{HOME_DIR}/{sys.argv[1]}/data_input/a_dp.shp",\
    'gaistdata':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaistdata.shp",\
    'ugdp':fr"{HOME_DIR}/{sys.argv[1]}/data output/cluster_output.shp",\
    'topographiclines':fr"{HOME_DIR}/{sys.argv[1]}/data_input/topographiclines.shp",\
    'streetlines':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetcenterline.shp",
})
print(res)