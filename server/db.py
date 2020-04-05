#!/usr/bin/python3
import datetime
import server.utill as util
import psycopg2

import server.config as config

def getConnection():
    conn = psycopg2.connect(dbname=config.database,
                            user=config.user,
                            password=config.password,
                            host=config.host,
                            port=config.port)
    return conn

class UserSessionRepo:

    def add(self, sessionId, ip):
        conn = getConnection()

        with conn.cursor() as cursor:
            conn.autocommit = True
            dateTime = datetime.datetime.now()
            values = (sessionId, dateTime, dateTime, ip)

            insert = 'INSERT INTO user_session (session_id, date_create, date_last_active, ip_adress) ' \
                     + 'VALUES (%s, %s, %s, %s) RETURNING id'

            cursor.execute(insert, values)

            self.id = cursor.fetchone()[0]

        return self.id

    def updateUserActive(self, userId):
        conn = getConnection()

        with conn.cursor() as cursor:
            conn.autocommit = True
            dateTime = datetime.datetime.now()
            values = (dateTime, userId)

            update = 'UPDATE user_session SET date_last_active = %s WHERE id = %s'

            cursor.execute(update, values)

class LoadFilesRepo:

    def addFile(self, userId, fileName):
        conn = getConnection()

        with conn.cursor() as cursor:
            conn.autocommit = True
            values = (userId, fileName)

            insert = 'INSERT INTO load_files (user_id, file_name) ' \
                     + 'VALUES (%s, %s) RETURNING id'

            cursor.execute(insert, values)

            self.id = cursor.fetchone()[0]

        return self.id

class MatrixRepo:

    def getNewIndex(self):
        conn = getConnection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = "select nextval('files_id_seq')"

            cursor.execute(select)

            self.id = cursor.fetchone()[0]

        return self.id

    def addMatrix(self, matrix):

        id = self.getNewIndex()

        conn = getConnection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO matrix (id, row_id, column_id, value) VALUES (%s, %s, %s, %s)'


            row_id = 0
            for row in matrix:
                column_id = 0
                for item in row:
                    values = (id, row_id, column_id, item)
                    cursor.execute(insert, values)
                    column_id += 1
                row_id += 1

        return id

    def getMatrix(self, matrix_id):
        matrix = []

        conn = getConnection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT row_id, column_id, "value" FROM matrix WHERE id = %s ORDER BY row_id, column_id'
            cursor.execute(select, (matrix_id,))

            rows = cursor.fetchall()

            row_num = 0
            line = []
            for row in rows:
                if row_num == int(row[0]):
                    line.append(util.format_number(row[2]))
                else:
                    matrix.append(line)
                    row_num += 1
                    line = []
                    line.append(util.format_number(row[2]))
            matrix.append(line)

        return matrix

    def setRow(self, row):

        id = self.getNewIndex()

        conn = getConnection()
        with conn.cursor() as cursor:
            conn.autocommit = True

            insert = 'INSERT INTO matrix (id, row_id, column_id, value) VALUES (%s, %s, %s, %s)'

            column_id = 0
            for item in row:
                values = (id, 0, column_id, item)
                cursor.execute(insert, values)
                column_id += 1

        return id

    def getRow(self, id):
        conn = getConnection()

        with conn.cursor() as cursor:
            conn.autocommit = True

            select = 'SELECT row_id, column_id, "value" FROM matrix WHERE id = %s ORDER BY row_id, column_id'
            cursor.execute(select, (id,))

            rows = cursor.fetchall()

            line = []
            for row in rows:
                line.append(util.format_number(row[2]))

        return line
