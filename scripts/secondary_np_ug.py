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

class Secondary_np(QgsProcessingAlgorithm):

    
    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # nodeplacement_ug
        alg_params = {
            'VERBOSE_LOG': False,
            'cluster': parameters['cluster'],
            'existing': parameters['existing'],
            'gaist': parameters['gaist'],
            'landboundary': parameters['landboundary'],
            'nodes': parameters['node'],
            'On_existing': parameters['Existing'],
            'Proposed': parameters['Proposed']
        }
        outputs['Nodeplacement_ug'] = processing.run('script:nodeplacement_ug', alg_params)
        results['Existing'] = outputs['Nodeplacement_ug']['On_existing']
        results['Proposed'] = outputs['Nodeplacement_ug']['Proposed']
        return results

obj = Secondary_np()
res = obj.processAlgorithm({
    'cluster':fr"{HOME_DIR}/{sys.argv[1]}/data output/cluster_output.shp",
    'existing':fr"{HOME_DIR}/{sys.argv[1]}/data_input/1pia_structures.shp",
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/1cityfibre_lincoln_2021.shp",
    'landboundary':fr"{HOME_DIR}/{sys.argv[1]}/data_input/1Land_Registry_Cadastral_Parcels_PREDEFINED.shp",
    'node':fr"{HOME_DIR}/{sys.argv[1]}/data output/nodes_output.shp",
    'Existing':fr"{HOME_DIR}/{sys.argv[1]}/data output/existing_output_ug.shp",
    'Proposed':fr"{HOME_DIR}/{sys.argv[1]}/data output/proposed_output_ug.shp"
})
print(res)