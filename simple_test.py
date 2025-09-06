from flask import Flask
import os
import uuid

app = Flask(__name__)

@app.route('/')
def index():
    with open('simple_site.html', 'r') as f:
        return f.read()


@app.route('/test')
def test():
    return "Test works!"

if __name__ == '__main__':
    app.run(debug=True)