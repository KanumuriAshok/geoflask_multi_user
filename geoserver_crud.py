import psycopg2
from config import *

null = None
def deleteData(data):
    try:
        print(data)
        connection = psycopg2.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)

        cursor = connection.cursor()

        # Update single record now
        sql_delete_query = f"""Delete from {data["layer_name"]} where gid = %s"""
        cursor.execute(sql_delete_query, (data["gid"],))
        connection.commit()
        count = cursor.rowcount
        print(count, "Record deleted successfully ")

    except (Exception, psycopg2.Error) as error:
        print("Error in Delete operation", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
            
def getAllData(data):
    try:
        connection = psycopg2.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)
        cursor = connection.cursor()
        postgreSQL_select_Query = f"select * from {data['layer_name']}"

        cursor.execute(postgreSQL_select_Query)
        print(f"Selecting rows from {data['layer_name']} table using cursor.fetchall")
        all_records = cursor.fetchall()
        
        return all_records
        # print("Print each row and it's columns values")
        # for row in all_records:
            # print("Id = ", row[0], )
            # print("Model = ", row[1])
            # print("Price  = ", row[2], "\n")

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
def addData(data):
    try:
        all_cols = list(data.keys())
        all_cols.remove("layer_name")
        all_cols.remove("action")
        connection = psycopg2.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)
        cursor = connection.cursor()
        all_data = getAllData(data)
        data["gid"] = all_data[-1][0]+1
        
        string_cols = ""
        variable_string = ""
        for x in all_cols[:-1]:
            string_cols += x
            string_cols += ", "
            variable_string += "%s,"
        string_cols += all_cols[-1]
        variable_string += "%s"
        postgres_insert_query = f""" INSERT INTO {data["layer_name"]} ({string_cols}) VALUES ({variable_string})"""
        
        record_to_insert = []
        for x in all_cols:
            record_to_insert.append(data[x])
        record_to_insert = tuple(record_to_insert)
        
        cursor.execute(postgres_insert_query, record_to_insert)

        connection.commit()
        count = cursor.rowcount
        print(count, f"Record inserted successfully into {data['layer_name']} table")

    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into mobile table", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
def updateData(data):
    try:
        all_cols = list(data.keys())
        all_cols.remove("layer_name")
        all_cols.remove("action")
        connection = psycopg2.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=database)

        cursor = connection.cursor()

        print("Table Before updating record ")
        sql_select_query = f"""select * from {data["layer_name"]} where gid = %s"""
        cursor.execute(sql_select_query, (data["gid"],))
        record = cursor.fetchone()
        print(record)

        # Update single record now
        set_string = ""
        for x in all_cols[1:-1]:
            set_string += x
            set_string += " = %s, "
        set_string += all_cols[-1]
        set_string += " = %s"
            
        sql_update_query = f"""Update {data["layer_name"]} set {set_string} where gid = %s"""
        record_info = []
        
        for x in all_cols[1:]:
            record_info.append(data[x])
        record_info.append(data["gid"])
        cursor.execute(sql_update_query, tuple(record_info))
        
        connection.commit()
        count = cursor.rowcount
        print(count, "Record Updated successfully ")

        print("Table After updating record ")
        sql_select_query = f"""select * from {data["layer_name"]} where gid = %s"""
        cursor.execute(sql_select_query, (data["gid"],))
        record = cursor.fetchone()
        print(record)

    except (Exception, psycopg2.Error) as error:
        print("Error in update operation", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


          
