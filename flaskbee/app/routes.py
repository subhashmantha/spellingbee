from flask import render_template
from . import app

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Subhash'}
    return render_template('index.html', title='Home', user=user)