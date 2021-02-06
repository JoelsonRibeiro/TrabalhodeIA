from flask import Flask, render_template,Response,json, request, redirect, url_for,flash,session,g,stream_with_context
from werkzeug.utils import secure_filename
from os import path,getcwd,remove
from db import DataBase as Db
import time
import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from reconhecimento import Face

import cv2
import numpy as np
import urllib.request
import ssl

app = Flask(__name__)
app.secret_key="UmaAiSystem-2021"
app.config['file_allowed'] = ['image/png','image/jpeg']
app.config['storage'] = path.join(getcwd(), 'storage')
app.db = Db()
app.config['SERVER_NAME'] = '127.0.0.1:3000'
fc = Face(app)

usuario = ''



cam =  cv2.VideoCapture(0)
def get_frame():
        success, img = cam.read()
        status,user= fc.face_detect_live(img)
        ret, jpeg = cv2.imencode('.jpg', img)
        if status:
            return jpeg.tobytes(),user
        else:
            return jpeg.tobytes(),'no user'


def gen_frames(user=None):
    global founded
    while True:
        data = get_frame()
        frame= data[0]
        yield(b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'+ frame + b'\r\n')
    cam.release()



@app.route('/',methods=['GET','POST'])
def facelog():
    session.pop('user',None)
    if request.method =='POST':
        success, img = cam.read()
        status,user= fc.face_detect_live(img)
        if status:
            adm = app.db.selectadm('SELECT username FROM adms WHERE username = ?',(user,))
            session.pop('user',None)
            session['user'] = user
            return redirect(url_for('index'))
        else:
            flash(u'Login Falhou!','alert-danger')
    return render_template('logface.html')


@app.route('/log',methods=['GET','POST'])
def login():
    session.pop('user',None)
    if request.method =='POST':
        username = request.form['username']
        password = request.form['password']

        adm = app.db.selectadm('SELECT username,password FROM adms WHERE username = ?',(username,))
        if adm and check_password_hash(adm[1],password):
            session.pop('user',None)
            session['user'] = request.form['username']
            return redirect(url_for('index'))
        else:
            flash(u'Login Falhou!','alert-danger')

    return render_template('login.html')

@app.route('/index')
def index():
    if g.user:
        pass
        #return render_template('index.html')
    else:
        return redirect(url_for('/'))

    results = app.db.select('SELECT users.id,users.name,users.created,faces.filename FROM users,faces WHERE users.id=faces.user_id')
    return render_template('index.html',data={'users':results,'user':g.user})

@app.route('/livereg',methods=['GET','POST'])
def livereg():
    if request.method =='POST':
        success, img = cam.read()
        conhecidas = path.join(app.config['storage'],'conhecidas')
        nome = request.form['username']
        filename = nome+'.jpeg'
        file_path = path.join(conhecidas, filename)
        cv2.imwrite(f'{file_path}',img)
        tam = fc.fconfirm(file_path)
        tam = int(tam)
        print('Tamanho = ',tam)
        if tam != 1:
            remove(file_path)
            flash(u'Imagem possui mais de uma ou não possui nenhuma face','alert-danger')
        else:
            criado = datetime.datetime.now()
            ultimo_id =app.db.insert('INSERT INTO users(name, created) VALUES (?,?)',[nome, criado])
            if ultimo_id :
                face_id = app.db.insert('INSERT INTO faces (user_id,filename,created) VALUES (?,?,?)',[ultimo_id,filename,criado])
                if face_id:
                    flash(u'Adicionado com Sucesso','alert-success')
                    return redirect(url_for('index'))
                else:
                    flash(u'Não Adicionado','alert-danger')
    return render_template('live.html')

@app.before_request
def before_request():
    g.user =None
    if 'user' in session:
        g.user = session['user']

@app.route('/getsession')
def getsession():
    if 'user' in session:
        return session['user']

    return 'Não Logado'


@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')


@app.route('/add_user',methods=['POST'])
def add_user():
    if request.method =='POST':
        if 'filec' not in request.files :
            flash('Arquivo Necessário','alert-danger')
        else:
            file = request.files['filec']

            filename = secure_filename(file.filename)
            conhecidas = path.join(app.config['storage'],'conhecidas')
            file_path = path.join(conhecidas, filename)
            file.save(file_path)


            tam = fc.fconfirm(file)
            tam = int(tam)
            print('Tamanho = ',tam)
            if file.mimetype not in app.config['file_allowed']:
                flash(u'Por Favor envie um ficheiro com a extensão jpeg ou png','alert-warning')
            else:
                if tam != 1:
                    try:
                        remove(file_path)
                    except:
                        pass
                    flash(u'Imagem possui mais de uma ou não possui nenhuma face','alert-danger')
                else:
                    nome = request.form['nome']

                    criado = datetime.datetime.now()
                    ultimo_id =app.db.insert('INSERT INTO users(name, created) VALUES (?,?)',[nome, criado])
                    if ultimo_id :
                        face_id = app.db.insert('INSERT INTO faces (user_id,filename,created) VALUES (?,?,?)',[ultimo_id,filename,criado])
                        if face_id:
                            flash(u'Adicionado com Sucesso','alert-success')
                        else:
                            remove(file_path)
                            flash(u'Não Adicionado','alert-danger')


    return redirect(url_for('index'))

@app.route('/edit/<id>',methods=['POST','GET'])
def get_user(id):
    results = app.db.query('SELECT users.id,users.name,faces.filename FROM users,faces WHERE users.id=? AND faces.user_id=? ',(id,id))
    return render_template('edit.html',user=results[0])


@app.route('/update/<id>',methods=['POST'])
def update_user(id):
    if request.method =='POST':
        filen = request.files['file']
        if 'file' not in request.files or request.files['file'].filename=='' :
            results = app.db.query('SELECT faces.filename FROM faces WHERE faces.user_id=? ',(id,))
            filename=results[0][0]
            nome = request.form['nome']
            result = app.db.update('UPDATE users SET name= ? WHERE id=?',(nome,id))
            results2 = app.db.update('UPDATE faces SET filename=? WHERE user_id=? ',(filename,id))
            if result and results2:
                flash(u'Atualizado com Sucesso','alert-success')
            else:
                flash(u'Não Atualizado','alert-danger')
        else:
            file = request.files['file']
            print(file.filename)
            if file.mimetype not in app.config['file_allowed']:
                flash(u'Por Favor envie um ficheiro com a extensao jpeg ou png','alert-warning')
            else:
                nome = request.form['nome']
                filename = secure_filename(file.filename)
                conhecidas = path.join(app.config['storage'],'conhecidas')
                file_path = path.join(conhecidas, filename)
                file.save(file_path)
                print(nome,filename)
                results = app.db.update('UPDATE users SET name= ? WHERE users.id=?',(nome,id))
                results2 = app.db.update('UPDATE faces SET filename=? WHERE faces.user_id=? ',(filename,id))
                if results:
                    flash(u'Atualizado com Sucesso','alert-success')
                else:
                    flash(u'Não Atualizado','alert-danger')


    return redirect(url_for('index'))

@app.route('/delete/<string:id>',methods=['POST','GET'])
def delete_user(id):

    result = app.db.delete('DELETE FROM users WHERE id=?',(id,))
    results2 = app.db.delete('DELETE FROM faces WHERE user_id=? ',(id,))
    if result and results2:
        flash(u'Removido com Sucesso','alert-success')
    else:
        flash(u'Não Removido','alert-danger')
    return redirect(url_for('index'))

@app.route('/reconhecer',methods=['POST'])
def reconhecer():
    if request.method =='POST':
        if 'file' not in request.files :
            flash('Arquivo Necessário')
        else:
            file = request.files['file']
            if file.mimetype not in app.config['file_allowed']:
                flash(u'Por Favor envie um ficheiro com a extensão jpeg ou png',['rec','alert-warning'])
            else:
                filename = secure_filename(file.filename)
                unknown_storage = path.join(app.config['storage'],'enviadas')
                file_path = path.join(unknown_storage, filename)
                file.save(file_path)
                nome = fc.face_detect(file_path)
                print(len(nome),nome)
                if len(nome) == 0:
                    flash('Não foi possível verificar faces na imagem',['rec','alert-warning'])
                elif len(nome) == 1 and nome[0] != 'Desconhecido':
                    flash(nome[0],['rec','alert-success'])
                elif len(nome) == 1 and nome[0] == 'Desconhecido':
                    flash(nome[0],['rec','alert-warning'])
                else:
                    flash(nome,['rec','alert-warning'])

    return redirect(url_for('index'))


@app.route('/live')
def live():
    return Response((gen_frames()),mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':

    app.run('127.0.0.1',3000, debug=True)
