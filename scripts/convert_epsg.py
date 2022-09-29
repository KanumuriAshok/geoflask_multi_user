import fiona
import os
import geopandas as gpd
for subdir, dirs, files in os.walk("."):
        for file in files:
            if(file.endswith(".shp")):
                print(file)
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"
                
                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf.crs)
