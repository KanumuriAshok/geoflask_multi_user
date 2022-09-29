"""
Model exported as python.
Name : secondary_structures
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


class Secondary_clusterbndry(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # clusterbndry_hybrid_v1
        alg_params = {
            'demandpoints': parameters['demandpoints'],
            'landboundary': parameters['landboundary'],
            'referenceline': parameters['referenceline'],
            'streetcenterlines': parameters['streetcenterlines'],
            'topographiclines': parameters['topographiclines'],
            'native:fixgeometries_1:cluster_bndry': parameters['Cluster_bndry'],
            'native:extractbylocation_2:mdu': parameters['Mdu']
        }
        outputs['Clusterbndry_hybrid_v1'] = processing.run('model:clusterbndry_hybrid_v1', alg_params)
        results['Cluster_bndry'] = outputs['Clusterbndry_hybrid_v1']['native:fixgeometries_1:cluster_bndry']
        results['Mdu'] = outputs['Clusterbndry_hybrid']['native:extractbylocation_2:mdu']
        return results

obj = Secondary_clusterbndry()
res = obj.processAlgorithm({
    'demandpoints':fr"{HOME_DIR}/{sys.argv[1]}/data output/preprocessed_dp.shp",
    'landboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/landboundary.shp",
    'referenceline':fr"{HOME_DIR}/{sys.argv[1]}/data_input/referenceline.shp",
    'streetcenterlines':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetcenterlines.shp",
    'topographiclines':fr"{HOME_DIR}/{sys.argv[1]}/data_input/topographiclines.shp",
    'Cluster_bndry':fr"{HOME_DIR}/{sys.argv[1]}/data output/cluster_bndry.shp",
    'Mdu':fr"{HOME_DIR}/{sys.argv[1]}/data output/Mdu.shp",
})
print(res)