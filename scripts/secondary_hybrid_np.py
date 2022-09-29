"""
Model exported as python.
Name : secondary_hybrid_np
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


class Secondary_hybrid_np(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # hybrid_nodeplacement
        # hybrid_nodeplacement
        alg_params = {
            'clusterboundary': parameters['clusterboundary'],
            'gaist': parameters['gaist'],
            'googlepoles': parameters['googlepoles'],
            'piastructure': parameters['piastructure'],
            'native:snapgeometries_1:ugnode_sn': parameters['Ugnode_sn'],
            'native:snapgeometries_2:proposedpoles_asn': parameters['Proposedpoles_asn'],
            'native:snapgeometries_3:existingpoles_asn': parameters['Existingpoles_asn']
        }
        outputs['Hybrid_nodeplacement'] = processing.run('model:hybrid_nodeplacement', alg_params)
        results['Existingpoles_asn'] = outputs['Hybrid_nodeplacement']['native:snapgeometries_3:existingpoles_asn']
        results['Proposedpoles_asn'] = outputs['Hybrid_nodeplacement']['native:snapgeometries_2:proposedpoles_asn']
        results['Ugnode_sn'] = outputs['Hybrid_nodeplacement']['native:snapgeometries_1:ugnode_sn']
        return results

obj = Secondary_hybrid_np()
res = obj.processAlgorithm({
    'clusterboundary':fr"{HOME_DIR}/{sys.argv[1]}/data output/cluster_bndry.shp",
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaist.shp",
    'googlepoles':fr"{HOME_DIR}/{sys.argv[1]}/data output/googlepoles.shp",
    'piastructure':fr"{HOME_DIR}/{sys.argv[1]}/data_input/piastructures.shp",
    'Existingpoles_asn':fr"{HOME_DIR}/{sys.argv[1]}/data output/existingpoles_asn.shp",
    'Proposedpoles_asn':fr"{HOME_DIR}/{sys.argv[1]}/data output/proposedpoles_asn.shp",
    'Ugnode_sn':fr"{HOME_DIR}/{sys.argv[1]}/data output/Ugnode_sn.shp",
})
print(res)