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

class Secondary_ref_bndry(QgsProcessingAlgorithm):

    
    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # ref_bndry
        alg_params = {
            'aerialdp': parameters['aerialdp'],
            'gaistdata': parameters['gaistdata'],
            'lndbnry': parameters['lndbnry'],
            'streetcenterline': parameters['streetcenterline'],
            'topographiclines': parameters['topographiclines'],
            'undergrounddp': parameters['undergrounddp'],
            'native:deleteholes_1:final_boundaries': parameters['Ref_bndry'],
            'native:fieldcalculator_3:new_clusters': parameters['Clusters']
        }
        outputs['Ref_bndry'] = processing.run('model:ref_bndry', alg_params)
        results['Clusters'] = outputs['Ref_bndry']['native:fieldcalculator_3:new_clusters']
        results['Ref_bndry'] = outputs['Ref_bndry']['native:deleteholes_1:final_boundaries']
        return results

obj = Secondary_ref_bndry()
res = obj.processAlgorithm({
    'aerialdp':fr"{HOME_DIR}/{sys.argv[1]}/data_input/aerialdp.shp",
    'gaistdata':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaistdata.shp",
    'lndbnry':fr"{HOME_DIR}/{sys.argv[1]}/data_input/lndbnry.shp",
    'streetcenterline':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetcenterline.shp",
    'topographiclines':fr"{HOME_DIR}/{sys.argv[1]}/data_input/topographiclines.shp",
    'undergrounddp':fr"{HOME_DIR}/{sys.argv[1]}/data_input/undergrounddp.shp",
    'Ref_bndry':fr"{HOME_DIR}/{sys.argv[1]}/data output/final_boundaries.shp",
    'Clusters':fr"{HOME_DIR}/{sys.argv[1]}/data output/new_clusters.shp"
})
print(res)
