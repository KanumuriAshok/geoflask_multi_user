"""
Model exported as python.
Name : secondary_ar
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

class Secondary_ar(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # clustergrpouing_A
        alg_params = {
            'VERBOSE_LOG': False,
            'demandpoints': parameters['demand'],
            'streetlines': parameters['street'],
            'Cluster': parameters['Cluster'],
            'Est_nodes': parameters['Est_nodes'],
            'Out': parameters['Outlier']
        }
        outputs['Clustergrpouing_a'] = processing.run('script:clustergrpouing_A', alg_params)
        results['Cluster'] = outputs['Clustergrpouing_a']['Cluster']
        results['Est_nodes'] = outputs['Clustergrpouing_a']['Est_nodes']
        results['Outlier'] = outputs['Clustergrpouing_a']['Out']
        return results

obj = Secondary_ar()
res = obj.processAlgorithm({
    'demand':fr"{HOME_DIR}/{sys.argv[1]}/data_input/demandpoints.shp",
    'street':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetlines.shp",
    'Cluster':fr"{HOME_DIR}/{sys.argv[1]}/data output/cluster_output.shp",
    'Est_nodes':fr"{HOME_DIR}/{sys.argv[1]}/data output/nodes_output.shp",
    'Outlier':fr"{HOME_DIR}/{sys.argv[1]}/data output/outlier_output.shp"
})
print(res)
