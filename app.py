from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    1/0
    return 'hi for lunats'