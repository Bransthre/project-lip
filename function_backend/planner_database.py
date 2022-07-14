#Packages
import sqlite3
from . import global_database

#Establishing connection to database
events_col_names = [
    'event_id', 'event_name', 'event_type', 'event_description', 'event_yr', 
    'event_month', 'event_day', 'event_hr', 'event_min'
]
events_db_access = (
    global_database.CWD + r'\databases/events_schedule.db'
)
data_conn = sqlite3.connect(events_db_access, check_same_thread=False)
data_crsr = data_conn.cursor()

def database_setup(tbl_name = "events"):
    """
    This function sets up a database for the event planner functions to 
    operate on.
    
    Args:
        tbl_name (str): The name for the table being set up in the database.
    """
    
    generate_events_tbl = f"""
    CREATE TABLE IF NOT EXISTS {tbl_name} (
        event_id INTEGER PRIMARY KEY,
        event_name VARCHAR(100),
        event_type VARCHAR(30),
        event_description VARCHAR(200),
        event_yr INTEGER,
        event_month INTEGER CHECK(event_month > 0 AND event_month <= 12),
        event_day INTEGER CHECK(event_day > 0 AND event_day <= 31),
        event_hr INTEGER CHECK(event_hr >= -1 AND event_hr <= 23),
        event_min INTEGER CHECK(event_min >= -1 AND event_min <= 59)
    );
    """
    data_crsr.execute(generate_events_tbl)
    data_conn.commit()

def clear_all_events(tbl_name = "events"):
    """
    This function clears all recorded events in the SQL database.

    Args:
        tbl_name (str): The name of the table this function works on.
    """
    data_crsr.execute(f"DELETE FROM {tbl_name}")
    data_conn.commit()

def get_all_events(tbl_name = "events"):
    """
    This function returns a sequence of all recorded events in the SQL database.

    Args:
        tbl_name (str): The name of the table this function works on.

    Returns:
        tuple: a sequence of all events in the database
    """
    data_crsr.execute(f"SELECT * FROM {tbl_name}")
    return data_crsr.fetchall()

def get_new_event_id(tbl_name = "events"):
    """
    This function returns the id of the next new event that should be inserted 
    into the table for primary key argument.

    Args:
        tbl_name (str): The name of the table this function works on.
    
    Returns:
        int: The new ID.
    """
    sql_get_max_id = f"SELECT MAX(event_id) FROM {tbl_name}"
    data_crsr.execute(sql_get_max_id)
    max_row_sequence = data_crsr.fetchone()
    max_id = (max_row_sequence[0] or 0) + 1
    return max_id

def get_event_id(
        name, year, month, day, 
        hr = None, min = None, tbl_name = "events"
    ):
    """
    This function retruns the ID of an event with specified details that
    includes name and time of an event. It returns None if the ID was not found.

    Args:
        name (str): the user-defined name of the event
        year (int): the year that this event occurs at
        month (int): the month that this event occurs at
        day (int): the day that this event occurs at
        hr (int): the hour that this event occurs at, in 24 hours counting
        min (int): the minute that this event occurs at
        tbl_name (str): table name of the table that entry will be created in.
    
    Returns:
        int or None: The ID of the described event, None if event was not found.
    """
    sql_get_event_id = f'''SELECT event_id FROM {tbl_name} WHERE
                           event_name = "{name}" AND event_yr = {year} AND 
                           event_month = {month} AND event_day = {day}'''
    
    if not hr is None: sql_get_event_id += f" AND event_hr = {hr}"
    if not min is None: sql_get_event_id += f" AND event_min = {min}"

    data_crsr.execute(sql_get_event_id)
    event_row_sequence = data_crsr.fetchone()
    try:
        return event_row_sequence[0]
    except:
        raise Exception("Event not found")

def create_event(
        name, type, descr, year, month, day, hr, min,
        tbl_name = "events"
    ):
    """
    This function creates an event in the SQLite Database of this program when
    connected to a user inputted prompt delivered from a different function.
    If no specific hour or minute was specified, they will both be set to -1.

    Args:
        name (str): the user-defined name of the event
        type (str): the user-defined type of the event
        descr (str): the descr of the created event
        year (int): the year that this event occurs at
        month (int): the month that this event occurs at
        day (int): the day that this event occurs at
        hr (int): the hour that this event occurs at, in 24 hours counting
        min (int): the minute that this event occurs at
        tbl_name (str): table name of the table that entry will be created in.
    """
    event_params = [
        get_new_event_id(tbl_name), name, type, descr, year, month, day, hr, min
    ]
    event_params_cleaned = []
    for elem in event_params:
        if elem is None: event_params_cleaned.append("NULL")
        else: event_params_cleaned.append(repr(elem))
    sql_event_param = ",".join(event_params_cleaned)

    sql_event_creation = f"INSERT INTO {tbl_name} VALUES ({sql_event_param});"
    data_crsr.execute(sql_event_creation)
    data_conn.commit()

def remove_event(
        name, year, month, day, 
        hr = None, min = None, tbl_name = "events"
    ):
    """
    This function removes an event in the SQLite Database of this program when
    connected to a user inputted prompt delivered from a different function.

    Args:
        name (str): the user-defined name of the event
        year (int): the year that this event occurs at
        month (int): the month that this event occurs at
        day (int): the day that this event occurs at
        hr (int): the hour that this event occurs at, in 24 hours counting
        min (int): the minute that this event occurs at
        tbl_name (str): table name of the table that entry will be created in.
    """
    removed_event_id = get_event_id(name, year, month, day, hr, min, tbl_name)
    sql_remove_event = (
        f"DELETE FROM {tbl_name} WHERE event_id = {removed_event_id}"
    )
    data_crsr.execute(sql_remove_event)
    data_conn.commit()

def update_event(updated, name, year, month, day, hr, min, tbl_name = "events"):
    """
    This function updates an event in the SQLite Database of this program when
    connected to a user inputted prompt delivered from a different function.

    Args:
        updated (dict): a dictionary of updated properties
        name (str): the user-defined name of the event
        year (int): the year that this event occurs at
        month (int): the month that this event occurs at
        day (int): the day that this event occurs at
        hr (int): the hour that this event occurs at, in 24 hours counting
        min (int): the minute that this event occurs at
        tbl_name (str): table name of the table that entry will be created in.
    """
    updated_event_id = get_event_id(name, year, month, day, hr, min, tbl_name)
    sql_update_prop = ""
    for p in updated.items():
        if p[1] is not None:
            sql_update_prop += f'{p[0]} = {repr(p[1])}, '
    sql_update_event = (
        f"UPDATE {tbl_name} SET {sql_update_prop[:-2]} "
        f"WHERE event_id = {updated_event_id}"
    )
    data_crsr.execute(sql_update_event)
    data_conn.commit()