"""
Model exported as python.
Name : secondary_pn_np
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

class Secondary_pn_np(QgsProcessingAlgorithm):


    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # pn_nodeplacement
        alg_params = {
            'gaist': parameters['gaist'],
            'piastructure': parameters['piastructure'],
            'pnboundary': parameters['pnboundary'],
            'pnnode': parameters['pnnode'],
            'native:snapgeometries_1:cabinet': parameters['Cabinet'],
            'native:snapgeometries_2:enclosure': parameters['Enclosure']
        }
        outputs['Pn_nodeplacement'] = processing.run('model:pn_nodeplacement', alg_params)
        results['Cabinet'] = outputs['Pn_nodeplacement']['native:snapgeometries_1:cabinet']
        results['Enclosure'] = outputs['Pn_nodeplacement']['native:snapgeometries_2:enclosure']
        return results

obj = Secondary_pn_np()
res = obj.processAlgorithm({
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaist.shp",
    'piastructure':fr"{HOME_DIR}/{sys.argv[1]}/data_input/piastructures.shp",
    'pnboundary':fr"{HOME_DIR}/{sys.argv[1]}/data output/pnboundary.shp",
    'pnnode':fr"{HOME_DIR}/{sys.argv[1]}/data_input/primarynodes.shp",
    'Cabinet':fr"{HOME_DIR}/{sys.argv[1]}/data output/pn_cabinet.shp",
    'Enclosure':fr"{HOME_DIR}/{sys.argv[1]}/data output/enclosure.shp",
})
print(res)