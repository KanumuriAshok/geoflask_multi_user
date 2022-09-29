"""
Model exported as python.
Name : secondary_structures
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

class Secondary_structures(QgsProcessingAlgorithm):


    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}
        
        print('parameters', parameters)
        # structures
        alg_params = {
            'googlepoles': parameters['googlepoles'],
            'piastructures': parameters['piastructures'],
            'native:fieldcalculator_2:structures': parameters['Structures']
        }
        print('alg_params', alg_params)
        outputs['Structures'] = processing.run('model:structures', alg_params)
        results['Structures'] = outputs['Structures']['native:fieldcalculator_2:structures']
        return results

obj = Secondary_structures()
res = obj.processAlgorithm({
    'googlepoles':fr"{HOME_DIR}/{sys.argv[1]}/data output/googlepoles.shp",
    'piastructures':fr"{HOME_DIR}/{sys.argv[1]}/data_input/piastructures.shp",
    'Structures':fr"{HOME_DIR}/{sys.argv[1]}/data output/structures.shp",
})
print(res)
