"""
Model exported as python.
Name : secondary_pre_gp
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
from config import *
from processing.script import ScriptUtils



class Secondary_pre_gp(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # preprocess_gp
        alg_params = {
            'gaist': parameters['gaistdata'],
            'googlePoles': parameters['rawgooglepoles'],
            'piastructurepoles': parameters['piastructure'],
            'pnboundary': parameters['pnboundary'],
            'native:extractbylocation_2:flagged': parameters['Flagged_poles'],
            'qgis:deletecolumn_2:updated_gp': parameters['Updated_gp']
        }
        outputs['Preprocess_gp'] = processing.run('model:preprocess_gp', alg_params)
        results['Flagged_poles'] = outputs['Preprocess_gp']['native:extractbylocation_2:flagged']
        results['Updated_gp'] = outputs['Preprocess_gp']['qgis:deletecolumn_2:updated_gp']
        return results

obj = Secondary_pre_gp()
res = obj.processAlgorithm({
    'Flagged_poles': fr"{HOME_DIR}/{sys.argv[1]}/data output/flagged.shp",
    'Updated_gp':fr"{HOME_DIR}/{sys.argv[1]}/data output/updated_gp.shp",
    'pnboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pnboundary.shp",
    'gaistdata':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaistdata.shp",
    'rawgooglepoles':fr"{HOME_DIR}/{sys.argv[1]}/data_input/googlepoles.shp",
    'piastructure':fr"{HOME_DIR}/{sys.argv[1]}/data_input/piastructurepoles.shp",
    
})
print(res)