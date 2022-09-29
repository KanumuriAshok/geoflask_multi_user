import json
import os
import shutil

from flask import Flask, flash, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename, send_file
from sqlalchemy import create_engine
import geopandas as gpd
import zipfile
import subprocess
from flask_cors import CORS
from geo.Geoserver import Geoserver
import pandas as pd
import psycopg2
import time
from waitress import serve
from config import *
from geoserver_crud import *
from flask_sqlalchemy import SQLAlchemy
# from scripts.shapefile_to_qgs import changing
from schema import create_schema
import jwt
from pathlib import Path
from utils import save_input_in_dir, copy_files
user = "postgres"
password = "postgres"
host = "localhost"
port = 5432
database = "UAT"
CURRENT_TYPE = dict()
#connections = "psql -U postgres -c "SELECT pid, (SELECT pg_terminate_backend(pid)) as killed from pg_stat_activity WHERE datname = 'my_database_to_alter';"
# Initialize the library
#postgres to shp - [pgsql2shp -f "{HOME_DIR}/data output\cluster_output" -h localhost -u postgres -P postgres UAT "SELECT * FROM {username}_sample_flask_cluster_output"]
#reference - https://gis.stackexchange.com/questions/55206/how-can-i-get-a-shapefile-from-a-postgis-query
#select pg_terminate_backend(pid) from pg_stat_activity where state = 'idle' and state_change<='now()'

#TO RUN -
#Terminate pythonw instance
#activate virtualenv - C:\Users\jyothy\vecv\Scripts\activate
#go to app.py directory - pythonw app.py
os.environ['PATH'] += r';C:\Program Files\PostgreSQL\14\bin'
# http://www.postgresql.org/docs/current/static/libpq-envars.html
os.environ['PGHOST'] = 'localhost'
os.environ['PGPORT'] = '5432'
os.environ['PGUSER'] = 'postgres'
os.environ['PGPASSWORD'] = 'postgres'
os.environ['PGDATABASE'] = 'UAT'

UPLOAD_FOLDER = fr'{HOME_DIR}'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','shp','zip','cpg','dbf','qmd','shx','prj'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/UAT'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'
My_SECRET_STRING = "AccuracySecretKey"
db = SQLAlchemy(app)
SQLALCHEMY_TRACK_MODIFICATIONS = True
CORS(app, resource={fr"*" : {"origins":"*"}})
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
GLOBAL_WORKSPACENAME = ''


class Userregister(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    schemaname = db.Column(db.String(128), nullable=False, unique=True)

    def __init__(self, username, password, schemaname):
        self.username = username
        self.password = password
        self.schemaname = schemaname



def terminate_connections():
    try:
        #'shp2pgsql "' + shapefile_list[0] + '" node_boundary | psql '
        #sql = "SELECT pid, (SELECT pg_terminate_backend(pid)) as killed from pg_stat_activity WHERE datname = 'UAT';"
        subprocess.run(f'python "{HOME_DIR}/scripts/test_postgres.py" ')
        return True
    except:
        return False

def generate_random_workspace():
    curr_time = int(time.time()*1000)
    workspaceName = "NODE_" + str(curr_time)
    set_workspace(workspaceName)
    return workspaceName

def set_workspace(data):
    GLOBAL_WORKSPACENAME = data

def get_workspace():
    return GLOBAL_WORKSPACENAME

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def remove_table(table_name):
    try:
        #terminate_connections()
        conn = psycopg2.connect(
           database=database, user=user, password=password, host=host, port= port
        )
        conn.autocommit = True

        cursor = conn.cursor()
        sql = f'DROP TABLE IF EXISTS {table_name}' #keeping constant for now
        cursor.execute(sql)
        conn.commit()
        conn.close()
        #terminate_connections()
        return {
            "status":"PASS"
        }

    except Exception as msg:
        try:

            conn.close()
            #terminate_connections()
        except:
            pass
        return  {
            "status":"PASS",
            "Error":msg
        }
def generate_outliers(lo,hi,username):

    try:
        check = Userregister.query.filter_by(username=username).first()
        schema = check.schemaname
        #terminate_connections()
        conn = psycopg2.connect(
           database=database, user=user, password=password, host=host, port= port
        )
        conn.autocommit = True

        cursor = conn.cursor()
        sql = f'DROP TABLE IF EXISTS {schema}.{username}_sample_flask_outlier_output' #keeping constant for now
        cursor.execute(sql)
        conn.commit()

        sql = f'select cluster_id,sum(pon_homes) as tot_pon into {schema}.{username}_sample_flask_outlier_output from {schema}.{username}_sample_flask_cluster_output group by cluster_id having sum(pon_homes) > {hi} or sum(pon_homes) < {lo}'
        cursor.execute(sql)
        conn.commit()

        sql = f'DROP TABLE IF EXISTS {schema}.{username}_sample_flask_joined_cluster_id'  # keeping constant for now
        cursor.execute(sql)
        conn.commit()

        sql = f'''
        SELECT  s.gid ,
            s.identifier ,
            s.pon_homes,
            s.p2p_homes,
            s.loc_issue,
            s.loc_desc,
            s.qc_check,
            s.include,
            s.exc_reason,
            s.connection,
            s.cfh_type,
            s.prop_type ,
            s.forced_cbl ,
            s.uprn ,
            s.category,
            s.cat_type ,
            s.org_name,
            s.bld_name,
            s.bld_name2 ,
            s.bld_num ,
            s.streetname ,
            s.postcode,
            s.pon_m_rev,
            s.p2p_m_rev ,
            s.rfs_status,
            s.bldg_id,
            s.gistool_id,
            s.hubname ,
            s.indexed ,
            s.cluster_id ,
            s.geom,
            o.tot_pon
        into {schema}.{username}_sample_flask_joined_cluster_id FROM {schema}.{username}_sample_flask_cluster_output s
        INNER JOIN {schema}.{username}_sample_flask_outlier_output o
        ON s.cluster_id = o.cluster_id group by s.cluster_id,s.gid
        ,o.cluster_id,o.tot_pon;
        '''
        cursor.execute(sql)
        conn.commit()
        #Closing the connection
        conn.close()
        #terminate_connections()
        return {
            "Status":"PASS"
        }
    except Exception as msg:
        try:
            conn.close()
            #terminate_connections()
        except:
            pass
        return {
            "Status":"FAILED",
            "Error":msg
        }
@app.route('/dashboard', methods=['POST'])
def dashboard():
    username = json.loads(request.data)["username"]
    if not os.path.exists(fr'{HOME_DIR}/{username}'):
        os.makedirs(fr'{HOME_DIR}/{username}')
        os.makedirs(fr'{HOME_DIR}/{username}/data_input')
        os.makedirs(fr'{HOME_DIR}/{username}/data output')
        print(str(Path.home() / "Default"))
        copy_files(str(Path.home() / "Default"), fr'{HOME_DIR}/{username}/data output')
    return "OK"
@app.route('/nb_page', methods=['GET', 'POST'])
def nb_page():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('landbndry'):
            # f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
            # if 'file' not in request.files:
            #     flash('No file part')
            #     return redirect(request.url)
            # file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "landbndry"
            file.filename = ".".join(ls_name)
            print("Land Boundary File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        for file in request.files.getlist('demandpoints'):
            # f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
            # if 'file' not in request.files:
            #     flash('No file part')
            #     return redirect(request.url)
            # file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoints"
            file.filename = ".".join(ls_name)
            print("Demandpoints file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+fr"/{username}/data_input", filename))
        #terminate_connections()
        response = nb_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>Land Boundary</h1>
      <input type=file name=landbndry multiple>
      <h1>Demand Points</h1>
      <input type=file name=demandpoints multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/nb_update_db', methods=['GET', 'POST'])
def nb_update_db(userparam):
    print("working in nb_update_db")
    username = str(userparam)
    # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_nb.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if (file_[-3:] == 'shp') and (file_[:-4] == "nodeboundary_output"):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
    # terminate_connections()
    remove_table(f"{username}_node_boundary")
    # terminate_connections()

    cmds = 'shp2pgsql "' + shapefile_list[0] + f'"{username}_node_boundary | psql '  # shp2pgsql <shapefile_name> <new_table> | psql
    subprocess.call(cmds, shell=True)
    # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    print("***************************RUNNING***********************")
    curr_time = int(time.time() * 1000)
    workspaceName = "NODE_" + str(curr_time)
    # workspaceName = get_workspace()
    table_name = f"{username}_node_boundary"
    geo.create_workspace(workspace=workspaceName)
    x = geo.create_featurestore(store_name=table_name, workspace=workspaceName, db='UAT', host='localhost', port="5432",
                                pg_user='postgres',
                                pg_password='postgres')
    # print(x)
    geo.publish_featurestore(workspace=workspaceName, store_name=table_name, pg_table=table_name, srs_data="EPSG:27700")
    print("***************************EN--D***********************")
    print(os.path.join(os.getcwd(), "nodebndry.sld"))
    # geo.upload_style(path=os.path.join(os.getcwd(),"nodebndry.sld"), workspace=workspaceName)
    geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")

    print("***************************END***********************")
    # terminate_connections()
    return {
        "status": 200,
        "workspace": workspaceName,
        "sample_flask": table_name
    }


@app.route('/load_data', methods=['GET', 'POST'])
def load_data():
    global CURRENT_TYPE
    username = str(request.args.get("username"))
    current_type = CURRENT_TYPE[username]
    # terminate_connections()
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    if (current_type == "A"):
        df = pd.read_sql_query(
            f'select cluster_id,sum(pon_homes) as tot_pon from "{username}_sample_flask_cluster_output" group by cluster_id having sum(pon_homes) > 24 or sum(pon_homes) < 3',
            con=engine)
    else:
        df = pd.read_sql_query(
            f'select cluster_id,sum(pon_homes) as tot_pon from "{username}_sample_flask_cluster_output" group by cluster_id having sum(pon_homes) > 48 or sum(pon_homes) < 16',
            con=engine)
    engine.dispose()
    # terminate_connections()
    print(df)
    return {
        "status": 200,
        "cluster_id": list(df["cluster_id"].astype(str).values),
        "sum_pon_homes": list(df["tot_pon"].astype(str).values)
    }


@app.route('/update_db', methods=['GET', 'POST'])
def update_db():
    global CURRENT_TYPE
    if request.method == 'POST':
        username = request.form.get('username')
        current_type = CURRENT_TYPE[username]
        # terminate_connections()
        # check if the post request has the file part
        cluster_in = int(request.form["input_cluster_id"])
        cluster_out = int(request.form["output_cluster_id"])
        gis_tool_id = int(request.form["gis_tool_id"])

        print("Cluster_in", cluster_in)
        print("Cluster_out", cluster_out)
        print("GIS_tool_id", gis_tool_id)

        # IMPORT psycopg2
        # update db
        try:
            conn = psycopg2.connect(
                database=database, user=user, password=password, host=host, port=port
            )
            conn.autocommit = True

            cursor = conn.cursor()
            sql = f'UPDATE "{username}_sample_flask_cluster_output" SET "cluster_id" = {cluster_out} WHERE ("gistool_id" = {gis_tool_id}) AND ("cluster_id" = {cluster_in})'
            cursor.execute(sql)
            conn.commit()

            # Closing the connection
            conn.close()
            # terminate_connections()
            if (current_type == "A"):
                ver = generate_outliers(3, 24, username)
            else:
                ver = generate_outliers(16, 48, username)
            curr_time = int(time.time() * 1000)
            workspace_name = f"NODE_{curr_time}"
            # workspace_name = "NODE_555"
            table_name = f"{username}_sample_flask_cluster_output"
            geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
            geo.create_workspace(workspace=workspace_name)
            x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost',
                                        port="5432",
                                        pg_user='postgres',
                                        pg_password='postgres', loose_bbox="")
            print(x)
            geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,
                                     srs_data="EPSG:27700")
            geo.publish_style(layer_name=table_name, style_name='outlier', workspace=workspace_name,
                              srs_name="EPSG:27700")
            # terminate_connections()
        except Exception as msg:
            return {
                "Status": "FAILED",
                "Error": msg
            }

        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
        if (CURRENT_TYPE == "A"):
            df = pd.read_sql_query(
                f'select cluster_id,sum(pon_homes) as tot_pon from "{username}_sample_flask_cluster_output" group by cluster_id having sum(pon_homes) > 24 or sum(pon_homes) < 3',
                con=engine)
        else:
            df = pd.read_sql_query(
                f'select cluster_id,sum(pon_homes) as tot_pon from "{username}_sample_flask_cluster_output" group by cluster_id having sum(pon_homes) > 48 or sum(pon_homes) < 16',
                con=engine)
        engine.dispose()
        # terminate_connections()
        print(df)

        filepath_cluster_output = fr"{HOME_DIR}/{username}/data output/cluster_output"
        query = f"SELECT * FROM {table_name}"

        cmds = 'pgsql2shp -f "' + filepath_cluster_output + f'" -h {host} -u {user} -P {password} {database} "' + query + '"'

        subprocess.call(cmds, shell=True)
        # terminate_connections()

        # filepath_cluster_output = fr"{HOME_DIR}/data output\nodes_output"
        # table_name_node = "{username}_sample_flask_nodes_output"

        # query = f"SELECT * FROM {table_name_node}"

        # cmds = 'pgsql2shp -f "'+ filepath_cluster_output + f'" -h {host} -u {user} -P {password} {database} "'+ query + '"'

        # subprocess.call(cmds, shell=True)
        # #terminate_connections()

        return {
            "status": 200,
            "cluster_id": list(df["cluster_id"].astype(str).values),
            "sum_pon_homes": list(df["tot_pon"].astype(str).values),
            "workspace_name": workspace_name,
            "table_name": table_name
        }
        print("*********WPNAME***")
        # print(get_workspace())
        # return redirect(url_for('load_data'))
    return '''
    <!doctype html>
    <title>Cluster Correction Test Form</title>
    <h1>Cluster Correction</h1>
    <form method=post enctype=multipart/form-data>
      <input type=text name=input_cluster_id multiple>
      <input type=text name=output_cluster_id multiple>
      <input type=text name=gis_tool_id multiple>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/aerial_page', methods=['GET', 'POST'])
def aerial_page():
    global CURRENT_TYPE
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        CURRENT_TYPE[username] = "A"
        # terminate_connections()

        # check if the post request has the file part
        for file in request.files.getlist('demand_files'):
            # f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
            # if 'file' not in request.files:
            #     flash('No file part')
            #     return redirect(request.url)
            # file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoints"
            file.filename = ".".join(ls_name)
            print("Demandpoints file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetlines'):
            # f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
            # if 'file' not in request.files:
            #     flash('No file part')
            #     return redirect(request.url)
            # file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "streetlines"
            file.filename = ".".join(ls_name)
            print("Streetlines File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()
        response = aerial_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>demandpoints</h1>
      <input type=file name=demandpoints multiple>
      <br>
      <h1>streetlines</h1>
      <input type=file name=streetlines multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


# @app.route('/aerial_update_db', methods=['GET', 'POST'])
def aerial_update_db(userparams):
    username = str(userparams)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    # generate_random_workspace()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_ar_process.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['cluster_output', 'nodes_output', 'outlier_output']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    try:
        # terminate_connections()
        conn = psycopg2.connect(
            database=database, user=user, password=password, host=host, port=port
        )
        conn.autocommit = True

        cursor = conn.cursor()
        sql = f'ALTER TABLE {schema}.{username}_sample_flask_cluster_output ALTER COLUMN gistool_id TYPE INTEGER;'
        cursor.execute(sql)
        conn.commit()

        # Closing the connection
        conn.close()
        # terminate_connections()
    except Exception as msg:
        print("Unable to change type", msg)
    ver = generate_outliers(3, 24, username)
    print(ver)
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = "NODE_" + str(curr_time)
    # workspace_name = "NODE_555"
    # set_workspace(workspace_name)
    # workspace_name = get_workspace()
    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *RUNNING ** ** ** ** ** ** ** ** ** ** ** *
        # {username}_sample_flask_cluster_output
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *END ** ** ** ** ** ** ** ** ** ** ** *
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *RUNNING ** ** ** ** ** ** ** ** ** ** ** *
        # {username}_sample_flask_nodes_output
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *END ** ** ** ** ** ** ** ** ** ** ** *
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *RUNNING ** ** ** ** ** ** ** ** ** ** ** *
        # {username}_sample_flask_outlier_output
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *END ** ** ** ** ** ** ** ** ** ** ** *
        # terminate_connections()

        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"
        print(table_name)
        x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost',
                                    port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")

        geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,
                                 srs_data="EPSG:27700")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        print("***************************END***********************")
        # terminate_connections()
        # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file + ["joined_cluster_id"],
        "workspace_name": workspace_name
    }


@app.route('/ug_page', methods=['GET', 'POST'])
def ug_page():
    global CURRENT_TYPE
    if request.method == 'POST':

        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        CURRENT_TYPE[username] = "U"
        # terminate_connections()
        # check if the post request has the file part
        for file in request.files.getlist('demand_files'):
            # f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
            # if 'file' not in request.files:
            #     flash('No file part')
            #     return redirect(request.url)
            # file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoints"
            file.filename = ".".join(ls_name)
            print("Demandpoints file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetcenterline_files'):
            # f.save(os.path.join(app.config['UPLOAD_PATH'], f.filename))
            # if 'file' not in request.files:
            #     flash('No file part')
            #     return redirect(request.url)
            # file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterlines"
            file.filename = ".".join(ls_name)
            print("Streetlines File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()
        response = ug_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>demandpoints</h1>
      <input type=file name=demand_files multiple>
      <br>
      <h1>streetlines</h1>
      <input type=file name=streetcenterline_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


#@app.route('/ug_update_db', methods=['GET', 'POST'])
def ug_update_db(userparams):
    username = str(userparams)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    # generate_random_workspace()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_ug_process.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['cluster_output', 'nodes_output', 'outlier_output']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    try:
        # terminate_connections()
        conn = psycopg2.connect(
            database=database, user=user, password=password, host=host, port=port
        )
        conn.autocommit = True

        cursor = conn.cursor()
        sql = f'ALTER TABLE {schema}.{username}_sample_flask_cluster_output ALTER COLUMN gistool_id TYPE INTEGER;'
        cursor.execute(sql)
        conn.commit()

        # Closing the connection
        conn.close()
        # terminate_connections()
    except Exception as msg:
        print("Unable to change type", msg)
    ver = generate_outliers(3, 24, username)
    print(ver)
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = "NODE_" + str(curr_time)
    # workspace_name = "NODE_555"
    # set_workspace(workspace_name)
    # workspace_name = get_workspace()
    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *RUNNING ** ** ** ** ** ** ** ** ** ** ** *
        # {username}_sample_flask_cluster_output
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *END ** ** ** ** ** ** ** ** ** ** ** *
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *RUNNING ** ** ** ** ** ** ** ** ** ** ** *
        # {username}_sample_flask_nodes_output
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *END ** ** ** ** ** ** ** ** ** ** ** *
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *RUNNING ** ** ** ** ** ** ** ** ** ** ** *
        # {username}_sample_flask_outlier_output
        # ** ** ** ** ** ** ** ** ** ** ** ** ** *END ** ** ** ** ** ** ** ** ** ** ** *
        # terminate_connections()

        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"
        print(table_name)
        x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost',
                                    port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")

        geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,
                                 srs_data="EPSG:27700")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        print("***************************END***********************")
        # terminate_connections()
        # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file + ["joined_cluster_id"],
        "workspace_name": workspace_name
    }


@app.route('/np_page', methods=['GET', 'POST'])
def np_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('existing_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "1pia_structures"
            file.filename = ".".join(ls_name)
            print("Existing file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaist_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "1cityfibre lincoln 2021"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('landboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "1Land_Registry_Cadastral_Parcels PREDEFINED"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()
        response = np_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Existing File</h1>
      <input type=file name=existing_files multiple>
      <br>
      <h1>Gaist File</h1>
      <input type=file name=gaist_files multiple>
      <br>
      <h1>Landboundary File</h1>
      <input type=file name=landboundary_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


# @app.route('/np_update_db', methods=['GET', 'POST'])
def np_update_db(userparams):
    username = str(userparams)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_np.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['existing_output', 'proposed_output']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/np_ug_page', methods=['GET', 'POST'])
def np_ug_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('existing_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "1pia_structures"
            file.filename = ".".join(ls_name)
            print("Existing file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaist_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "1cityfibre lincoln 2021"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('landboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "1Land_Registry_Cadastral_Parcels PREDEFINED"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()
        response = np_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Existing File</h1>
      <input type=file name=existing_files multiple>
      <br>
      <h1>Gaist File</h1>
      <input type=file name=gaist_files multiple>
      <br>
      <h1>Landboundary File</h1>
      <input type=file name=landboundary_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


#@app.route('/np_ug_update_db', methods=['GET', 'POST'])
def np_ug_update_db(userparams):
    username = str(userparams)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_np_ug.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    # terminate_connections()
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['existing_output_ug', 'proposed_output_ug']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        print("***************************END***********************")
        # terminate_connections()
        # GEOSERVER CODE
    # terminate_connections()
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


########################## DATA NETWORKING ##################################
@app.route('/dn_page', methods=['GET', 'POST'])
def dn_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('pia_structure'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "pia_structure1"
            file.filename = ".".join(ls_name)
            print("PIA structure", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('pia_duct'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pia_structure2"
            file.filename = ".".join(ls_name)
            print("PIA duct", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()
        return redirect(url_for('dn_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>pia_structure1</h1>
      <input type=file name=pia_structure multiple>
      <br>
      <h1>pia_structure2</h1>
      <input type=file name=pia_duct multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/dn_update_db', methods=['GET', 'POST'])
def dn_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    # qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    # subprocess.run(f'{qgis_int} "{HOME_DIR}/secondary_np_ug.py" ')

    base_dir = fr"{HOME_DIR}/data_input"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    # terminate_connections()
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['pia_structure1', 'pia_structure2']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user=user,
                                    pg_password=password, loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name='',workspace=workspace_name,srs_name="EPSG:27700")
        print("***************************END***********************")
        # terminate_connections()
        # GEOSERVER CODE
    # terminate_connections()
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/bf_page', methods=['GET', 'POST'])
def bf_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('demand_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoints"
            file.filename = ".".join(ls_name)
            print("Existing file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('duct_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pia_duct"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('landboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "landboundary"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('googlepoles_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "polesfromgoogle"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('piastruc_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pia_structure"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetcenterlines_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterlines"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()
        return redirect(url_for('bf_update_db',
                                filename=username))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Demand Points</h1>
      <input type=file name=demand_files multiple>
      <br>
      <h1>Duct files</h1>
      <input type=file name=duct_files multiple>
      <br>
      <h1>Landboundary File</h1>
      <input type=file name=landboundary_files multiple>
      <br>
      <h1>Googlepoles files</h1>
      <input type=file name=googlepoles_files multiple>
      <br>
      <h1>Piastruc files</h1>
      <input type=file name=piastruc_files multiple>
      <br>
      <h1>Streetlines files</h1>
      <input type=file name=streetlines_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/bf_update_db', methods=['GET', 'POST'])
def bf_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_bf.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (
                    file_[:-4] in ['asn_boundary', 'demand_points', 'a_dp', 'aerial_drop', 'ug_landboundary',
                                   'nodes_output', 'withleading', 'large_mdu', 'cluster_output', 'wall_mount_mdu']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    works_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=works_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=works_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=works_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=works_name,
                          srs_name="EPSG:27700")
        print("***************************END***********************")

        # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": works_name
    }


@app.route('/snboundary_page', methods=['GET', 'POST'])
def snboundary_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('aerialdp_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "aerialdp"
            file.filename = ".".join(ls_name)
            print("aerialdp file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaistdata_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaistdata"
            file.filename = ".".join(ls_name)
            print("gaistdata File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetcenterline_files'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):
            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterlines"
            file.filename = ".".join(ls_name)
            print("streetcenterline File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('undergrounddp_files'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):
            ls_name = file.filename.split(".")
            ls_name[0] = "undergrounddp"
            file.filename = ".".join(ls_name)
            print("undergrounddp File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('lndbnry_files'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):
            ls_name = file.filename.split(".")
            ls_name[0] = "lndbnry"
            file.filename = ".".join(ls_name)
            print("lndbnry File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('topographiclines_files'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):
            ls_name = file.filename.split(".")
            ls_name[0] = "topographiclines"
            file.filename = ".".join(ls_name)
            print("topographiclines File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()
        return redirect(url_for('snboundary_page_update_db',
                                filename=username))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Aerialdp files</h1>
      <input type=file name=aerialdp_files multiple>
      <br>
      <h1>Gaistdata Files</h1>
      <input type=file name=gaistdata_files multiple>
      <br>
      <h1>Streetcenterline files</h1>
      <input type=file name=streetcenterline_files multiple>
      <br>
      <h1>undergrounddp files</h1>
      <input type=file name=undergrounddp_files multiple>
       <br>
      <h1>lndbnry files</h1>
      <input type=file name=lndbnry_files multiple>
      <br>
      <h1>topographiclines files</h1>
      <input type=file name=topographiclines_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/snboundary_page_update_db', methods=['GET', 'POST'])
def snboundary_page_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_snb.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (
                    file_[:-4] in ['new_clusters', 'final_boundaries']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    works_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=works_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=works_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=works_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=works_name,
                          srs_name="EPSG:27700")
        print("***************************END***********************")

        # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": works_name
    }


@app.route('/secondary_core_page', methods=['GET', 'POST'])
def secondary_core_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('feederring_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "feederring"
            file.filename = ".".join(ls_name)
            print("feederring file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        return redirect(url_for('secondary_core_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Feederring File</h1>
      <input type=file name=feederring_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/secondary_core_update_db', methods=['GET', 'POST'])
def secondary_core_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_core.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['highlighted', 'proposed_sj', 'fw4']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/secondary_drop_ug_page', methods=['GET', 'POST'])
def secondary_drop_ug_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('demand_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "demand"
            file.filename = ".".join(ls_name)
            print("demand file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaist_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        return redirect(url_for('secondary_drop_ug_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Demand File</h1>
      <input type=file name=demand_file multiple>
      <br>
      <h1>Gaist File</h1>
      <input type=file name=gaist_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/secondary_drop_ug_update_db', methods=['GET', 'POST'])
def secondary_drop_ug_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_drop_ug.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['lead_in']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/secondary_add_page', methods=['GET', 'POST'])
def secondary_add_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('demandpoints_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoint"
            file.filename = ".".join(ls_name)
            print("demandpoint file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('onexisting_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "onexisting"
            file.filename = ".".join(ls_name)
            print("onexisting file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('proposednodes_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "proposednode"
            file.filename = ".".join(ls_name)
            print("proposednode file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        return redirect(url_for('secondary_add_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Demandpoint File</h1>
      <input type=file name=demandpoints_file multiple>
      <br>
      <h1>Onexisting File</h1>
      <input type=file name=onexisting_file multiple>
      <br>
      <h1>Proposednodes File</h1>
      <input type=file name=proposednodes_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/secondary_add_update_db', methods=['GET', 'POST'])
def secondary_add_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_snadd.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['sn_address']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")

        # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/secondary_dis_page', methods=['GET', 'POST'])
def secondary_dis_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('existingducts_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "existingducts"
            file.filename = ".".join(ls_name)
            print("existingducts file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('existingstructures_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "existingstructures"
            file.filename = ".".join(ls_name)
            print("existing structures file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaist_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('primarynodes_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "primarynodes"
            file.filename = ".".join(ls_name)
            print("primarynodes file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('proposednodes_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "proposednodes"
            file.filename = ".".join(ls_name)
            print("proposednodes file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        return redirect(url_for('secondary_dis_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Existingducts File</h1>
      <input type=file name=existingducts_file multiple>
      <br>
      <h1>Existingstructures File</h1>
      <input type=file name=existingstructures_file multiple>
      <br>
      <h1>Gaist File</h1>
      <input type=file name=gaist_file multiple>
      <br>
      <h1>Primarynodes File</h1>
      <input type=file name=primarynodes_file multiple>
      <br>
      <h1>Proposednodes File</h1>
      <input type=file name=proposednodes_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/secondary_dis_update_db', methods=['GET', 'POST'])
def secondary_dis_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_dis.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['usable_existing_ducts', 'proposed_ducts']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/load_data_cluster', methods=['GET', 'POST'])
def load_data_cluster():
    global CURRENT_TYPE
    username = str(request.args.get("username"))
    current_type = CURRENT_TYPE[username]
    # terminate_connections()
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
    if (current_type == "A"):
        df = pd.read_sql_query(
            f'select cluster_index,sum(pon_homes) as tot_pon from "{username}_sample_flask_clusters" group by cluster_index having sum(pon_homes) > 24 or sum(pon_homes) < 3',
            con=engine)
    else:
        df = pd.read_sql_query(
            f'select cluster_index,sum(pon_homes) as tot_pon from "{username}_sample_flask_clusters" group by cluster_index having sum(pon_homes) > 48 or sum(pon_homes) < 16',
            con=engine)
    engine.dispose()
    # terminate_connections()
    print(df)
    return {
        "status": 200,
        "cluster_index": list(df["cluster_index"].astype(str).values),
        "sum_pon_homes": list(df["tot_pon"].astype(str).values)
    }


@app.route('/update_db_cluster', methods=['GET', 'POST'])
def update_db_cluster():
    global CURRENT_TYPE
    if request.method == 'POST':
        username = request.form.get('username')
        current_type = CURRENT_TYPE[username]
        # terminate_connections()
        # check if the post request has the file part
        cluster_in = int(request.form["input_cluster_index"])
        cluster_out = int(request.form["output_cluster_index"])
        uprn = int(request.form["uprn"])

        print("Cluster_in", cluster_in)
        print("Cluster_out", cluster_out)
        print("uprn", uprn)

        # IMPORT psycopg2
        # update db
        try:
            conn = psycopg2.connect(
                database=database, user=user, password=password, host=host, port=port
            )
            conn.autocommit = True

            cursor = conn.cursor()
            sql = f'UPDATE "{username}_sample_flask_clusters" SET "cluster_index" = {cluster_out} WHERE ("uprn" = {uprn}) AND ("cluster_index" = {cluster_in})'
            cursor.execute(sql)
            conn.commit()

            # Closing the connection
            conn.close()
            # terminate_connections()
            if (current_type == "A"):
                ver = generate_outliers(3, 24, username)
            else:
                ver = generate_outliers(16, 48, username)
            curr_time = int(time.time() * 1000)
            workspace_name = f"NODE_{curr_time}"
            # workspace_name = "NODE_555"
            table_name = f"{username}_sample_flask_cluster_output"
            geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
            geo.create_workspace(workspace=workspace_name)
            x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost',
                                        port="5432",
                                        pg_user='postgres',
                                        pg_password='postgres', loose_bbox="")
            print(x)
            geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,
                                     srs_data="EPSG:27700")
            geo.publish_style(layer_name=table_name, style_name='outlier', workspace=workspace_name,
                              srs_name="EPSG:27700")
            # terminate_connections()
        except Exception as msg:
            return {
                "Status": "FAILED",
                "Error": msg
            }

        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{database}')
        if (CURRENT_TYPE == "A"):
            df = pd.read_sql_query(
                f'select cluster_index,sum(pon_homes) as tot_pon from "{username}_sample_flask_clusters" group by cluster_index having sum(pon_homes) > 24 or sum(pon_homes) < 3',
                con=engine)
        else:
            df = pd.read_sql_query(
                f'select cluster_index,sum(pon_homes) as tot_pon from "{username}_sample_flask_clusters" group by cluster_index having sum(pon_homes) > 48 or sum(pon_homes) < 16',
                con=engine)
        engine.dispose()
        # terminate_connections()
        print(df)

        filepath_cluster_output = fr"{HOME_DIR}/{username}/data output/cluster_output"
        query = f"SELECT * FROM {table_name}"

        cmds = 'pgsql2shp -f "' + filepath_cluster_output + f'" -h {host} -u {user} -P {password} {database} "' + query + '"'

        subprocess.call(cmds, shell=True)
        # terminate_connections()

        # filepath_cluster_output = fr"{HOME_DIR}/data output\nodes_output"
        # table_name_node = "{username}_sample_flask_nodes_output"

        # query = f"SELECT * FROM {table_name_node}"

        # cmds = 'pgsql2shp -f "'+ filepath_cluster_output + f'" -h {host} -u {user} -P {password} {database} "'+ query + '"'

        # subprocess.call(cmds, shell=True)
        # #terminate_connections()

        return {
            "status": 200,
            "cluster_index": list(df["cluster_index"].astype(str).values),
            "sum_pon_homes": list(df["tot_pon"].astype(str).values),
            "workspace_name": workspace_name,
            "table_name": table_name
        }
        print("*********WPNAME***")
        # print(get_workspace())
        # return redirect(url_for('load_data'))
    return '''
    <!doctype html>
    <title>Cluster Correction Page</title>
    <h1>Cluster Correction</h1>
    <form method=post enctype=multipart/form-data>
      <h1>input cluster index</h1>
      <input type=text name=input_cluster_index multiple>
      <br>
      <h1>Output cluster index</h1>
      <input type=text name=output_cluster_index multiple>
      <br>
      <h1>uprn</h1>
      <input type=text name=uprn multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''
@app.route('/secondary_pre_gp_page', methods=['GET', 'POST'])
def secondary_pre_gp_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('PNBoundary_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "pnboundary"
            file.filename = ".".join(ls_name)
            print("pnboundary file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaistdata_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "gaistdata"
            file.filename = ".".join(ls_name)
            print("existing structures file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('googlepoles_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "googlepoles"
            file.filename = ".".join(ls_name)
            print("googlePoles file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('piastructurepoles_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "piastructurepoles"
            file.filename = ".".join(ls_name)
            print("piastructurepoles file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        return redirect(url_for('secondary_pre_gp_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>PNBoundary File</h1>
      <input type=file name=PNBoundary_file multiple>
      <br>
      <h1>gaistdata File</h1>
      <input type=file name=gaistdata_file multiple>
      <br>
      <h1>googlePoles File</h1>
      <input type=file name=googlepoles_file multiple>
      <br>
      <h1>piastructurepoles File</h1>
      <input type=file name=piastructurepoles_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/secondary_pre_gp_update_db', methods=['GET', 'POST'])
def secondary_pre_gp_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_pre_gp.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['flagged', 'updated_gp']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/secondary_ref_bndry', methods=['GET', 'POST'])
def secondary_ref_bndry():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('aerialdp_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "aerialdp"
            file.filename = ".".join(ls_name)
            print("aerialdp file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaistdata_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaistdata"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('lndbnry_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "lndbnry"
            file.filename = ".".join(ls_name)
            print("lndbnry File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetcenterline_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterline"
            file.filename = ".".join(ls_name)
            print("streetcenterline File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        for file in request.files.getlist('topographiclines_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "topographiclines"
            file.filename = ".".join(ls_name)
            print("topographiclines File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        for file in request.files.getlist('undergrounddp_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "undergrounddp"
            file.filename = ".".join(ls_name)
            print("undergrounddp File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
            # terminate_connections()
        return redirect(url_for('secondary_ref_bndry_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Aerialdp files</h1>
      <input type=file name=aerialdp_files multiple>
      <br>
      <h1>Gaist data File</h1>
      <input type=file name=gaistdata_files multiple>
      <br>
      <h1>Landboundary File</h1>
      <input type=file name=lndbnry_files multiple>
      <br>
      <h1>Street Centerline File</h1>
      <input type=file name=streetcenterline_files multiple>
      <br>
      <h1>Topographiclines File</h1>
      <input type=file name=topographiclines_files multiple>
      <br>
      <h1>Undergrounddp File</h1>
      <input type=file name=undergrounddp_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/secondary_ref_bndry_update_db', methods=['GET', 'POST'])
def secondary_ref_bndry_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_ref_bndry.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    # terminate_connections()
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['final_boundaries', 'new_clusters']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        print("***************************END***********************")
        # terminate_connections()
        # GEOSERVER CODE
    # terminate_connections()
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }
########################## DATA NETWORKING ##################################

@app.route('/secondary_fianl_nb', methods=['GET', 'POST'])
def secondary_fianl_nb():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('gaistdata_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "gaistdata"
            file.filename = ".".join(ls_name)
            print("gaistdata file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('landboundary_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "landboundary"
            file.filename = ".".join(ls_name)
            print("landboundary file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetcenterline_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterline"
            file.filename = ".".join(ls_name)
            print("streetcenterline file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('topographiclines_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "topographiclines"
            file.filename = ".".join(ls_name)
            print("topographiclines file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('updatedcluster_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "updatedcluster"
            file.filename = ".".join(ls_name)
            print("updatedcluster file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        return redirect(url_for('secondary_fianl_nb_update_db',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Gaistdata File</h1>
      <input type=file name=gaistdata_file multiple>
      <br>
      <h1>Landboundary File</h1>
      <input type=file name=landboundary_file multiple>
      <br>
      <h1>Streetcenterline File</h1>
      <input type=file name=streetcenterline_file multiple>
      <br>
      <h1>Topographiclines File</h1>
      <input type=file name=topographiclines_file multiple>
      <br>
      <h1>Updated cluster File</h1>
      <input type=file name=updatedcluster_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/secondary_fianl_nb_update_db', methods=['GET', 'POST'])
def secondary_fianl_nb_update_db():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_fianl_nb.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['final_boundaries']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/google_Poles_page', methods=['GET', 'POST'])
def google_Poles_page():
    if request.method == 'POST':

        username = request.form.get('username')
        for file in request.files.getlist('googlePoles_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "googlePoles"
            file.filename = ".".join(ls_name)
            print("googlePoles file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/googlpoles_data", filename))
        return redirect(url_for('google_Poles_update_folder',
                                filename=username))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>googlePoles File</h1>
      <input type=file name=googlePoles_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/google_Poles_update_folder', methods=['GET', 'POST'])
def google_Poles_update_folder():
    username = request.args.get("filename")
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/googlpoles_data"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/googlpoles_data"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)

    return {
        "status": 200,

    }


@app.route('/download_google_Poles_files', methods=['GET', 'POST'])
def download_google_Poles_files():
    # Zip file Initialization and you can change the compression type
    zipfolder = zipfile.ZipFile('files.zip', 'w', compression=zipfile.ZIP_STORED)

    # zip all the files which are inside in the folder
    for root, dirs, files in os.walk('user1/googlpoles_data/'):
        for file in files:
            zipfolder.write('user1/googlpoles_data/' + file)
    zipfolder.close()
    p = 'files.zip'

    return send_file(p, mimetype='zip', download_name=p, environ=request.environ, as_attachment=True)

    # Delete the zip file if not needed
    os.remove("files.zip")
    return {
        "status": 200,

    }


@app.route('/export_output', methods=['GET', 'POST'])
def export_output():
    import shutil
    if request.method == "POST":
        # print(request.data)
        # json.loads(request.data)["username"]
        username = request.form.get('username')
        try:
            os.remove(fr"{HOME_DIR}/{username}/data_output.zip")
        except Exception as msg:
            pass
        qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
        subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/shp_to_qgs.py" {username}')
        shutil.make_archive(fr"{HOME_DIR}/{username}/data_output", 'zip', fr"{HOME_DIR}/{username}/data output")
        try:
            return {"status": 200}
        except Exception as msg:
            print('message', msg)
            return f"error : {msg}"
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
      <br>
      <h1>All Files</h1>
      <input type=file name=allfiles multiple>
    </form>
    '''


@app.route('/crud', methods=['GET', 'POST'])
def crud():
    data = json.loads(request.data)
    if (data["action"].lower() == "add"):
        addData(data)
        return "Add Operation done!"
    elif (data["action"].lower() == "update"):
        updateData(data)
        return "Update Operation done!"
    elif (data["action"].lower() == "delete"):
        deleteData(data)
        return "Delete Operation done!"
    else:
        return "Invalid Action"

@app.route('/register', methods=['POST'])
def registration():
    print("Register")
    if request.method == "POST" and json.loads(request.data)["username"] and json.loads(request.data)["password"]\
            and json.loads(request.data)["schemaname"]:
        username = json.loads(request.data)["username"]
        user_password = json.loads(request.data)["password"]
        schemaname = json.loads(request.data)["schemaname"]

        conn = psycopg2.connect(
            database=database, user=user, password=password, host=host, port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Userregister WHERE username = %s", [username])
        if cursor is not None:
            record = Userregister(username, user_password, schemaname)
            db.session.add(record)
            db.session.commit()
            create_schema(schemaname)
            return {'success': True,
                    'message': 'User created and schema is generated'}
        else:
            return {'success': False,
                    'message': 'User already exist'}
    else:
        return {'success': False,
                'message': 'this method accept GET'}

@app.route('/login', methods=['POST'])
def login():
    if request.method == "POST" and json.loads(request.data)["password"] and json.loads(request.data)["username"]:
        username = json.loads(request.data)["username"]
        password = json.loads(request.data)["password"]
        exist = Userregister.query.filter_by(username=username).first()
        if exist and exist.password == password:
            payload = {'user_id': {"id": exist.id, "username": exist.username}}
            token = jwt.encode(payload=payload, key=My_SECRET_STRING)
            return {'success': True,
                    'message': 'User created and schema is generated',
                    'token': token,
                    'isUserLoggedId': 1,
                    'username': username,
                    'schema': exist.schemaname}
        else:
            return {'success': False,
                    'message': 'Please check your username and password.'}
    else:
        return {'success': False,
                'message': 'This method accept POST'}

@app.route('/secondary_structures', methods=['GET', 'POST'])
def secondary_structures():
    print("this is running")
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        username = request.form.get('username')
        print(request.files)
        # # terminate_connections()
        for file in request.files.getlist('googlepoles_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "googlepoles"
            file.filename = ".".join(ls_name)
            print("googlepoles file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data output", filename))

        for file in request.files.getlist('piastructures_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "piastructures"
            file.filename = ".".join(ls_name)
            print("piastructures file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        response = secondary_structures_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Googlepoles File</h1>
      <input type=file name=googlepoles_file multiple>
      <br>
      <h1>Piastructures File</h1>
      <input type=file name=piastructures_file multiple>
      <br>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


# @app.route('/secondary_structures_update_db', methods=['GET', 'POST'])
def secondary_structures_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_structures.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['structures']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }

@app.route('/secondary_preprocessdp', methods=['GET', 'POST'])
def secondary_preprocessdp():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')
        # shape_file_page()
        # terminate_connections()
        for file in request.files.getlist('cartograpgictext_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "cartograpgictext"
            file.filename = ".".join(ls_name)
            print("Cartograpgictext File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        for file in request.files.getlist('demandpoints_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoints"
            file.filename = ".".join(ls_name)
            print("Demandpoints file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+fr"/{username}/data_input", filename))
        for file in request.files.getlist('gaistdata_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        for file in request.files.getlist('landboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "landboundary"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        for file in request.files.getlist('streetcenterline_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterlines"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('topographicline_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "topographicline"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        #terminate_connections()
        response = secondary_preprocessdp_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>Cartograpgictext</h1>
      <input type=file name=cartograpgictext_file multiple>
      <h1>Demand Points</h1>
      <input type=file name=demandpoints_files multiple>
      <h1>gaist</h1>
      <input type=file name=gaist_files multiple>
      <h1>landboundary</h1>
      <input type=file name=landboundary_files multiple>
      <h1>streetcenterline</h1>
      <input type=file name=streetcenterline_files multiple>
      <h1>topographicline</h1>
      <input type=file name=topographicline_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/nb_update_db', methods=['GET', 'POST'])
def secondary_preprocessdp_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_preprocessdp.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['preprocessed_dp']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }
@app.route('/secondary_clusterbndry', methods=['GET', 'POST'])
def Secondary_clusterbndry():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')
        for file in request.files.getlist('preprocessed_dp'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoints"
            file.filename = ".".join(ls_name)
            print("updated Demandpoints file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+fr"/{username}/data output", filename))
        for file in request.files.getlist('referencepoints_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "referenceline"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data output", filename))
        for file in request.files.getlist('landboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "landboundary"
            file.filename = ".".join(ls_name)
            print("landboundary file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetcenterlines_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterlines"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('topographiclines_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "topographiclines"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        #terminate_connections()
        response = Secondary_clusterbndry_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>Demand points files</h1>
      <input type=file name=demandpoints_files multiple>
      <h1>Final poles files</h1>
      <input type=file name=finalpoles_files multiple>
      <h1>Referencepoints files</h1>
      <input type=file name=referencepoints_files multiple>
      <h1>landboundary</h1>
      <input type=file name=landboundary_files multiple>
      <h1>streetcenterline</h1>
      <input type=file name=streetcenterlines_files multiple>
      <h1>topographicline</h1>
      <input type=file name=topographiclines_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/nb_update_db', methods=['GET', 'POST'])
def Secondary_clusterbndry_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/Secondary_clusterbndry.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['cluster_bndry','Mdu']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }


@app.route('/shape_file_page', methods=['GET', 'POST'])
def shape_file_page():
    if request.method == 'POST':
        print("ddddd")
        # username = json.loads(request.data)["username"]
        # username = request.form.get('username')
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('demand_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "demandpoints"
            file.filename = ".".join(ls_name)
            print("Existing file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('duct_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pia_duct"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('landboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "landboundary"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data output", filename))

        for file in request.files.getlist('piastruc_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "piastructures"
            file.filename = ".".join(ls_name)
            print("Gaist File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetcenterline_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "streetcenterlines"
            file.filename = ".".join(ls_name)
            print("streetcenterline File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        # terminate_connections()

        for file in request.files.getlist('pnboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "pnboundary"
            file.filename = ".".join(ls_name)
            print("aerialdp file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('gaistdata_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaistdata File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('streetline_files'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):
            ls_name = file.filename.split(".")
            ls_name[0] = "streetline"
            file.filename = ".".join(ls_name)
            print("streetcenterline File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('primarynodes_files'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):
            ls_name = file.filename.split(".")
            ls_name[0] = "primarynodes"
            file.filename = ".".join(ls_name)
            print("undergrounddp File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))



        for file in request.files.getlist('topographiclines_files'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):
            ls_name = file.filename.split(".")
            ls_name[0] = "topographiclines"
            file.filename = ".".join(ls_name)
            print("topographiclines File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('cartograpgictext_file'):
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "cartograpgictext"
            file.filename = ".".join(ls_name)
            print("Cartograpgictext File", file.filename)
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))
        response = shape_file_update_folder(username)
        return response

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
        <h1>Demand Points</h1>
      <input type=file name=demand_files multiple>
      <br>
      <h1>Duct files</h1>
      <input type=file name=duct_files multiple>
      <br>
      <h1>Landboundary File</h1>
      <input type=file name=landboundary_files multiple>
      <br>
      <h1>Googlepoles files</h1>
      <input type=file name=googlepoles_files multiple>
      <br>
      <h1>Piastruc files</h1>
      <input type=file name=piastruc_files multiple>
      <br>
      <h1>streetcenterline files</h1>
      <input type=file name=streetline_files multiple>
      <br>
      <h1>Aerialdp files</h1>
      <input type=file name=aerialdp_files multiple>
      <br>
      <h1>Gaistdata Files</h1>
      <input type=file name=gaistdata_files multiple>
      <br>
      <h1>primarynodes files</h1>
      <input type=file name=primarynodes_files multiple>
      <br>
      <h1>topographiclines files</h1>
      <input type=file name=topographiclines_files multiple>
      <br>
      <h1>cartograpgictext file</h1>
      <input type=file name=cartograpgictext_file multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload> 
    </form>
    '''


#@app.route('/shape_file_update_folder', methods=['GET', 'POST'])
def shape_file_update_folder(userparam):
    username = str(userparam)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                pointDf.to_file(full_path)
                print(pointDf)

    return {
        "status": 200
    }


# @app.route('/shp_to_qgs', methods=['GET', 'POST'])
# def shp_to_qgs():
#     global CURRENT_TYPE
#     if request.method == 'POST':
#         workspace = request.form.get('workspace')
#         username = request.form.get('username')
#
#         save_input_in_dir(username, request.files)
#         response = changing(username, workspace)
#         return response
    # return '''
    # <!doctype html>
    # <title>Upload new File</title>
    # <h1>Upload new File</h1>
    # <form method=post enctype=multipart/form-data>
    #   <h1>WorkSpace name</h1>
    #   <input type=text name=workspace multiple>
    #   <input type=submit value=Upload>
    #
    #   <br>
    #   <h1>All Files</h1>
    #   <input type=file name=allfiles multiple>
    # </form>
    # '''

@app.route('/secondary_cp', methods=['GET', 'POST'])
def secondary_cp():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')
        for file in request.files.getlist('gaist_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+fr"/{username}/data_input", filename))
        for file in request.files.getlist('nodepoints_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "nodepoints"
            file.filename = ".".join(ls_name)
            print("nodepoints file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        #terminate_connections()
        response = secondary_cp_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>gaist files</h1>
      <input type=file name=gaist_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/secondary_cp_update_db', methods=['GET', 'POST'])
def secondary_cp_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_cp.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['Ugnode_sn','cabinets']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }

@app.route('/secondary_preprocessgp', methods=['GET', 'POST'])
def secondary_preprocessgp():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')
        for file in request.files.getlist('gaist_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+fr"/{username}/data_input", filename))
        for file in request.files.getlist('piastructures_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "piastructures"
            file.filename = ".".join(ls_name)
            print("piastructures file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('pnboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pnboundary"
            file.filename = ".".join(ls_name)
            print("pnboundary file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('citygooglepoles_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "citygooglepoles"
            file.filename = ".".join(ls_name)
            print("rawgooglepoles file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))


        #terminate_connections()
        response = secondary_preprocessgp_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>gaist files</h1>
      <input type=file name=gaist_files multiple>
      <h1>piastructures files</h1>
      <input type=file name=piastructures_files multiple>
      <h1>pnboundary files</h1>
      <input type=file name=pnboundary_files multiple>
      <h1>rawgooglepoles files</h1>
      <input type=file name=rawgooglepoles_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/secondary_preprocessgp', methods=['GET', 'POST'])
def secondary_preprocessgp_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_preprocess_rgp.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['googlepoles','poles_at_5mtrs']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'"{schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }
@app.route('/secondary_hybrid_np', methods=['GET', 'POST'])
def secondary_hybrid_np():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')


        for file in request.files.getlist('gaistdata_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('piastruc_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "piastructures"
            file.filename = ".".join(ls_name)
            print("piastructures file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))


        #terminate_connections()
        response = secondary_hybrid_np_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>gaist files</h1>
      <input type=file name=gaistdata_files multiple>
      <h1>piastructure files</h1>
      <input type=file name=piastruc_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/secondary_hybrid_np', methods=['GET', 'POST'])
def secondary_hybrid_np_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_hybrid_np.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['existingpoles_asn','proposedpoles_asn','Ugnode_sn']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }
@app.route('/secondary_pnb_fed_ug', methods=['GET', 'POST'])
def secondary_pnb_fed_ug():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')
        for file in request.files.getlist('piastructures_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "piastructures"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER']+fr"/{username}/data_input", filename))
        for file in request.files.getlist('pnboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pnboundary"
            file.filename = ".".join(ls_name)
            print("piastructures file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))



        #terminate_connections()
        response = secondary_pnb_fed_ug_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>piastructures_files</h1>
      <input type=file name=piastructures_files multiple>
      <h1>pnboundary files</h1>
      <input type=file name=pnboundary_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/secondary_preprocessgp', methods=['GET', 'POST'])
def secondary_pnb_fed_ug_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_pnb_fed_ug.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['pnboundary']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }

@app.route('/download_qgis_files', methods=['GET', 'POST'])
def download_qgis_files():
    username = request.form.get('username')
    # Zip file Initialization and you can change the compression type
    zipfolder = zipfile.ZipFile('data_output.zip', 'w', compression=zipfile.ZIP_STORED)

    # zip all the files which are inside in the folder
    for root, dirs, files in os.walk(fr"{HOME_DIR}/{username}/data output"):
        for file in files:
            zipfolder.write(fr"{username}/data output/" +file)
    for root, dirs, files in os.walk(fr"{HOME_DIR}/{username}/data_input"):
        for file in files:
            zipfolder.write(fr"{username}/data_input/" +file)
    zipfolder.close()
    p = 'data_output.zip'

    return send_file(p, mimetype='zip', download_name=p, environ=request.environ, as_attachment=True)


    return {
        "status": 200,

    }
@app.route('/ref_point_page', methods=['GET', 'POST'])
def ref_point_page():
    if request.method == 'POST':
        # username = json.loads(request.data)["username"]
        # username = request.form.get('username')
        username = request.form.get('username')
        # terminate_connections()
        for file in request.files.getlist('refpoint_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            ls_name = file.filename.split(".")
            ls_name[0] = "referenceline"
            file.filename = ".".join(ls_name)
            print("referencepoints file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))


        response = ref_point_update_folder(username)
        return response

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
    <form method=post enctype=multipart/form-data>
        <h1>ref.point points</h1>
      <input type=file name=refpoint_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload> 
    </form>
    '''


#@app.route('/shape_file_update_folder', methods=['GET', 'POST'])
def ref_point_update_folder(userparam):
    username = str(userparam)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                pointDf.to_file(full_path)
                print(pointDf)

    return {
        "status": 200
    }

@app.route('/user_connectivity', methods=['GET','POST'])
def server_to_server_connectivity():
    if request.method == 'POST':
        username = request.form.get('username')
        zipfolder = zipfile.ZipFile(f'{username}_files.zip', 'w', compression=zipfile.ZIP_STORED)
        for root, dirs, files in os.walk(fr"{HOME_DIR}/{username}/data output"):
            for file in files:
                if (file.startswith("streetcenterlines")):
                    zipfolder.write(fr"{username}/data output/" +file)
        for root, dirs, files in os.walk(fr"{HOME_DIR}/{username}/data_input"):
            for file in files:
                if (file.startswith("streetcenterlines")):
                    zipfolder.write(fr"{username}/data_input/" +file)
        zipfolder.close()
        file_name = fr'{username}_files.zip'
        # return send_file(file_name, mimetype='zip', download_name=file_name, environ=request.environ, as_attachment=True)
        return send_file(

                    f'{username}_files.zip',
                    download_name=file_name,
                    as_attachment=True,
            environ=request.environ

        )
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data
          <h1>username</h1>
          <input type=text name=username multiple>
          <input type=submit value=download> 
        </form>
        '''

@app.route('/secondary_pn_np', methods=['GET', 'POST'])
def secondary_pn_np():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')

        for file in request.files.getlist('gaistdata_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "gaist"
            file.filename = ".".join(ls_name)
            print("gaist file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('piastruc_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "piastructures"
            file.filename = ".".join(ls_name)
            print("piastructures file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))



        for file in request.files.getlist('primarynodes_file'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pnnode"
            file.filename = ".".join(ls_name)
            print("pnnode file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))


        #terminate_connections()
        response = secondary_pn_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>gaist files</h1>
      <input type=file name=gaistdata_files multiple>
      <h1>piastructure files</h1>
      <input type=file name=piastruc_files multiple>
      <h1>pnboundary files</h1>
      <input type=file name=pnboundary_files multiple>
      <h1>pnnode files</h1>
      <input type=file name=pnnode_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''

# @app.route('/secondary_hybrid_np', methods=['GET', 'POST'])
def secondary_pn_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_pn_np.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['pn_cabinet','enclosure']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    # terminate_connections()
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'" {schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")

        print("***************************END***********************")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        # table_name = f"{username}_sample_flask_{name_shape_file[shape_path]}"
        # print(table_name)
        # x = geo.create_featurestore(store_name=table_name, workspace=workspace_name, db='UAT', host='localhost', port="5432",
        # pg_user='postgres',
        # pg_password='postgres',loose_bbox="")

        # geo.publish_featurestore(workspace=workspace_name, store_name=table_name, pg_table=table_name,srs_data="EPSG:27700")
        # geo.publish_style(layer_name=table_name, style_name=table_name[len(username)+1:], workspace=workspace_name,
        # srs_name="EPSG:27700")
        # # terminate_connections()
        # geo.upload_style(path=os.path.join(os.getcwd(),"proposed.sld"), workspace=workspaceName)
    # geo.publish_style(layer_name=table_name, style_name='nodeboundary', workspace=workspaceName, srs_name="EPSG:27700")
    # terminate_connections()
    print("***************************END***********************")
    # GEOSERVER CODE
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }

# @app.route('/city_register_login', methods=['POST'])
# def city_register_login():
#     if request.method == "POST" and json.loads(request.data)["password"] and json.loads(request.data)["username"]:
#         username = json.loads(request.data)["username"]
#         password = json.loads(request.data)["password"]
#         exist = Userregister.query.filter_by(username=username).first()
#         if exist and exist.password == password:
#             payload = {'user_id': {"id": exist.id, "username": exist.username}}
#             token = jwt.encode(payload=payload, key=My_SECRET_STRING)
#             return {'success': True,
#                     'message': 'User created and schema is generated',
#                     'token': token,
#                     'isUserLoggedId': 1,
#                     'username': username}
#         else:
#             return {'success': False,
#                     'message': 'Please check your username and password.'}
#     else:
#         return {'success': False,
#                 'message': 'This method accept POST'}
#
# @app.route('/city_register', methods=["POST", "GET"])
# def city_register():
#     username = request.form.get("username")
#     if request.method == "POST":
#         username = username.strip().capitalize()
#         user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
#         os.mkdir(user_folder)
#         return f"folder is created under the name {username} and the full path is {user_folder}"
#     return """
#     <form method="post" action="/city_register">
#     <input type="text" name="username" required>
#     <button type="submit" >Submit</button>
#     </form>
#     """
# @app.route('/dir')
# def dir_by():
#     path = "static"
#     dirs = os.listdir(path)
#     temp = []
#     for dir in dirs:
#         temp.append({'name': dir})
#
#     return temp

@app.route('/googleapifetch2', methods=['GET', 'POST'])
def googleapifetch2():
    if request.method == 'POST':
        # check if the post request has the file part
        username = request.form.get('username')

        for file in request.files.getlist('pnboundary_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "pnboundary"
            file.filename = ".".join(ls_name)
            print("pnboundary file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        for file in request.files.getlist('citygooglepoles_files'):

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            # if file and allowed_file(file.filename):

            ls_name = file.filename.split(".")
            ls_name[0] = "citygooglepoles"
            file.filename = ".".join(ls_name)
            print("citygooglepoles file", file.filename)

            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input", filename))

        # terminate_connections()
        response = googleapifetch2_update_db(username)
        return response
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <h1>pnboundary files</h1>
      <input type=file name=pnboundary_files multiple>
      <h1>rawgooglepoles files</h1>
      <input type=file name=citygooglepoles_files multiple>
      <h1>username</h1>
      <input type=text name=username multiple>
      <input type=submit value=Upload>
    </form>
    '''


# @app.route('/googleapifetch2_update_db', methods=['GET', 'POST'])
def googleapifetch2_update_db(userparam):
    username = str(userparam)
    check = Userregister.query.filter_by(username=username).first()
    schema = check.schemaname
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".zip")):
                with zipfile.ZipFile((os.path.join(subdir, file)), "fr") as zip_ref:
                    zip_ref.extractall(subdir)
    for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
        for file in files:
            if (file.endswith(".shp")):
                full_path = os.path.join(subdir, file)
                pointDf = gpd.read_file(full_path)
                pointDf.crs = "epsg:27700"

                os.remove(full_path)
                pointDf.to_file(full_path)
                print(pointDf)
    qgis_int = fr"C:\Program Files\QGIS 3.20.0\bin\python-qgis.bat"
    subprocess.run(f'{qgis_int} "{HOME_DIR}/scripts/secondary_clip_rgp.py" {username}')

    base_dir = fr"{HOME_DIR}/{username}/data output"
    full_dir = os.walk(base_dir)
    shapefile_list = []
    name_shape_file = []
    # terminate_connections()
    for source, dirs, files in full_dir:
        for file_ in files:
            if file_[-3:] == 'shp' and (file_[:-4] in ['rawgooglepoles']):
                shapefile_path = os.path.join(base_dir, file_)
                shapefile_list.append(shapefile_path)
                name_shape_file.append(file_[:-4])
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        remove_table(f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}")
        # terminate_connections()
        print()
        print("Table name", name_shape_file[shape_path])
        print()
        cmds = 'shp2pgsql "' + shapefile_list[
            shape_path] + f'"{schema}.{username}_sample_flask_{name_shape_file[shape_path]} | psql '
        subprocess.call(cmds, shell=True)
        # terminate_connections()
    # for subdir, dirs, files in os.walk(app.config['UPLOAD_FOLDER'] + fr"/{username}/data_input"):
    #     for file in files:
    #         os.remove(os.path.join(subdir, file))
    geo = Geoserver('http://localhost:8080/geoserver', username='admin', password='geoserver')
    curr_time = int(time.time() * 1000)
    workspace_name = f"NODE_{curr_time}"

    geo.create_workspace(workspace=workspace_name)
    arr = []
    for shape_path in range(len(shapefile_list)):
        # terminate_connections()
        print("***************************RUNNING***********************")

        table_name = f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}"

        x = geo.create_featurestore(store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                    workspace=workspace_name, db='UAT', host='localhost', port="5432",
                                    pg_user='postgres',
                                    pg_password='postgres', loose_bbox="")
        print(x)
        geo.publish_featurestore(workspace=workspace_name,
                                 store_name=f"{schema}.{username}_sample_flask_{name_shape_file[shape_path]}",
                                 pg_table=table_name, srs_data="EPSG:27700")
        geo.publish_style(layer_name=table_name, style_name=table_name[len(username) + 1:], workspace=workspace_name,
                          srs_name="EPSG:27700")
        print("***************************END***********************")
        # terminate_connections()
        # GEOSERVER CODE
    # terminate_connections()
    return {
        "status": 200,
        "table_name": name_shape_file,
        "workspace_name": workspace_name
    }

@app.route("/directory_list_submit", methods=['GET', 'POST'])
def directory_list_submit():
    select = request.form.get('comp_select')
    username = request.form.get('username')
    os.makedirs(fr'{HOME_DIR}/{username}')
    os.makedirs(fr'{HOME_DIR}/{username}/data_input')
    os.makedirs(fr'{HOME_DIR}/{username}/data output')
    # Providing the folder path
    origin = fr'C:/Users/jyothy/Desktop/New folder/geoflask_multi_user/cities/{select}/'
    target = fr'C:/Users/jyothy/Desktop/New folder/geoflask_multi_user/{username}/data_input/'

    files = os.listdir(origin)

    # Fetching all the files to directory
    for file_name in files:
        shutil.copy(origin + file_name, target + file_name)

    print(str(Path.home() / "Default"))
    copy_files(str(Path.home() / "Default"), fr'{HOME_DIR}/{username}/data output')
    print("Files are copied successfully")
    print(select)
    return {
        "status": 200,

    }


@app.route('/directory_list', methods=['GET', 'POST'])
def directory_list():
    path = "C:\\Users\\jyothy\\Desktop\\New folder\\geoflask_multi_user\\cities"
    dirs = os.listdir(path)
    temp = []
    for dir in dirs:
        temp.append({'name': dir})

    return {
        "status": 200,
        "data": temp
    }

#serve(app, host='0.0.0.0', port=5000, threads=8) #WAITRESS!
if __name__ == '__main__':
    # app.run(host='192.168.1.34')
    db.create_all()
    app.run(debug=True)
