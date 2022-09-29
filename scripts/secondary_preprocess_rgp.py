"""
Model exported as python.
Name : secondary_preprocess_rgp
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
from processing.script import ScriptUtils
from config import *

class Secondary_preprocess_rgp(QgsProcessingAlgorithm):

    
    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # preprocess_rgp
        alg_params = {
            'gaist': parameters['gaist'],
            'piastructures': parameters['piastructures'],
            'pnboundary': parameters['pnboundary'],
            'rawgooglepoles': parameters['rawgooglepoles'],
            'native:extractbylocation_3:poles_at_5mtrs': parameters['Poles_at_5mtrs'],
            'native:snapgeometries_1:googlepoles': parameters['Googlepoles']
        }
        outputs['Preprocess_rgp'] = processing.run('model:preprocess_rgp', alg_params)
        results['Googlepoles'] = outputs['Preprocess_rgp']['native:snapgeometries_1:googlepoles']
        results['Poles_at_5mtrs'] = outputs['Preprocess_rgp']['native:extractbylocation_3:poles_at_5mtrs']
        return results

obj = Secondary_preprocess_rgp()
res = obj.processAlgorithm({
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaist.shp",
    'piastructures':fr"{HOME_DIR}/{sys.argv[1]}/data_input/piastructures.shp",
    'pnboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pnboundary.shp",
    'rawgooglepoles':fr"{HOME_DIR}/{sys.argv[1]}/data_input/citygooglepoles.shp",
    'Poles_at_5mtrs':fr"{HOME_DIR}/{sys.argv[1]}/data output/poles_at_5mtrs.shp",
    'Googlepoles':fr"{HOME_DIR}/{sys.argv[1]}/data output/googlepoles.shp",
})
print(res)