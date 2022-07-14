#Packages
import sqlite3
import re
import os

CWD = os.getcwd()
if r"\Project Lip" not in CWD:
    CWD += r"/Project Lip"
print(CWD)
ICON_PATH = CWD + r"/images/notif_icon_test.png"
#Establishing connection to database
global_db = CWD + r'/databases/global_vals.db'
data_conn = sqlite3.connect(global_db, check_same_thread=False)
data_crsr = data_conn.cursor()

def global_tbl_setup():
    """
    This function sets up a database for the global variables to be stored in.
    """ 
    
    generate_global_tbl = f"""
    CREATE TABLE IF NOT EXISTS global_data (
        attr_name VARCHAR(50),
        val
    );
    """
    data_crsr.execute(generate_global_tbl)
    data_conn.commit()

def get_all_attr_names():
    """
    Returns a list containing the name of all attributes currently existing in global_database.

    Returns:
        List: a list of Strings for the attributes in global_database.
    """
    attr_sql = f'SELECT attr_name FROM global_data'
    data_crsr.execute(attr_sql)
    attr_names = data_crsr.fetchall()
    return [p[0] for p in attr_names]

def get_global_attr(attr_name):
    """
    Get the value of a global attribute whose name is attr_name.

    Args:
        attr_name (str): The attribute name whose value needs to be acquired.
    
    Returns:
        Any: the value of that global attribute which the query is made on.
    """
    attr_sql = f'SELECT val FROM global_data WHERE attr_name = "{attr_name}"'
    data_crsr.execute(attr_sql)
    attr_val = data_crsr.fetchone()
    if attr_val is None:
        return None
    else:
        real_val_repr = attr_val[0]
        if real_val_repr == 'FALSE':
            return False
        elif real_val_repr == 'TRUE':
            return True
        elif type(real_val_repr) is float or type(real_val_repr) is int:
            return real_val_repr
        elif real_val_repr.isdigit():
            return int(real_val_repr)
        else:
            return real_val_repr

def set_global_attr(attr_name, val):
    """
    Sets a global attribute in the database with name attr_name to a value val.

    Args:
        attr_name (str): The attribute name whose value is to be set to val.
        val (Any): The new purposed value of the attribute of attr_name.
    """
    val = repr(val)
    if get_global_attr(attr_name) is None:
        set_attr_sql = f'INSERT INTO global_data VALUES ("{attr_name}", {val})'
    else:
        set_attr_sql = f'''UPDATE global_data 
                           SET val = {val}
                           WHERE attr_name = "{attr_name}"
                        '''
    data_crsr.execute(set_attr_sql)
    data_conn.commit()

def transform_msg(selected_line, replace_txt = ('',)):
    """
    Transforms a message noted by selected_line into a version whose specific
    keywords are converted into the values noted by replace_txt.

    Args:
        selected_line (str): The line of message to be transformed
        replace_txt (tuple): A tuple whose contents note the substitute values
        of keywords in selected_line.
    
    Returns:
        str: The transformed version of message.
    """
    params = re.findall(r'({[^{}]+})', selected_line)
    for param_pair in zip(params, replace_txt[:len(params)]):
        replacement = get_global_attr(param_pair[0][1:-1])
        selected_line = selected_line.replace(
            param_pair[0], 
            replacement or param_pair[1]
        )
    return selected_line
