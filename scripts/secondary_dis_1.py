"""
Model exported as python.
Name : secondary_dis_1
Group : 
With QGIS : 31604
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


class Secondary_dis_1(QgsProcessingAlgorithm):

    def processAlgorithm(self, parameters):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # distribution_1005
        alg_params = {
            'existingducts': parameters['existingducts'],
            'existingstructures': parameters['existingstructures'],
            'gaist': parameters['gaist'],
            'primarynodes': parameters['primarynodes'],
            'proposednodes': parameters['proposednodes'],
            'native:extractbyexpression_1:usable_existing_ducts': parameters['Usable_existing_ducts'],
            'native:shortestpathpointtolayer_1:proposed_duct': parameters['Proposed_ducts']
        }
        outputs['Distribution_1005'] = processing.run('model:distribution_1005', alg_params)
        results['Proposed_ducts'] = outputs['Distribution_1005']['native:shortestpathpointtolayer_1:proposed_duct']
        results['Usable_existing_ducts'] = outputs['Distribution_1005']['native:extractbyexpression_1:usable_existing_ducts']
        return results

obj = Secondary_dis_1()
res = obj.processAlgorithm({
    'existingducts':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pia_ducts.shp",
    'existingstructures':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pia_structures.shp",
    'gaist':fr"{HOME_DIR}/{sys.argv[1]}/data_input/cityfibre_lincoln_2021.shp",
    'primarynodes':fr"{HOME_DIR}/{sys.argv[1]}/data_input/pn.shp",
    'proposednodes':fr"{HOME_DIR}/{sys.argv[1]}/data_input/proposed.shp",
    'Usable_existing_ducts':fr"{HOME_DIR}/{sys.argv[1]}/data output/usable_existing_ducts.shp",
    'Proposed_ducts':fr"{HOME_DIR}/{sys.argv[1]}/data output/proposed_ducts.shp"
})
print(res)
