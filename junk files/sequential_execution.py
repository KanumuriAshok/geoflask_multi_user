import subprocess
qgis_int = r"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
subprocess.run(f'{qgis_int} "C:/Users/jyothy/Desktop/New folder/geoflask/main_process.py" ')
subprocess.run(f'python "C:/Users/jyothy/Desktop/New folder/geoflask/databse_commit.py" ')