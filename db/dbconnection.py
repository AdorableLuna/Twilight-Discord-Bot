import mysql.connector
import logging
from db import dbconnector as dbc

class DBConnection(object):
    def __init__(self):
        self.connection_pool = dbc.DBConnector().create_pool()

    def get_connection(self):
        return self.connection_pool.get_connection()

    def insert(self, query, values = []):
        try:
            connection = self.get_connection()

            if connection.is_connected():
                cursor = connection.cursor(prepared = True)

                if values:
                    cursor.execute(query, values)
                else:
                    cursor.execute(query)
                connection.commit()
        except mysql.connector.Error as error:
            logging.error("Parameterized query failed: {}".format(error))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def delete(self, query):
        try:
            connection = self.get_connection()

            if connection.is_connected():
                cursor = connection.cursor(prepared = True)

                cursor.execute(query)
                connection.commit()
        except mysql.connector.Error as error:
            logging.error("Parameterized query failed: {}".format(error))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def select(self, query, multipleRows = False):
        try:
            connection = self.get_connection()

            if connection.is_connected():
                cursor = connection.cursor(dictionary = True)

                cursor.execute(query)
                if multipleRows:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
        except mysql.connector.Error as error:
            logging.error("Parameterized query failed: {}".format(error))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

                return result

    # This will return the first booster with a keystone,
    # if there are no keystone holders then it returns the first booster to sign up
    def selectPriorityBooster(self, role, groupid, limit):
        try:
            connection = self.get_connection()

            if connection.is_connected():
                query = f"""SELECT {role} FROM (
                            (SELECT B.id, B.`user` as '{role}' FROM mythicplus.booster B INNER JOIN mythicplus.keystone K
                            ON B.groupid = K.groupid AND B.`user` = K.`user` WHERE K.groupid = '{groupid}' AND B.`role` = '{role}' AND K.has_keystone = 1 ORDER BY B.id ASC LIMIT 1)
                            UNION
                            (SELECT B.id, B.`user` as '{role}' FROM mythicplus.booster B INNER JOIN mythicplus.keystone K
                            ON B.groupid = K.groupid AND B.`user` = K.`user` WHERE K.groupid = '{groupid}' AND B.`role` = '{role}' AND K.has_keystone = 0 ORDER BY B.id ASC LIMIT {limit})
                        ) UNIONED
                        LIMIT {limit}"""
                cursor = connection.cursor(dictionary = True)

                cursor.execute(query)
                result = cursor.fetchall()
        except mysql.connector.Error as error:
            logging.error("Parameterized query failed: {}".format(error))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

                return result
