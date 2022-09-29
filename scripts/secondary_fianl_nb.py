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

class Secondary_fianl_nb(QgsProcessingAlgorithm):

    
    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # final_nb
        alg_params = {
            'gaistdata': parameters['gaistdata'],
            'landboundary': parameters['landboundary'],
            'streetcenterline': parameters['streetcenterline'],
            'topographiclines': parameters['topographiclines'],
            'updatedcluster': parameters['updatedcluster'],
            'native:deleteholes_1:final_boundaries': parameters['Final_boundary']
        }
        outputs['Final_nb'] = processing.run('model:final_nb', alg_params)
        results['Final_boundary'] = outputs['Final_nb']['native:deleteholes_1:final_boundaries']
        return results

obj = Secondary_fianl_nb()
res = obj.processAlgorithm({
    'gaistdata':fr"{HOME_DIR}/{sys.argv[1]}/data_input/gaistdata.shp",
    'landboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/landboundary.shp",
    'streetcenterline':fr"{HOME_DIR}/{sys.argv[1]}/data_input/streetcenterline.shp",
    'topographiclines':fr"{HOME_DIR}/{sys.argv[1]}/data_input/topographiclines.shp",
    'updatedcluster':fr"{HOME_DIR}/{sys.argv[1]}/data_input/updatedcluster.shp",
    'Final_boundary':fr"{HOME_DIR}/{sys.argv[1]}/data output/final_boundaries.shp"
})
print(res)
