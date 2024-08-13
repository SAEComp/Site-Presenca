from flask import Flask, render_template, url_for, redirect, jsonify, request, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from functools import wraps 
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
from defs import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'

#formulário de login
class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)])
    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)])
    submit = SubmitField('Login')

#pagina principal
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'saecomp' and form.password.data == 'saecomp123':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

#verificar se o login foi satisfeito
def login_required(f):
    @wraps(f) 
    def wrap(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

#pagina principal
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

#salvar os códigos lidos 
@app.route('/save_code', methods=['POST'])
@login_required
def save_code():
    data = request.json
    code = data.get('code', '')

    if code:
        with open('codes.txt', 'r') as file:
            codes = file.read().splitlines()
        if code not in codes:
            with open('codes.txt', 'a') as file:
                file.write(code + '\n')
            return jsonify({'status': 'success', 'message': 'Código salvo com sucesso!'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Código não fornecido.'}), 400

#executar diariamente a função diariamente()
scheduler = BackgroundScheduler()
scheduler.add_job(func=diariamente, trigger=CronTrigger(hour=0, minute=0))
scheduler.start()

#garantir que quando finalizar a função nao será mais executada
atexit.register(lambda: scheduler.shutdown(wait=False))

if __name__ == "__main__":
    app.run(debug=True)
