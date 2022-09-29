from flask import Flask, flash, request, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename, send_file
import os
import shutil


def save_input_in_dir(username, files):
    for file in files.getlist('allfiles'):
        filename = secure_filename(file.filename)
        file.save(
            os.path.join(fr"C:/Users/jyothy/Desktop/New Folder/geoflask_multi_user/{username}/data_input", filename))

def copy_files(source, destination):
    try:
        for subdir, dirs, files in os.walk(source):
            for file in files:
                # if (file.endswith(".shp")):
                shutil.copy(os.path.join(source, file), os.path.join(destination, file))
    except Exception as e:
        print(e)
        pass