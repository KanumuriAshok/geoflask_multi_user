import psycopg2
# from app import remove_table
# import subprocess
# user = "globals"
# password = "globals"
# host = "localhost"
# port = 5432
# database = "globals"
user = "postgres"
password = "postgres"
host = "localhost"
port = 5432
database = "UAT"


def create_schema(schema):
    # name_shape_file = []
    connection = psycopg2.connect(
        database=database, user=user, password=password, host=host, port=port
    )
    # cursor = connection.cursor()
    CREATE_SCHEMA = f"CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION postgres;"
    # CREATE_TABLE1 = f"CREATE TABLE IF NOT EXISTS {schema}.{username} (username text)"
    # CREATE_TABLE2 = f"CREATE TABLE IF NOT EXISTS {schema}.{username} (username text)"


    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_SCHEMA)
            # cursor.execute(CREATE_TABLE1)
            # cursor.execute(CREATE_TABLE2)
