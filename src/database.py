import sqlite3, uuid
import re, uuid, string
import datatypes

class DuplicateError(Exception):
    pass

class NonExistingError(Exception):
    pass

class DataBaseError(Exception):
    pass

def open_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON")
    except:
        raise DataBaseError
    return conn

def row2Event(row):
    return datatypes.Event(row[0], row[1], row[2], row[3], row[4])

def attendingRow2User(row):
    return datatypes.User(row[0])

def escape_quote_sql_value(value):
    return "'"+re.escape(value)+"'"


def add_event_from_json(conn, json):
    return add_event(conn, json['name'], json['location'], json['start_timestamp'], json['end_timestamp'])

def add_event(conn, name, location, start_timestamp, end_timestamp):
    cur = conn.cursor()
    cur.execute("INSERT INTO events (name, location, start_timestamp, end_timestamp) VALUES (%s, %s, %s, %s)" % (escape_quote_sql_value(name), escape_quote_sql_value(location), escape_quote_sql_value(start_timestamp), escape_quote_sql_value(end_timestamp)))
    return cur.lastrowid


def delete_event(conn, event_id):
    sql_check = "SELECT * FROM events WHERE id=%s" % escape_quote_sql_value(event_id)
    sql_delete = "DELETE FROM events WHERE id=%s" % escape_quote_sql_value(event_id)
    delete_if_exists(conn, sql_check, sql_delete)

def get_event(conn, event_id):
    sql = "SELECT * FROM events WHERE id=%s" % escape_quote_sql_value(event_id)
    cur = conn.cursor()
    cur.execute(sql)
    return row2Event(cur.fetchone())

def get_users_attending_event(conn, event_id):
    raise_if_not_exist(conn,"SELECT * FROM events WHERE id=%s" % escape_quote_sql_value(event_id))
    sql = "SELECT email FROM attendings WHERE event_id=%s" % escape_quote_sql_value(event_id)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    res = []
    for row in rows:
        res.append(attendingRow2User(row))
    return res

def count_events(conn, email):
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM attendings WHERE email=%s" % escape_quote_sql_value(email))
    return cur.fetchone()[0]

def list_events(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    rows = cur.fetchall()
    res = []
    for row in rows:
        res.append(row2Event(row))
    return res

def list_user_events(conn, email):
    cur = conn.cursor()
    cur.execute("SELECT * FROM events e, attendings a WHERE e.id=a.event_id AND a.email=%s" % escape_quote_sql_value(email))
    rows = cur.fetchall()
    res = []
    for row in rows:
        res.append(row2Event(row))
    return res

def safe_insert(conn, sql):
    try:
        conn.execute(sql)
        conn.commit()
    except sqlite3.IntegrityError as e:
        if "FOREIGN" in str(e):
            raise NonExistingError
        elif "UNIQUE" in str(e):
            raise DuplicateError
        else:
            raise e

def register_user(conn, email, event_id):
    sql = "INSERT INTO users VALUES (%s)" % escape_quote_sql_value(email)
    safe_insert(conn, sql)

def register_event(conn, email, event_id):
    sql = "INSERT INTO attendings VALUES (%s, %s)" % (escape_quote_sql_value(email), escape_quote_sql_value(event_id))
    safe_insert(conn, sql)

def unregister_event(conn, email, event_id):
    sql_check = "SELECT * FROM attendings WHERE email=%s AND event_id=%s" % (escape_quote_sql_value(email), escape_quote_sql_value(event_id))
    sql_delete = "DELETE FROM attendings WHERE email=%s AND event_id=%s" % (escape_quote_sql_value(email), escape_quote_sql_value(event_id))
    delete_if_exists(conn, sql_check, sql_delete)

def raise_if_not_exist(conn, sql_check_exists):
    cur = conn.cursor()
    cur = conn.execute(sql_check_exists)
    row = cur.fetchone()
    if row is None:
        raise NonExistingError

def delete_if_exists(conn, sql_check_exists, sql_delete):
    raise_if_not_exist(conn, sql_check_exists)
    conn.execute(sql_delete)
    conn.commit()
