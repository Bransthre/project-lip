#Packages
import sqlite3
import numpy as np
import pandas as pd
import datetime
from . import global_database as gl_ds

#Establishing connection agent with database
#Establishing Connection with Database
emo_col_names = [
    'log_id', 'user_valence', 'user_activation', 'log_year', 'log_month', 
    'log_date', 'emotion', 'log_time', 'log_day', 'log_loc', 'social_deg', 
    'work_deg', 'rest_deg'
]
emo_db_access = gl_ds.CWD + r'/databases/emotion_data.db'
data_conn = sqlite3.connect(emo_db_access, check_same_thread = False)
data_conn.row_factory = sqlite3.Row
data_crsr = data_conn.cursor()
entries_file_address = (
    gl_ds.CWD + r"/function_backend/log_entries.txt"
)

def emo_tbl_setup(tbl_name = "emotion_data"):
    """
    This function sets up a database for the decision tree functions to 
    operate on.

    Args:
        tbl_name (str): The name of the table this function works on.
    """
    
    generate_emo_tbl = f"""
    CREATE TABLE IF NOT EXISTS {tbl_name} (
        log_id INTEGER PRIMARY KEY,
        user_valence INTEGER CHECK(user_valence >= -1 AND user_valence <= 1),
        user_activation INTEGER CHECK(user_activation >= -1 AND \
            user_activation <= 1),
        log_year INTEGER,
        log_month INTEGER CHECK(1 <= log_month AND log_month <= 12),
        log_date INTEGER CHECK(1 <= log_date AND log_date <= 31),
        emotion VARCHAR(50),
        log_time INTEGER,
        log_day INTEGER CHECK(log_day >= 0 AND log_day <= 6),
        log_loc VARCHAR(100),
        social_deg INTEGER CHECK(social_deg >= 1 AND social_deg <= 5),
        work_deg INTEGER CHECK(work_deg >= 1 AND work_deg <= 5),
        rest_deg INTEGER CHECK(rest_deg >= 1 AND rest_deg <= 5)
    );
    """
    data_crsr.execute(generate_emo_tbl)
    data_conn.commit()

def get_sample_data(
        tbl_name = "emotion_data",
        cutoff_col = 6,
        filter = "",
        target_class = "emotion"
    ):
    """
    This function gathers data from SQL database into the format of pandas 
    DataFrame

    Args:
        tbl_name (str): The name of the table this function works on.
        
    Returns:
        DataFrame: a dataframe containing the contents of data from the SQL
        databases
    """
    select_all_sql = f"SELECT * FROM {tbl_name} {filter}"
    data_crsr.execute(select_all_sql)
    all_data = data_crsr.fetchall()
    all_data_dict = {}
    key_names = ()
    for rows in all_data:
        if key_names == ():
            if target_class == "all":
                key_names = rows.keys()[:]
            elif target_class in emo_col_names:
                key_names = [target_class] + rows.keys()[cutoff_col + 1:]
            else:
                raise Exception(f"Inputted a column that DNE, {target_class}")
        for key in key_names:
            all_data_dict[key] = all_data_dict.get(key, []) + [rows[key]]
    return pd.DataFrame(data = all_data_dict)[-100:]

def get_new_entry_id(tbl_name = 'emotion_data'):
    """
    This function returns the id of the next new event that should be inserted 
    into the table with name tbl_name for primary key argument.
    
    Args:
        tbl_name (str): The name of the table this function works on.
    
    Returns:
        int: The new ID.
    """
    sql_get_max_id = f"SELECT MAX(log_id) FROM {tbl_name}"
    data_crsr.execute(sql_get_max_id)
    max_row_sequence = data_crsr.fetchone()
    max_id = (max_row_sequence[0] or 0) + 1
    return max_id

def clear_all_logs(tbl_name = "emotion_data"):
    """
    This function clears all recorded logs of the table with name tbl_name
    in the SQL database.
    
    Args:
        tbl_name (str): The name of the table this function works on.
    """
    data_crsr.execute(f"DELETE FROM {tbl_name}")
    data_conn.commit()

def delete_tbl(tbl_name = "emotion_data"):
    """
    This function deletes the table in database whose name is tbl_name.
    
    Args:
        tbl_name (str): The name of the table this function works on.
    """
    data_crsr.execute(f"DROP TABLE IF EXISTS {tbl_name}")
    data_conn.commit()

def create_entry(
        emotion, log_time, log_day, log_loc, social_deg, work_deg, rest_deg, 
        today,
        tbl_name = 'emotion_data', valence = None, activate = None
    ):
    """
    Creates an entry in the emotion database for this system based on the
    parameters noted in the function arguments.

    Args:
        emotion (str): emotion type.
        log_time (int): time of survey entry creation.
        log_day (int): day of survey entry creation.
        log_loc (str): physical location during survey entry creation.
        social_deg (int): social degree of user at point of survey.
        work_deg (int): work degree of user at point of survey.
        rest_deg (int): rest degree of user at point of survey.
        today (datetime.datetime): A datetime object for today's date.
        tbl_name (str): table name of the table that entry will be created in.
        valence (int): valence of user's emotion at point of survey.
        activate (int): activation of user's emotion at point of survey.
    """
    log_params = [
        get_new_entry_id(tbl_name), valence, activate, today.year, today.month,
        today.day, emotion, log_time, log_day, log_loc, social_deg, work_deg, 
        rest_deg
    ]
    log_params_cleaned = []
    for elem in log_params:
        if elem is None: log_params_cleaned.append("NULL")
        else: log_params_cleaned.append(repr(elem))
    sql_log_param = ",".join(log_params_cleaned)
    sql_log_creation = f"INSERT INTO {tbl_name} VALUES ({sql_log_param});"
    data_crsr.execute(sql_log_creation)
    data_conn.commit()

def get_all_log_entries():
    all_lines = open(entries_file_address).readlines() + [""]
    data_entries = []
    cur_entry = []
    column_lbls = ["yr", "month", "day", "hr", "min", "text", "val", "act"]
    cur_txt = ""
    while len(all_lines):
        cur_line = all_lines[0]
        if cur_line == "":
            pass
        elif cur_line[0] == "#":
            cur_entry.append(cur_txt)
            cur_entry.extend([int(el) for el in cur_line[1:].split("|")[:-1]])
            data_entries.append(cur_entry)
        elif cur_line[0] == "@":
            cur_entry = []
            cur_txt = ""
            entry_attr = [int(elem) for elem in cur_line[1:].split("-")[:-1]]
            cur_entry.extend(entry_attr[:3])
            cur_entry.extend(list(divmod(int(entry_attr[3]), 60)))
        else:
            cur_txt += cur_line
        all_lines.pop(0)
    return pd.DataFrame(np.array(data_entries), columns = column_lbls)

def get_log_entries(filter_funcs = [None for _ in range(8)]):
    log_entries = get_all_log_entries()
    column_lbls = ["yr", "month", "day", "hr", "min", "text", "val", "act"]
    for lbl in column_lbls:
        if lbl != "text":
            log_entries[lbl] = pd.to_numeric(log_entries[lbl])
        else:
            log_entries[lbl] = log_entries[lbl].astype(str)
    print(log_entries.dtypes)
    if any([elem is not None for elem in filter_funcs]):
        for i in range(8):
            if filter_funcs[i] is not None:
                current_col = log_entries[column_lbls[i]]
                log_entries = log_entries[filter_funcs[i](current_col)]
            if len(log_entries) == 0:
                return None
    return log_entries

def get_today_data_properties():
    today = datetime.datetime.now()
    filter_txt = f"WHERE log_month = {today.month} AND log_day = {today.day}"
    all_data_today = get_sample_data(filter = filter_txt, target_class = "all")
    if all_data_today.empty:
        all_data_today = get_sample_data(target_class = "all")[-5:]
    status_dict = {}
    survey_interval = gl_ds.get_global_attr("checkin_interval") * 2
    locations = all_data_today['log_loc']
    valences = all_data_today['user_valence']
    activations = all_data_today['user_activation']
    work_time = np.sum(locations.apply(lambda x: x in ['Study Space', 'Workplace'])) * survey_interval
    status_dict['work_time'] = work_time / 60
    status_dict['rest_num'] = get_consecutive_num(locations, ['Eatery', 'Home'])
    status_dict['neg_val'] = get_consecutive_num(valences, [-1])
    status_dict['neg_act'] = get_consecutive_num(activations, [-1])
    return status_dict

def get_consecutive_num(column, valid_classes):
    consecutive_num = 0
    for i in range(1, len(column) + 1):
        if column.iloc[-1 * i] in valid_classes:
            consecutive_num += 1
    return consecutive_num

def convert_tuple_to_series(row):
    data_dict = {}
    for key, elem in zip(emo_col_names[7:], row):
        data_dict[key] = elem
    return pd.Series(data = data_dict)
