from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from app import db
from check_user import CheckUser
from functools import wraps
import mysql.connector

bp_auth = Blueprint('auth',__name__, url_prefix='/auth')

ADMIN_ROLE_ID = 1

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Для доступа необходимо пройти аутентификацию'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)

def check_rights(action):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = None
            if kwargs.get('user_id'):
                user_id = kwargs['user_id']
                user = load_user(user_id)
            if current_user.can(action, user):
                return func(*args, **kwargs)
            else:
                flash("У вас недостаточно прав для доступа к данной странице.", "danger")
                return redirect(url_for('show_users'))
        return wrapper
    return decorator

class User(UserMixin):
    def __init__(self, user_id, user_login, role_id):
        self.id = user_id
        self.login = user_login
        self.role_id = role_id

    def is_admin(self):
        return self.role_id == ADMIN_ROLE_ID

    def can(self, action, record=None):
        check_user = CheckUser(record)
        method = getattr(check_user, action, None)
        if method:
            return method()
        return False

# def load_user(user_id):
#     query = 'SELECT * FROM users2 WHERE users2.id=%s'
#     user = None
#     try:
#         with db.connection().cursor(named_tuple=True) as cursor:
#             cursor.execute(query, (user_id,))
#             user = cursor.fetchone()
        
#         if user:
#             return User(user.id, user.login, user.role_id)
#     except mysql.connector.errors.DatabaseError as e:
#         db.connection().rollback()
#         flash('Database error: {}'.format(e), 'danger')
#     except Exception as e:
#         flash('An error occurred: {}'.format(e), 'danger')
    
#     return None
def load_user(user_id):
    query = 'SELECT * FROM users2 WHERE users2.id=%s'
    user = None
    cursor = db.connection().cursor(named_tuple=True)
    try:
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user.id, user.login, user.role_id)
    except mysql.connector.errors.DatabaseError as e:
        db.connection().rollback()
        flash('Database error: {}'.format(e), 'danger')
    except Exception as e:
        flash('An error occurred: {}'.format(e), 'danger')
    finally:
        cursor.close()
    
    return None

# @bp_auth.route('/login', methods=['POST', 'GET'])
# def login():
#     if request.method == 'POST':
#         login = request.form['login']
#         password = request.form['password']
#         check = request.form.get('secretcheck') == 'on'
#         query = 'SELECT * FROM users2 WHERE users2.login=%s AND users2.password_hash=SHA2(%s,256)'
#         user = None
#         try:
#             with db.connection().cursor(named_tuple=True) as cursor:
#                 cursor.execute(query, (login, password))
#                 user = cursor.fetchone()
#                 cursor.close()  # Ensure the cursor is closed after fetching data

#             if user:
#                 login_user(User(user.id, user.login, user.role_id), remember=check)
#                 param_url = request.args.get('next')
#                 flash('Вы успешно вошли!', 'success')
#                 return redirect(param_url or url_for('index'))
#             else:
#                 flash('Неверный логин или пароль.', 'danger')
#         except mysql.connector.errors.DatabaseError as e:
#             db.connection().rollback()
#             flash('Database error: {}'.format(e), 'danger')
#         except Exception as e:
#             flash('An error occurred: {}'.format(e), 'danger')

#     return render_template('login.html')
@bp_auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        check = request.form.get('secretcheck') == 'on'
        query = 'SELECT * FROM users2 WHERE users2.login=%s AND users2.password_hash=SHA2(%s,256)'
        user = None
        connection = db.connection()
        try:
            cursor = connection.cursor(named_tuple=True)
            cursor.execute(query, (login, password))
            user = cursor.fetchone()
            cursor.close()  # Ensure the cursor is closed after fetching data

            if user:
                login_user(User(user.id, user.login, user.role_id), remember=check)
                param_url = request.args.get('next')
                flash('Вы успешно вошли!', 'success')
                return redirect(param_url or url_for('index'))
            else:
                flash('Неверный логин или пароль.', 'danger')
        except mysql.connector.errors.DatabaseError as e:
            connection.rollback()
            flash('Database error: {}'.format(e), 'danger')
        except Exception as e:
            flash('An error occurred: {}'.format(e), 'danger')
        finally:
            connection.close()

    return render_template('login.html')

@bp_auth.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))
