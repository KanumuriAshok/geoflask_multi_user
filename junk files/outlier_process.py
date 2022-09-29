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

class Outlier(QgsProcessingAlgorithm):


    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # outlierjoin
        alg_params = {
            'cluster': parameters['cluster'],
            'outlier': parameters['outlier'],
            'native:joinattributestable_2:trial': parameters['Outlier']
        }
        outputs['Outlierjoin'] = processing.run('model:outlierjoin', alg_params)
        results['Outlier'] = outputs['Outlierjoin']['native:joinattributestable_2:trial']
        return results

obj = Outlier()
res = obj.processAlgorithm({
    'cluster':r"C:\Users\jyothy\Desktop\New folder\geoflask\outlier_input\cluster_output.shp",
    'outlier':r"C:\Users\jyothy\Desktop\New folder\geoflask\outlier_input\outlier_output.shp",
    'Outlier':r"C:\Users\jyothy\Desktop\New folder\geoflask\outlier_output\joined_output.shp"
})
print(res)