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
from processing.script import ScriptUtils

# Processing path for standalone - C:\Users\jyothy\AppData\Roaming\python\profiles\default\processing
# Processing path for desktop app - C:\Users\jyothy\AppData\Roaming\QGIS\QGIS3\profiles\default\processing

# Processing.initialize()
# print("[INFO] Folder for script algorithms:", ScriptUtils.scriptsFolders())
# print("[INFO] Script algorithms available:",
#     [s.displayName() for s in QgsApplication.processingRegistry().providerById("script").algorithms()])

class Combi(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # NODEBOUNDARY
        alg_params = {
            'cluster': parameters['cluster'],
            'plotboundary': parameters['boundary'],
            'model:lrnb_1:clean': QgsProcessing.TEMPORARY_OUTPUT,
            'native:extractbyexpression_1:FINAL BOUNDARY': parameters['Final']
        }
        outputs['Nodeboundary'] = processing.run('model:NODEBOUNDARY', alg_params)
        results['Final'] = outputs['Nodeboundary']['native:extractbyexpression_1:FINAL BOUNDARY']
        return results


obj = Combi()
res = obj.processAlgorithm({
    'cluster':r"C:\Users\jyothy\Desktop\New folder\geoflask\data output\cluster_output.shp",
    'boundary':r"C:\Users\jyothy\Desktop\New folder\geoflask\data_input\landbndry.shp",
    'Final':r"C:\Users\jyothy\Desktop\New folder\geoflask\data output\nodeboundary_output.shp"
})
print(res)

