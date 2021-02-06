import csv
from werkzeug.security import generate_password_hash
from datetime import datetime
from db import DataBase as Db
db = Db()
class Administradores:
    def __init__(self):
        self.data = 'adms.csv'

    def file_read(self):
        list = []
        with open(self.data) as f:
            f_reader = csv.reader(f,delimiter=',')
            conta_linhas = 0
            for row in f_reader:
                if conta_linhas == 0:
                    conta_linhas +=1
                else:
                    username =row[0]
                    password =row[1]
                    conta_linhas +=1
                    list.append(row)
        print()
        return list

    def insert(self,username,password):

        adms = db.insert('INSERT INTO adms (username,password,created) VALUES (?,?,?)',[username,password,datetime.now()])
        return adms


F1 = Administradores()

admins = F1.file_read()

for i,j in admins:
    adm = db.selectadm('SELECT username,password FROM adms WHERE username = ?',(i,))
    if len(adm) != 0:
        pass
    else:
        F1.insert(i,generate_password_hash(j))
    

    #print('username:',i,'Password: ',generate_password_hash(j))
