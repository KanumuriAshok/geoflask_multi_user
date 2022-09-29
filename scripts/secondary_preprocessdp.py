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
# Processing path for standalone - C:\Users\jyothy\AppData\Roaming\python\profiles\default\processing
# Processing path for desktop app - C:\Users\jyothy\AppData\Roaming\QGIS\QGIS3\profiles\default\processing

# Processing.initialize()
# print("[INFO] Folder for script algorithms:", ScriptUtils.scriptsFolders())
# print("[INFO] Script algorithms available:",
#     [s.displayName() for s in QgsApplication.processingRegistry().providerById("script").algorithms()])


class Secondary_preprocessdp(QgsProcessingAlgorithm):

    
    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # missingdemandpoints
        alg_params = {
            'cartograpgictext': parameters['cartograpgictext'],
            'demandpoints': parameters['demandpoints'],
            'gaist': parameters['gaist'],
            'landboundary': parameters['landboundary'],
            'streetcenterline': parameters['streetcenterline'],
            'topographicline': parameters['topographicline'],
            'native:mergevectorlayers_3:preprocessed_dp': parameters['Preprocessed_dp']
        }
        outputs['Missingdemandpoints'] = processing.run('model:missingdemandpoints', alg_params)
        results['Preprocessed_dp'] = outputs['Missingdemandpoints']['native:mergevectorlayers_3:preprocessed_dp']
        return results

obj = Secondary_preprocessdp()
res = obj.processAlgorithm({
    'cartograpgictext':fr"{HOME_DIR}/{sys.argv[1]}/data_input/cartograpgictext.shp",
    'demandpoints':fr"{HOME_DIR}/{sys.argv[1]}/data_input/demandpoints.shp",
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaist.shp",
    'landboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/landboundary.shp",
    'streetcenterline':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetcenterlines.shp",
    'topographicline':fr"{HOME_DIR}/{sys.argv[1]}/data_input/topographiclines.shp",
    'Preprocessed_dp':fr"{HOME_DIR}/{sys.argv[1]}/data output/preprocessed_dp.shp"
})
print(res)