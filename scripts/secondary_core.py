import sys

from qgis.core import *
from qgis.analysis import QgsNativeAlgorithms

QgsApplication.setPrefixPath('C:/Program Files/QGIS 3.20.0/apps/qgis', True)
qgs = QgsApplication([], False)
qgs.initQgis()

# Add the path to processing so we can import it next
# sys.path.append(r'C:\OSGeo4W64\apps\qgis\python\plugins')
sys.path.append('C:/Program Files/QGIS 3.20.0/apps/qgis/python/plugins')
# Imports usually should be at the top of a script but this unconventional
# order is necessary here because QGIS has to be initialized first

import processing
from processing.core.Processing import Processing
from config import *
from processing.script import ScriptUtils

# Processing path for standalone - C:\Users\jyothy\AppData\Roaming\python\profiles\default\processing
# Processing path for desktop app - C:\Users\jyothy\AppData\Roaming\QGIS\QGIS3\profiles\default\processing

# Processing.initialize()
# print("[INFO] Folder for script algorithms:", ScriptUtils.scriptsFolders())
# print("[INFO] Script algorithms available:",
#     [s.displayName() for s in QgsApplication.processingRegistry().providerById("script").algorithms()])

class Secondary_core(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # CORE
        alg_params = {
            'feederring': parameters['feederring'],
            'native:extractbyexpression_2:highlighted': parameters['Highlighted'],
            'native:pointsalonglines_1:proposed_sj': parameters['Proposed_sj'],
            'native:pointsalonglines_2:fw4': parameters['Fw4']
        }
        outputs['Core_1'] = processing.run('model:core_1', alg_params)
        results['Fw4'] = outputs['Core_1']['native:pointsalonglines_2:fw4']
        results['Highlighted'] = outputs['Core_1']['native:extractbyexpression_2:highlighted']
        results['Proposed_sj'] = outputs['Core_1']['native:pointsalonglines_1:proposed_sj']
        return results
        
obj = Secondary_core()
res = obj.processAlgorithm({
    'feederring':fr"{HOME_DIR}/{sys.argv[1]}/data_input/feederring.shp",\
    'Highlighted':fr"{HOME_DIR}/{sys.argv[1]}/data output/highlighted.shp",\
    'Proposed_sj':fr"{HOME_DIR}/{sys.argv[1]}/data output/proposed_sj.shp",\
    'Fw4':fr"{HOME_DIR}/{sys.argv[1]}/data output/fw4.shp"
})
print(res)
