import sqlite3
from os import path,getcwd

dbUrl = 'database.db'

conn = sqlite3.connect(dbUrl)
cObj = conn.cursor()
cObj.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created datetime NOT NULL)")
cObj.execute("CREATE TABLE IF NOT EXISTS faces(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL, filename TEXT, created datetime NOT NULL)")
cObj.execute("CREATE TABLE IF NOT EXISTS adms(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL, password TEXT NOT NULL, created datetime NOT NULL)")
conn.commit()
conn.close()

class DataBase:
    def __init__(self):
        self.connection = sqlite3.connect(dbUrl,check_same_thread=False)

    def query(self, q, arg=()):
        cursor = self.connection.cursor()


        cursor.execute(q, arg)
        results = cursor.fetchall()
        cursor.close()
        return results


    def insert(self, q, arg=()):
        cursor = self.connection.cursor()
        cursor.execute(q,arg)

        self.connection.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def select(self, q, arg=()):
        cursor = self.connection.cursor()

        return cursor.execute(q,arg)

    def selectadm(self, q, arg=()):
        cursor = self.connection.cursor()
        cursor.execute(q,arg)
        results = cursor.fetchone()
        cursor.close()
        return results

    def update(self, q, arg=()):
        cursor = self.connection.cursor()
        result = cursor.execute(q,arg)
        self.connection.commit()
        return result
    def delete(self, q, arg=()):
        cursor = self.connection.cursor()
        result = cursor.execute(q,arg)
        self.connection.commit()
        return result
