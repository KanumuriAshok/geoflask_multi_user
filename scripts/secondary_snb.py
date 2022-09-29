"""
Model exported as python.
Name : secondary_snb
Group : 
With QGIS : 32403
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
from config import *
from processing.script import ScriptUtils



class Secondary_snb(QgsProcessingAlgorithm):

    
    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        
        results = {}
        outputs = {}

        # snboundary
        alg_params = {
            'aerialdp': parameters['adp'],
            'gaistdata': parameters['gaist'],
            'lndbnry': parameters['landboundary'],
            'streetcenterline': parameters['streetline'],
            'topographiclines': parameters['topographic'],
            'undergrounddp': parameters['ugcluster'],
            'model:dp_clusters_1:new_clusters': parameters['Cluster'],
            'native:deleteholes_1:final_boundaries': parameters['Final_boudary']
        }
        outputs['Snboundary'] = processing.run('model:snboundary', alg_params)
        results['Cluster'] = outputs['Snboundary']['model:dp_clusters_1:new_clusters']
        results['Final_boudary'] = outputs['Snboundary']['native:deleteholes_1:final_boundaries']
        return results

obj = Secondary_snb()
res = obj.processAlgorithm({
    'Cluster': fr"{HOME_DIR}/{sys.argv[1]}/data output/new_clusters.shp",
    'Final_boudary':fr"{HOME_DIR}/{sys.argv[1]}/data output/final_boundaries.shp",
    'adp':fr"{HOME_DIR}/{sys.argv[1]}/data output/a_dp.shp",
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaistdata.shp",
    'landboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/lndbnry.shp",
    'streetline':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetcenterline.shp",
    'topographic':fr"{HOME_DIR}/{sys.argv[1]}/data_input/topographiclines.shp",
    'ugcluster':fr"{HOME_DIR}/{sys.argv[1]}/data output/cluster_output.shp"
})
print(res)