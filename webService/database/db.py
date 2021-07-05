import mysql.connector
import csv


def connect():
    cnx = mysql.connector.connect(
        host = "localhost",
        user =  'tccuser',
        password = 'wPk4!364',
        database = 'vibraniumDB')
    cursor = cnx.cursor()
    return(cnx, cursor)


def disconnect(cnx, cursor):
    cursor.close()
    cnx.close()
    

def fetchAll(cursor):
    fields = tuple(map(lambda x:x[0], cursor.description))
    result = [dict(zip(fields, row)) for row in cursor.fetchall()]
    return result


def querySelectAllFrom(table, column, value):
    '''
    Query: SELECT * FROM table WHERE column = value
    '''    
    query = f"SELECT * FROM {table} WHERE {column}=(%s)"
    values = [value]
    try:
        cnx, cursor = connect()
        cursor.execute(query, values)
        results = fetchAll(cursor)
        disconnect(cnx, cursor)
        return results

    except mysql.connector.Error as e:
        print(e)
        return []


def querySelectLastFrom(table, pKey, column, value):
    '''
    Query:  SELECT * FROM table WHERE pKey IN (
                SELECT MAX(pKey)
                FROM table
                WHERE column = value
                )
    '''    
    query = f"SELECT * FROM {table} WHERE {pKey} IN (   \
            SELECT MAX({pKey})                          \
            FROM {table}                                \
            WHERE {column}=(%s))"
    value = [value]
    try:
        cnx, cursor = connect()
        cursor.execute(query, value)
        results = fetchAll(cursor)
        disconnect(cnx, cursor)
        return results

    except mysql.connector.Error as e:
        print(e)
        return []


def queryInsertInto(table, columns, values):
    '''
    Query: INSERT INTO table (columnA, ...) VALUES (%s, ...)
    '''
    columns = tuple(columns)
    values  = tuple(values)

    query = f"INSERT INTO {table} {columns} VALUES ("
    for i in columns:
        query += "%s,"
    query = query[:-1] + ")"
    query = query.replace("'","")

    try:
        cnx, cursor = connect()
        cursor.execute(query, values)
        cnx.commit()
        disconnect(cnx, cursor)
    except mysql.connector.Error as e:
        print(e)


def queryUpdate(table, column, newValue, pKey, pValue):
    '''
    Query: UPDATE table SET column = newValue WHERE pKey = pValue
    '''
    query = f"UPDATE {table} SET {column} = %s WHERE {pKey} = %s"
    values = (newValue, pValue)

    try:
        cnx, cursor = connect()
        cursor.execute(query, values)
        cnx.commit()
        disconnect(cnx, cursor)
        return True

    except mysql.connector.Error as e:
        print(e)
        return False


def extractJsonAcq(jsonData):
    '''
    Extract JSON data and return acquisition Fields and Values\n
    Important: anomaly value returned as NULL by default
    '''
    query = "SHOW COLUMNS FROM acquisition"
    try:
        cnx, cursor = connect()
        cursor.execute(query)

        # Return only field names
        fields = list(map(lambda x:x[0], cursor.fetchall()))
        disconnect(cnx, cursor)

        # Remove 'AcqID' because it's AUTO INCREMENTED
        fields.pop(0)

        endpointID  = jsonData['endpointID']
        timeStamp   = jsonData['timeStamp']
        values      = [endpointID, None, timeStamp]

        for axis in ('x','y','z'):
            axisrms     = jsonData[axis]['rms']
            axiscf      = jsonData[axis]['cf']
            axisfreq    = jsonData[axis]['freq']
            axisamp     = jsonData[axis]['amp']
            values.extend([axisrms, axiscf, axisfreq, axisamp])

        return (fields, values)

    except mysql.connector.Error as e:
        print(e)
        return ((),())


def makeCSVfile(table, column, value, size):
    '''
    Make a csv file from a query with specific size
    '''    
    query = f"(SELECT * FROM {table} WHERE {column} = (%s) \
             ORDER BY acqID DESC LIMIT {size}) ORDER BY acqID"
    values = [value]
    try:
        cnx, cursor = connect()
        cursor.execute(query, values)
        with open("query.csv", "w", newline='') as csv_file:
	        writer = csv.writer(csv_file)
	        writer.writerow([i[0] for i in cursor.description])
	        writer.writerows(cursor)
        disconnect(cnx, cursor)

    except mysql.connector.Error as e:
        print(e)