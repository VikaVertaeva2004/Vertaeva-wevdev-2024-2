from flask import Flask, render_template,request, make_response, url_for

app = Flask(__name__) #это мы создали объект -на основе фласк и основным файлом у нас будет app.py
application = app

@app.route('/')#при переходе на главную страничку я хочу вывести helloworld
def index():
    msg = 'Hello world'
    return render_template('index.html',msg=msg)
#при обращении к главной странице ("/"), функция index создает переменную msg со значением 'Hello world' и передает эту переменную в шаблон index.html с помощью render_template. Таким образом, при открытии главной страницы пользователю будет показан HTML-код из файла index.html, где переменная msg будет заменена на 'Hello world'.
@app.route('/argv')
def argv():
    return render_template('argv.html')

@app.route('/calc')
def calc():
    result = ''
    num1 =  request.args.get('num1') 
    oper = request.args.get('operation') 
    num2 = request.args.get('num2')
    if oper == "+": 
        result = int(num1)+ int(num2)
    elif oper == "-":
        result = int(num1) - int(num2)
    elif oper == "*":
        result = int(num1) * int(num2)
    elif oper == "/":
        result = int(num1)/int(num2)

    return render_template('calc.html', result=result)

@app.route('/headers')
def headers():
    return render_template('headers.html')

@app.route('/cookie')
def cookie():
    resp = make_response(render_template('cookie.html'))
    if 'user' in request.cookies:
        resp.delete_cookie('user')
    else:
        resp.set_cookie('user','NoName')
    return resp

@app.route('/form', methods = ['POST', 'GET'])
def form():
    return render_template('form.html' )


if __name__ == "__main__":
    app.run(debug=True)#вывод ошибок, но можно удалить




