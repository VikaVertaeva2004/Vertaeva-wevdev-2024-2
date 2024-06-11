import io
from flask import render_template, request, redirect, url_for, flash, Blueprint, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from app import db
from functools import wraps
import mysql.connector
import math

bp_visit = Blueprint('visit', __name__, url_prefix='/visit')

PER_PAGE = 10

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@bp_visit.route('/show')
@login_required
def show():
    user_filter = ''
    params = ()
    
    if not current_user.is_admin():
        user_filter = 'WHERE visit_logs.user_id = %s'
        params = (current_user.id, )

    querry_count = f'''
    SELECT COUNT(*) as cnt FROM visit_logs
    {user_filter}
    '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(querry_count, params)
    count = math.ceil((cursor.fetchone().cnt) / PER_PAGE)
    cursor.close()

    querry_data = f'''
    SELECT visit_logs.id, 
           COALESCE(CONCAT_WS(' ', users2.last_name, users2.first_name, users2.middle_name), "Неаутентифицированный пользователь") AS user_full_name, 
           visit_logs.path, 
           visit_logs.created_at
    FROM visit_logs
    LEFT JOIN users2 ON visit_logs.user_id = users2.id
    {user_filter}
    ORDER BY visit_logs.created_at DESC
    LIMIT %s OFFSET %s
    '''
    values = []  
    try:
        page = int(request.args.get('page', 1))
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(querry_data, params + (PER_PAGE, PER_PAGE * (page - 1)))
        values = cursor.fetchall()
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()

    return render_template('/visits/show.html', values=values, count=count, page=page)

@bp_visit.route('/show_route')
@login_required
@admin_required
def show_route():
    page = int(request.args.get('page', 1))
    query_count = '''
    SELECT COUNT(DISTINCT path) as cnt FROM visit_logs
    '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query_count)
    count = math.ceil((cursor.fetchone().cnt) / PER_PAGE)
    cursor.close()

    query_data = '''
    SELECT path, COUNT(user_id) AS count_path 
    FROM visit_logs 
    GROUP BY path 
    LIMIT %s OFFSET %s
    '''
    values = []
    try:
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query_data, (PER_PAGE, PER_PAGE * (page - 1)))
        values = cursor.fetchall()
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()

    return render_template('/visits/show_route.html', values=values, count=count, page=page)


@bp_visit.route('/show_user')
@login_required
@admin_required
def show_user():
    page = int(request.args.get('page', 1))
    query_count = '''
    SELECT COUNT(DISTINCT user_id) as cnt FROM visit_logs
    '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(query_count)
    count = math.ceil((cursor.fetchone().cnt) / PER_PAGE)
    cursor.close()

    query_data = '''
    SELECT visit_logs.user_id, 
           COALESCE(CONCAT_WS(' ', users2.last_name, users2.first_name, users2.middle_name), "Неаутентифицированный пользователь") AS user_full_name,
           COUNT(*) AS cnt2
    FROM visit_logs
    LEFT JOIN users2 ON visit_logs.user_id = users2.id
    GROUP BY visit_logs.user_id
    ORDER BY cnt2 DESC
    LIMIT %s OFFSET %s
    '''
    values = []
    try:
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(query_data, (PER_PAGE, PER_PAGE * (page - 1)))
        values = cursor.fetchall()
        cursor.close()
        
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()

    return render_template('/visits/show_user.html', values=values, count=count, page=page)


@bp_visit.route('/send_csv')
@login_required
def send_csv():
    user_filter = ''
    params = ()

    if not current_user.is_admin():
        user_filter = 'WHERE visit_logs.user_id = %s'
        params = (current_user.id, )

    querry = f'''
    SELECT * FROM visit_logs
    {user_filter}
    '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(querry, params)
    records = cursor.fetchall()
    csv_text = ''
    for record in records:
        csv_text += str(record.id)
        csv_text += ', '
        csv_text += str(record.path)
        csv_text += ', '
        csv_text += str(record.user_id)
        csv_text += ', '
        csv_text += str(record.created_at)
        csv_text += ', '
        csv_text += '\n'
    cursor.close()
    mem = io.BytesIO()
    mem.write(csv_text.encode())
    mem.seek(0)

    return send_file(mem, as_attachment=True, download_name='csv_text.csv')
