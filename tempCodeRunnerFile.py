from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import pymysql
import pymysql.cursors
import db
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from flask import send_from_directory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import google.generativeai as genai
import json
from flask import send_from_directory
import os

import traceback
from rag_service import RAGService

app = Flask(__name__)
app.secret_key = os.urandom(24
)
@app.route('/')
def index():
    recent_questions = get_recent_questions(5)  
    return render_template('index.html', recent_questions=recent_questions, username=session.get('username'))

rag_service = RAGService(api_key="AIzaSyAt55QVbUbXcFqNGFfxspVrlgW3qKOLOOo")  
@app.route('/ai_chat', methods=['GET', 'POST'])
def ai_chat():
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        if user_input:
            response = rag_service.generate_response(user_input)
            return jsonify({'response': response})
        return jsonify({'response': '請輸入有效的問題。'})
    return render_template('index.html')  
@app.route('/data', methods=['GET', 'POST'])
def test_data():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        print(request.form)
        return f"Received POST request with username: {username} and password: {password}", 200
    else:
        return render_template('data.html')
    
@app.route("/jinja2")
def jinja2():
    data = []
    with open("templates/jinja2.txt") as fin:
        for line in fin:
            line = line[:-1]
            day,wage,hour = line.split("\t")
            data.append((day,wage,hour))
    return render_template("jinja2.html", data=data)

@app.route("/show_add_user")
def show_add_user():
    return render_template("show_add_user.html")

@app.route("/do_add_user" , methods =["POST"])
def do_add_user():
    print(request.form)
    employee_id = request.form.get("employee_id")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    hourly_pay = request.form.get("hourly_pay")
    hire_date = request.form.get("hire_date")
    sql = f""" insert into user (employee_id,first_name,last_name,hourly_pay,hire_date)
            values({employee_id},"{first_name}","{last_name}",{hourly_pay},"{hire_date}")
    """
    print(sql)
    db.insert_or_update_data(sql)
    return "資料已儲存"

def get_conn():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="00000000",
        database="python_mysql",
        charset="utf8"
    )
@app.route('/criminal_law', methods=['GET', 'POST'])
def criminal_law():
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    search_query = request.form.get('search', '')
    
    if search_query:
        sql = """SELECT article_number, law_content 
                 FROM criminal_law 
                 WHERE law_content LIKE %s OR article_number LIKE %s"""
        cursor.execute(sql, (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute("SELECT article_number, law_content FROM criminal_law")
    
    data = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('criminal_law.html', data=data, search_query=search_query)

@app.route('/civil_law', methods=['GET', 'POST'])
def civil_law():
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    search_query = request.form.get('search', '')
    
    if search_query:
        sql = """SELECT article_number, law_content 
                 FROM civil_law 
                 WHERE law_content LIKE %s OR article_number LIKE %s"""
        cursor.execute(sql, (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute("SELECT article_number, law_content FROM civil_law")
    
    data = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('civil_law.html', data=data, search_query=search_query)

@app.route('/constitution', methods=['GET', 'POST'])
def constitution():
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    search_query = request.form.get('search', '')
    
    if search_query:
        sql = """SELECT article_number, law_content 
                 FROM constitution 
                 WHERE law_content LIKE %s OR article_number LIKE %s"""
        cursor.execute(sql, (f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute("SELECT article_number, law_content FROM constitution")
    
    data = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('constitution.html', data=data, search_query=search_query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        account = request.form['account']
        password = request.form['password']
        
        connection = get_conn()
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM login WHERE username=%s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return "該用戶名已存在，請選擇其他用戶名", 400

        cursor.execute("SELECT * FROM login WHERE account=%s", (account,))
        existing_account = cursor.fetchone()
        
        if existing_account:
            return "該帳號已存在，請選擇其他帳號", 400
     
        cursor.execute("INSERT INTO login (username, account, password) VALUES (%s, %s, %s)", (username, account, password))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return render_template('success.html', message="註冊成功！")
    
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        
        connection = get_conn()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT username FROM login WHERE account=%s AND password=%s", (account, password))
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if user:
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return "帳號或密碼錯誤", 400
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  
    return redirect(url_for('login'))  

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 's1092733@gm.pu.edu.tw' 
app.config['MAIL_PASSWORD'] = 'Q124458315'  
app.config['MAIL_DEFAULT_SENDER'] = 's1092733@gm.pu.edu.tw'

mail = Mail(app)

@app.route('/callme', methods=['GET', 'POST'])
def callme():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        subject = request.form['subject']
        message = request.form['message']
        msg = Message(subject,
                      recipients=['s1092733@gm.pu.edu.tw'])
        msg.body = f"""
        From: {name} <{email}>
        Phone: {phone}
        Message:
        {message}
        """
        try:
            mail.send(msg)
            return render_template('success.html', message="感謝您的來信！我們將盡快回覆您。")
        except Exception as e:
            print(str(e))
            return "抱歉，發送郵件時出現問題。請稍後再試。", 500
    return render_template('callme.html')


@app.route('/ask_question', methods=['GET', 'POST'])
def ask_question():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        user_id = get_user_id(session['username'])
        category_id = request.form['category_id']
        title = request.form['title']
        question = request.form['question']
        connection = get_conn()
        cursor = connection.cursor()
        sql = "INSERT INTO questions (user_id, category_id, title, question) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (user_id, category_id, title, question))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('index'))
    categories = get_categories()
    return render_template('ask_question.html', categories=categories)

@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def view_question(question_id):
    question = get_question(question_id)
    answers = get_answers(question_id)
    if request.method == 'POST' and 'username' in session:
        user_id = get_user_id(session['username'])
        content = request.form['answer']
        connection = get_conn()
        cursor = connection.cursor()
        sql = "INSERT INTO answers (question_id, user_id, content) VALUES (%s, %s, %s)"
        cursor.execute(sql, (question_id, user_id, content))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('view_question', question_id=question_id))

    return render_template('view_question.html', question=question, answers=answers)

@app.route('/all_questions')
def all_questions():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    pagination = get_paginated_questions(page, category_id=category_id)
    categories = get_categories()
    
    return render_template('all_questions.html',
                         pagination=pagination,
                         categories=categories,
                         current_category=category_id)
def get_recent_questions(limit):
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    sql = """
    SELECT q.id, q.title, q.created_at, c.name as category_name, l.username
    FROM questions q
    JOIN categories c ON q.category_id = c.id
    JOIN login l ON q.user_id = l.id
    ORDER BY q.created_at DESC
    LIMIT %s
    """
    cursor.execute(sql, (limit,))
    questions = cursor.fetchall()
    cursor.close()
    connection.close()
    return questions


def get_question(question_id):
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    sql = """
    SELECT q.id, q.title, q.question, q.created_at, c.name as category_name, l.username
    FROM questions q
    JOIN categories c ON q.category_id = c.id
    JOIN login l ON q.user_id = l.id
    WHERE q.id = %s
    """
    cursor.execute(sql, (question_id,))
    question = cursor.fetchone()
    cursor.close()
    connection.close()
    return question

def get_answers(question_id):
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    sql = """
    SELECT a.id, a.content, a.created_at, l.username
    FROM answers a
    JOIN login l ON a.user_id = l.id
    WHERE a.question_id = %s
    ORDER BY a.created_at ASC
    """
    cursor.execute(sql, (question_id,))
    answers = cursor.fetchall()
    cursor.close()
    connection.close()
    return answers

def get_all_questions():
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    sql = """
    SELECT q.id, q.title, q.created_at, c.name as category_name, l.username
    FROM questions q
    JOIN categories c ON q.category_id = c.id
    JOIN login l ON q.user_id = l.id
    ORDER BY q.created_at DESC
    """
    cursor.execute(sql)
    questions = cursor.fetchall()
    cursor.close()
    connection.close()
    return questions

def get_categories():
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    sql = """
    SELECT c.id, c.name, COUNT(q.id) as question_count
    FROM categories c
    LEFT JOIN questions q ON c.id = q.category_id
    GROUP BY c.id, c.name
    """
    cursor.execute(sql)
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return categories

def get_user_id(username):
    connection = get_conn()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM login WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] if result else None

def get_questions_by_category(category_id):
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    sql = """
    SELECT q.id, q.title, q.created_at, c.name as category_name, l.username
    FROM questions q
    JOIN categories c ON q.category_id = c.id
    JOIN login l ON q.user_id = l.id
    WHERE q.category_id = %s
    ORDER BY q.created_at DESC
    """
    cursor.execute(sql, (category_id,))
    questions = cursor.fetchall()

    cursor.close()
    connection.close()
    return questions

def get_categories():
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    sql = """
    SELECT c.id, c.name, COUNT(q.id) as question_count
    FROM categories c
    LEFT JOIN questions q ON c.id = q.category_id
    GROUP BY c.id, c.name
    """
    cursor.execute(sql)
    categories = cursor.fetchall()

    cursor.close()
    connection.close()

    return categories

@app.route('/search_questions')
def search_questions():
    search_query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if not search_query:
        return redirect(url_for('all_questions'))
    
    pagination = get_paginated_questions(page, search_query=search_query)
    categories = get_categories()
    
    return render_template('all_questions.html',
                         pagination=pagination,
                         categories=categories,
                         search_query=search_query,
                         current_category=None)

def get_paginated_questions(page, per_page=10, category_id=None, search_query=None):
    connection = get_conn()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    base_sql = """
        FROM questions q
        JOIN categories c ON q.category_id = c.id
        JOIN login l ON q.user_id = l.id
    """
    where_clause = ""
    params = []
    if category_id:
        where_clause = "WHERE q.category_id = %s"
        params.append(category_id)
    
    if search_query:
        where_clause = "WHERE (q.title LIKE %s OR q.question LIKE %s)"
        search_pattern = f'%{search_query}%'
        params.extend([search_pattern, search_pattern])
    count_sql = f"SELECT COUNT(*) as total {base_sql} {where_clause}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()['total']
    offset = (page - 1) * per_page
    data_sql = f"""
        SELECT q.id, q.title, q.created_at, c.name as category_name, l.username
        {base_sql}
        {where_clause}
        ORDER BY q.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    cursor.execute(data_sql, params)
    questions = cursor.fetchall()
    
    cursor.close()
    connection.close()
    total_pages = (total + per_page - 1) // per_page
    return {
        'questions': questions,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    }
if __name__ == '__main__':
    app.run(debug=True)