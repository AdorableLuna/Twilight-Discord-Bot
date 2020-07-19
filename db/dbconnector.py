import json
import mysql.connector
from mysql.connector.connection import MySQLConnection
from mysql.connector import pooling

with open('./config.json', 'r') as cjson:
    config = json.load(cjson)

class DBConnector(object):

    def __init__(self):
        self.host = config["DATABASE"]["HOST"]
        self.user = config["DATABASE"]["USER"]
        self.passwd = config["DATABASE"]["PASSWORD"]
        self.database = config["DATABASE"]["SCHEMA"]
        self.auth_plugin = config["DATABASE"]["AUTH_PLUGIN"]
        self.dbconn = None

    # creats new connection
    def create_pool(self):
        return mysql.connector.pooling.MySQLConnectionPool(pool_name="pynative_pool",
                                                           pool_size=5,
                                                           pool_reset_session=True,
                                                           host=self.host,
                                                           database=self.database,
                                                           user=self.user,
                                                           password=self.passwd)
