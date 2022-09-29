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

class Secondary_preprocessgp(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # preprocess_gp
        alg_params = {
            'gaist': parameters['gaist'],
            'piastructures': parameters['piastructures'],
            'pnboundary': parameters['pnboundary'],
            'rawgooglepoles': parameters['rawgooglepoles'],
            'native:extractbylocation_2:poles_at_5mtrs': parameters['Poles_at_5mtrs'],
            'qgis:deletecolumn_2:googlepoles': parameters['Googlepoles']
        }
        outputs['Preprocess_gp'] = processing.run('model:preprocess_gp', alg_params)
        results['Googlepoles'] = outputs['Preprocess_gp']['qgis:deletecolumn_2:googlepoles']
        results['Poles_at_5mtrs'] = outputs['Preprocess_gp']['native:extractbylocation_2:poles_at_5mtrs']
        return results

obj = Secondary_preprocessgp()
res = obj.processAlgorithm({
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaist.shp",
    'piastructures':fr"{HOME_DIR}/{sys.argv[1]}/data_input/piastructures.shp",
    'pnboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pnboundary.shp",
    'rawgooglepoles':fr"{HOME_DIR}/{sys.argv[1]}/data_input/rawgooglepoles.shp",
    'Googlepoles':fr"{HOME_DIR}/{sys.argv[1]}/data output/googlepoles.shp",
    'Poles_at_5mtrs':fr"{HOME_DIR}/{sys.argv[1]}/data output/poles_at_5mtrs.shp",
})
print(res)
