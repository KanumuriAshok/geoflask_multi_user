import subprocess
import os
import time
os.environ['PATH'] += r';C:\Program Files\PostgreSQL\14\bin'
os.environ['PGPASSWORD'] = 'postgres'
shapefile_list = [r"C:\Users\jyothy\Desktop\geoflask\sample data\cluster1.shp"]
sql = "select pg_terminate_backend(pid) from pg_stat_activity where client_addr = '127.0.0.1';"
cmds = f'psql -U postgres -w -c "{sql}"'
CREATE_NO_WINDOW = 0x08000000

while(True):
    pro = subprocess.Popen(cmds, shell=False,creationflags = CREATE_NO_WINDOW) 
    time.sleep(2)
    pro.kill()