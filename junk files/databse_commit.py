from sqlalchemy import create_engine
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

#Sample shp - r'C:\Users\jyothy\Desktop\New folder\data output\nodeboundary_output.shp'
#shp2pgsql -> C:\Program Files\PostgreSQL\14\bin
user = "postgres"
password = "postgres"
host = "localhost"
port = 5432
database = "UAT"

def insert_to_postgis(shapefile,table_name):
    global user,password,host,port,database
    print("Loading Data")
    pointDf = gpd.read_file(shapefile)
    print("Data Loaded")

    print("Creating Engine")
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    print("Posting Data")
    try:
        pointDf["uprn"] = pd.to_numeric(pointDf["uprn"])
        pointDf["gistool_id"] = pd.to_numeric(pointDf["gistool_id"])
        pointDf.to_postgis(name=table_name, con=engine, schema="public",if_exists='replace')
        print("Success")
    except Exception as ms:
        print(f"Failed due to {ms}")
insert_to_postgis(r'C:\Users\jyothy\Desktop\New folder\geoflask\data output\nodeboundary_output.shp','sample_flask')