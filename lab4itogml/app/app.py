from typing import Dict
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from mysql_db import MySQL
import mysql.connector
import re

app = Flask(__name__)

application = app
 
app.config.from_pyfile('config.py')

db = MySQL(app)

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа необходимо пройти аутентификацию'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, user_id, user_login):
        self.id = user_id
        self.login = user_login


def password_validation(password: str) -> bool:
    reg = re.compile(r'''^(?=.*?[a-zа-я])(?=.*?[A-ZА-Я])(?=.*?[0-9])[-A-ZА-Яa-zа-я\d~!?@#$%^&*_+()\[\]{}></\\|"'.,:;]{8,128}$''')
    if reg.match(password):
        return True
    else:
        return False


def login_validation(login: str) -> bool:
    reg = re.compile(r'^[0-9a-zA-Z]{5,}$')
    if reg.match(login):
        return True
    else:
        return False

def validate(login: str, password: str, last_name: str, first_name: str) -> Dict[str, str]:
    errors = {}
    if not login:
        errors['l_class'] = "is-invalid"
        errors['l_message_class'] = "invalid-feedback"
        errors['l_message'] = "Логин не должен быть пустым"
    elif not login_validation(login):
        errors['l_class'] = "is-invalid"
        errors['l_message_class'] = "invalid-feedback"
        errors['l_message'] = "Логин должен состоять только из латинских букв и цифр и иметь длину не менее 5 символов"
    
    if not password:
        errors['p_class'] = "is-invalid"
        errors['p_message_class'] = "invalid-feedback"
        errors['p_message'] = "Пароль не должен быть пустым"
    elif not password_validation(password):
        errors['p_class'] = "is-invalid"
        errors['p_message_class'] = "invalid-feedback"
        errors['p_message'] = '''Пароль не удовлетворяет одному из следующих требований:
не менее 8 символов;
не более 128 символов;
как минимум одна заглавная и одна строчная буква;
только латинские или кириллические буквы;
как минимум одна цифра;
только арабские цифры;
без пробелов;
Другие допустимые символы:~ ! ? @ # $ % ^ & * _ - + ( ) [ ] { } > < / \ | " ' . , : ;
            '''
    
    if not last_name:
        errors['ln_class'] = "is-invalid"
        errors['ln_message_class'] = "invalid-feedback"
        errors['ln_message'] = "Фамилия не должна быть пустой"
    
    if not first_name:
        errors['fn_class'] = "is-invalid"
        errors['fn_message_class'] = "invalid-feedback"
        errors['fn_message'] = "Имя не должно быть пустым"
    
    return errors
# def validate(login: str, password: str, last_name: str, first_name: str) -> Dict[str, str]:
#     errors = {}
#     if not password_validation(password):
#         errors['p_class'] = "is-invalid"
#         errors['p_message_class'] = "invalid-feedback"
#         errors['p_message'] = '''Пароль не удовлетворяет одному из следующих требований:
# не менее 8 символов;
# не более 128 символов;
# как минимум одна заглавная и одна строчная буква;
# только латинские или кириллические буквы;
# как минимум одна цифра;
# только арабские цифры;
# без пробелов;
# Другие допустимые символы:~ ! ? @ # $ % ^ & * _ - + ( ) [ ] { } > < / \ | " ' . , : ;
#             '''
#     if not login_validation(login):
#         errors['l_class'] = "is-invalid"
#         errors['l_message_class'] = "invalid-feedback"
#         errors['l_message'] = "Логин должен состоять только из латинских букв и цифр и иметь длину не менее 5 символов"
#     if len(login):
#         errors['l_class'] = "is-invalid"
#         errors['l_message_class'] = "invalid-feedback"
#         errors['l_message'] = "Логин не должен быть пустым"
#     if len(password):
#         errors['p_class'] = "is-invalid"
#         errors['p_message_class'] = "invalid-feedback"
#         errors['p_message'] = "Пароль не должен быть пустым"
#     if len(last_name):
#         errors['ln_class'] = "is-invalid"
#         errors['ln_message_class'] = "invalid-feedback"
#         errors['ln_message'] = "Фамилия не должна быть пустой"
#     if len(first_name):
#         errors['fn_class'] = "is-invalid"
#         errors['fn_message_class'] = "invalid-feedback"
#         errors['fn_message'] = "Имя не должно быть пустым"
#     return errors


@login_manager.user_loader
def load_user(user_id):
    query = 'SELECT * FROM users2 WHERE users2.id=%s'
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(user.id, user.login)
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        check = request.form.get('secretcheck') == 'on'
        query = 'SELECT * FROM users2 WHERE users2.login=%s AND users2.password_hash=SHA2(%s,256)'
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query, (login, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            login_user(User(user.id, user.login), remember=check)
            param_url = request.args.get('next')
            flash('Вы успешно вошли!', 'success')
            return redirect(param_url or url_for('index'))
        flash('Ошибка входа!', 'danger')
    return render_template('login.html')


@app.route('/logout', methods = ['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/users/')
@login_required
def show_users():
    query = 'SELECT * FROM users2'
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()
    return render_template('users/index.html',users=users)


@app.route('/users/create', methods = ['POST', 'GET'])
@login_required
def create():
    if request.method == 'POST':
        login = request.form['login']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        password = request.form['password']
        errors = validate(login, password, last_name, first_name)
        if len(errors.keys()) > 0:
            return render_template('users/create.html', **errors)
        try:
            query = '''
                insert into users2 (login, last_name, first_name, middle_name, password_hash)
                VALUES (%s, %s, %s, %s, SHA2(%s, 256))
                '''
            cursor = db.connection().cursor(named_tuple=True)
            cursor.execute(query, (login, last_name, first_name, middle_name, password))
            db.connection().commit()
            flash(f'Пользователь {login} успешно создан.', 'success')
            cursor.close()
        except mysql.connector.errors.DatabaseError:
            db.connection().rollback()
            flash(f'При создании пользователя произошла ошибка.', 'danger')
            return render_template('users/create.html')
        
    return render_template('users/create.html')


@app.route('/users/show/<int:user_id>') 
def show_user(user_id):
    query = 'SELECT * FROM users2 WHERE users2.id=%s'
    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
    return render_template('users/show.html', user=user)


@app.route('/users/edit/<int:user_id>', methods=["POST", "GET"])
def edit(user_id):
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        try:
            query = '''
                UPDATE users2 set first_name = %s, last_name = %s, middle_name = %s where id = %s
                '''
            cursor = db.connection().cursor(named_tuple=True)
            cursor.execute(query, (first_name, last_name, middle_name, user_id))
            db.connection().commit()
            flash(f'Данные пользователя {first_name} успешно обновлены.', 'success')
            cursor.close()
        except mysql.connector.errors.DatabaseError:
            db.connection().rollback()
            flash(f'При обновлении пользователя произошла ошибка.', 'danger')
            return render_template('users/edit.html')

    query = 'SELECT  * FROM users2 WHERE users2.id=%s'
    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
    return render_template('users/edit.html', user=user)


@app.route('/users/delete/')
@login_required
def delete():
    try:
        user_id = request.args.get('user_id')
        query = '''
            DELETE from users2 where id = %s
            '''
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query, (user_id,))
        db.connection().commit()
        flash(f'Пользователь {user_id} успешно удален.', 'success')
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()
        flash(f'При удалении пользователя произошла ошибка.', 'danger')
        return render_template('users/index.html', user_id=user_id)

    return redirect(url_for('show_users'))


@app.route('/pass_change', methods=["POST", "GET"])
@login_required
def change():
    if request.method == "POST":
        user_id = current_user.id
        password = request.form['password']
        n_password = request.form['n_password']
        n_password_2 = request.form['n2_password']
        query = '''
            SELECT * FROM `users2` WHERE id = %s and password_hash = SHA2(%s, 256)
            '''
        user = None
        try:
            with db.connection().cursor(named_tuple=True) as cursor:
                cursor.execute(query, (user_id, password))
                user = cursor.fetchone()
        except mysql.connector.errors.DatabaseError:
            db.connection().rollback()
            flash(f'При проверке старого пароля возникла ошибка.', 'danger')
            return render_template('users/change.html')
        if not user:
            flash(f'Старый пароль не соответствует текущему', 'danger')
            return render_template('users/change.html')
        elif not password_validation(n_password):
            flash(f'Новый пароль не соответствует требованиям', 'danger')
            return render_template('users/change.html')
        elif n_password != n_password_2:
            flash(f'Пароли не совпадают', 'danger')
            return render_template('users/change.html')
        else:
            query = '''
                UPDATE `users2` SET password_hash = SHA2(%s, 256) where id = %s
                '''
            try:
                with db.connection().cursor(named_tuple=True) as cursor:
                    cursor.execute(query, (n_password, user_id))
                    db.connection().commit()
                flash(f'Пароль успешно обновлен.', 'success')
                return redirect(url_for('index'))
            except mysql.connector.errors.DatabaseError:
                db.connection().rollback()
                flash(f'При обновлении пароля возникла ошибка.', 'danger')
                return render_template('users/change.html')
    else:
        return render_template('users/change.html')
