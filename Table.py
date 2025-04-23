"""Work_modele sqlite3"""
import sqlite3

from sqlite3 import Error

def create_connection(path):
    """THREE.create_connection"""
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("successfully connection!")
    except Error as e:
        print(f'Error {e}')
    return connection

connection1 = create_connection("data.sqlite")

cursor = connection1.cursor()
def create_table_for_zone():
    """Create table for zone information"""
    cursor.execute("""CREATE TABLE Zone
               (id INTEGER PRIMARY KEY,
               zone_name TEXT,
               category INTEGER NOT NULL,
               CONSTRAINT fk_category_id FOREIGN KEY (category)  REFERENCES Zone (id))
               """)
    cursor.execute("""CREATE TABLE Project_Zone
                (project_id INTEGER NOT NULL,
                zone_id INTEGER NOT NULL,
                PRIMARY KEY (project_id, zone_id),
                CONSTRAINT fk_project_id FOREIGN KEY (project_id)  REFERENCES Project (id),
                CONSTRAINT fk_zone_id FOREIGN KEY (zone_id)  REFERENCES Zone (id))
               """)
def create_table_for_workers():
    """Create table for workers information"""
    cursor.execute("""CREATE TABLE Workers
               (id INTEGER PRIMARY KEY,
                name TEXT)""")

    cursor.execute("""CREATE TABLE Project_Workers
                (project_id INTEGER NOT NULL,
                worker_id INTEGER NOT NULL,
                PRIMARY KEY (project_id, worker_id),
                CONSTRAINT fk_project_id FOREIGN KEY (project_id)  REFERENCES Project (id),
                CONSTRAINT fk_worker_id FOREIGN KEY (worker_id)  REFERENCES Workers (id))
               """)

def create_table_for_project():
    """Create table for project information"""
    cursor.execute("""CREATE TABLE Project
                (id INTEGER PRIMARY KEY,
                data TEXT,
                work_time REAL,
                approximate_costst REAL)
               """)

create_table_for_zone()

connection1.commit()

connection1.close()
