"""
Model exported as python.
Name : arcombi
Group : 
With QGIS : 31604
"""
import sys
from qgis.core import *
sys.path.append('C:/Program Files/QGIS 3.20.0/apps/qgis/python/plugins')
import processing
from processing.core.Processing import Processing
QgsApplication.setPrefixPath('C:/Program Files/QGIS 3.20.0/apps/qgis', True)
qgs = QgsApplication([], False)
qgs.initQgis()

class Arcombi(QgsProcessingAlgorithm):


    def processAlgorithm(self, parameters):
        Processing.initialize()
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingFeedback()
        results = {}
        outputs = {}

        # aerial_UPDATED
        alg_params = {
            'demandpoints': parameters['demand'],
            'streetlines': parameters['street'],
            'native:extractbyexpression_1:shortest_path': QgsProcessing.TEMPORARY_OUTPUT,
            'script:min_max_kmeans2_1:cluster': parameters['Cluster'],
            'script:min_max_kmeans2_1:nodes': parameters['Nodes']
        }
        outputs['Aerial_updated'] = processing.run('model:aerial_UPDATED', alg_params)
        results['Cluster'] = outputs['Aerial_updated']['script:min_max_kmeans2_1:cluster']
        results['Nodes'] = outputs['Aerial_updated']['script:min_max_kmeans2_1:nodes']
        return results
obj = Arcombi()
res = obj.processAlgorithm({
    'demand':r"C:\Users\jyothy\Desktop\New folder\geoflask\data_input\1in_demandpoints.shp",
    'street':r"C:\Users\jyothy\Desktop\New folder\geoflask\data_input\1in_streetcenterlines.shp",
    'Cluster':r"C:\Users\jyothy\Desktop\New folder\geoflask\data output\Cluster.shp",
    'Nodes':r"C:\Users\jyothy\Desktop\New folder\geoflask\data output\Nodes.shp"
})
print(res)

