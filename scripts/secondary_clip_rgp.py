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


class Secondary_clip_rgp(QgsProcessingAlgorithm):


    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # clip_rgp
        alg_params = {
            'pnboundary': parameters['pnboundary'],
            'rawgooglepoles': parameters['rawgooglepoles'],
            'native:clip_1:rawgooglepoles': parameters['Rawgooglepoles']
        }
        outputs['Clip_rgp'] = processing.run('model:clip_rgp', alg_params)
        results['Rawgooglepoles'] = outputs['Clip_rgp']['native:clip_1:rawgooglepoles']
        return results

obj = Secondary_clip_rgp()
res = obj.processAlgorithm({
    'pnboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pnboundary.shp",
    'rawgooglepoles':fr"{HOME_DIR}/{sys.argv[1]}/data_input/citygooglepoles.shp",
    'Rawgooglepoles':fr"{HOME_DIR}/{sys.argv[1]}/data output/rawgooglepoles.shp",
})
print(res)
