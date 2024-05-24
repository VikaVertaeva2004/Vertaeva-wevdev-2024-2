import io
from flask import render_template, request, redirect, url_for, flash, Blueprint, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from app import db
from check_user import CheckUser
from functools import wraps
import mysql.connector
import math

bp_visit = Blueprint('visit', __name__, url_prefix='/visit')

PER_PAGE = 10

@bp_visit.route('/show')
def show():
    querry = '''
    SELECT COUNT(*) as cnt FROM journal
    '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(querry)
    count = math.ceil((cursor.fetchone().cnt)/PER_PAGE)
    cursor.close()
    querry = '''
    SELECT * FROM journal LIMIT %s OFFSET %s
    '''
    try:
        page = int(request.args.get('page', 1))
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(querry, (PER_PAGE,PER_PAGE*(page-1) ))
        values = cursor.fetchall()
        cursor.close()

    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()
    return render_template('/visits/show.html', values=values, count=count, page=page)

@bp_visit.route('/show_route')
def show_route():
    values=[]

    try:
        cursor = db.connection().cursor(named_tuple=True)

        if current_user.can("show_route"):
            querry = '''
            SELECT path, COUNT(user_id) AS count_path FROM journal GROUP BY path
            '''
            cursor.execute(querry)
        else:
            querry = '''
            SELECT path, COUNT(user_id) AS count_path FROM journal WHERE user_id=%s GROUP BY path
            '''
            cursor.execute(querry, (current_user.id,))

        values = cursor.fetchall()
        cursor.close()
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()

    return render_template('/visits/show_route.html', values=values)

@bp_visit.route('/show_user')
def show_user():
    querry = '''
    SELECT user_id, COUNT(*) as cnt2 FROM journal GROUP BY user_id
    '''
    try:
        cursor = db.connection().cursor(named_tuple=True)
        cursor.execute(querry,)
        values = cursor.fetchall()
        cursor.close()
        
    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()
    return render_template('/visits/show_user.html', values=values)


@bp_visit.route('/send_csv')
def send_csv():
    querry = '''
    SELECT * FROM journal
    '''
    cursor = db.connection().cursor(named_tuple=True)
    cursor.execute(querry)
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