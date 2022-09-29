"""
Model exported as python.
Name : secondary_pnb_fed_ug
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


class Secondary_pnb_fed_ug(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # pnb_fed_ug
        alg_params = {
            'piastructures': parameters['piastructures'],
            'pnboundary': parameters['pnboundary'],
            'native:fieldcalculator_1:pnboundary': parameters['Pnboundary']
        }
        outputs['Pnb_fed_ug'] = processing.run('model:pnb_fed_ug', alg_params)
        results['Pnboundary'] = outputs['Pnb_fed_ug']['native:fieldcalculator_1:pnboundary']
        return results

obj = Secondary_pnb_fed_ug()
res = obj.processAlgorithm({
    'piastructures':fr"{HOME_DIR}/{sys.argv[1]}/data_input/piastructures.shp",
    'pnboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pnboundary.shp",
    'Pnboundary':fr"{HOME_DIR}/{sys.argv[1]}/data output/pnboundary.shp",
})
print(res)