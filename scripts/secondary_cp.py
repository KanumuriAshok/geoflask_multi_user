"""
Model exported as python.
Name : secondary_cp
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


class Secondary_cp(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # cabinetplacement
        alg_params = {
            'gaist': parameters['gaist'],
            'nodepoints': parameters['nodepoints'],
            'native:snapgeometries_1:cabinets': parameters['Cabinets']
        }
        outputs['Cabinetplacement'] = processing.run('model:cabinetplacement', alg_params)
        results['Cabinets'] = outputs['Cabinetplacement']['native:snapgeometries_1:cabinets']
        return results

obj = Secondary_cp()
res = obj.processAlgorithm({
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaist.shp",
    'nodepoints':fr"{HOME_DIR}/{sys.argv[1]}/data output/Ugnode_sn.shp",
    'Cabinets':fr"{HOME_DIR}/{sys.argv[1]}/data output/cabinets.shp",
})
print(res)
