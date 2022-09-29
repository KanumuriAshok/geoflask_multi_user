import subprocess
import os
os.environ['PATH'] += r';C:\Program Files\PostgreSQL\14\bin'
user = "postgres"
password = "postgres"
host = "localhost"
port = 5432
database = "UAT"
table_name = "sample_flask_cluster_output"
filepath_cluster_output = r"C:\Users\jyothy\Desktop\New folder\geoflask\data output\cluster_output"
query = f"SELECT * FROM {table_name}"

cmds = 'pgsql2shp -f "'+ filepath_cluster_output + f'" -h {host} -u {user} -P {password} {database} "'+ query + '"'
        
print(cmds)
subprocess.call(cmds, shell=True)