import os

import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, g
from flask_login import current_user, login_user, login_required, logout_user
from flask_principal import Principal, identity_loaded, identity_changed, UserNeed, Identity, \
    PermissionDenied, AnonymousIdentity
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField

from Corpus import *
from Lexicon import lex_page
from Normalization import norm_page
from Speech import speech_page
from auth import admin_permission, login_manager, get_user, edit_permission
from db import mongo

app = Flask(__name__)

with open(Path(__file__).absolute().parent / 'secret', 'rb') as f:
    app.secret_key = f.read()

app.register_blueprint(speech_page, url_prefix='/speech/')
app.register_blueprint(norm_page, url_prefix='/norm/')
app.register_blueprint(lex_page, url_prefix='/lex/')

app.config['MONGO_URI'] = f'mongodb://{os.environ["DB_HOST"]}:{os.environ["DB_PORT"]}/corrector'

principals = Principal(app)
login_manager.init_app(app)
mongo.init_app(app)

root = Path(__file__).absolute().parent


@app.route('/')
@edit_permission.require()
def index():
    is_admin = False
    if g.identity.can(admin_permission):
        is_admin = True
    corpora = mongo.db.corpora.find()
    return render_template('index.html', corpora=corpora, is_admin=is_admin)


@app.route('/import', methods=['GET'])
@admin_permission.require()
def import_list():
    corpus = request.args.get('corp')
    corp_type = request.args.get('type')

    if corpus and corp_type:
        corpus_import(root / 'import' / corpus, corp_type)
        return redirect('/')

    corpora = list_import(root / 'import')
    return render_template('import.html', corpora=corpora)


@app.route('/remove', methods=['GET'])
@admin_permission.require()
def remove_corpus():
    corpus = request.args['corp']

    corpus_remove(corpus)

    return redirect('/')


@app.route('/export', methods=['GET'])
@admin_permission.require()
def export_corpus():
    corpus = request.args['corp']
    corp_type = request.args['type']

    corpus_export(root / 'export' / corpus, corpus, corp_type)

    return redirect('/')


@app.errorhandler(PermissionDenied)
def permission_denied(e):
    return redirect(url_for('login'))


principals = Principal(app)

login_manager.init_app(app)


class LoginForm(FlaskForm):
    user = StringField()
    passwd = PasswordField()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = LoginForm()

        if form.validate_on_submit():
            user = get_user(form.user.data)

            if user and user.retry_count < 10 and user.check_pw(form.passwd.data):
                mongo.db.users.update_one({'username': user.id}, {'$set': {'retry_count': 0}})
                login_user(user)
                identity_changed.send(app, identity=Identity(user.id))

                if user.need_change_pw():
                    return redirect('/password')

                next = request.args.get('next')
                if not next or next == 'None':
                    return redirect('/')
                else:
                    return redirect(next)
            else:
                if not user:
                    return redirect('/login?err')

                if user.retry_count >= 10:
                    return redirect('/login?blocked')

                if user:
                    mongo.db.users.update_one({'username': user.id}, {'$inc': {'retry_count': 1}})
                    # if user.retry_count == 9:
                    #     send_blocked_email(user.id)

                return redirect('/login?err')
    else:
        err = False
        if 'err' in request.args:
            err = True
        blocked = False
        if 'blocked' in request.args:
            blocked = True
        return render_template('login.html', err=err, blocked=blocked, form=LoginForm())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    identity_changed.send(app, identity=AnonymousIdentity())
    return redirect(request.args.get('next') or '/')


num = re.compile('[0-9]')
cap = re.compile('[A-Z]')
low = re.compile('[a-z]')
spc = re.compile('[\W_]')


class PasswordForm(FlaskForm):
    old = PasswordField()
    password = PasswordField()
    repeat = PasswordField()

    def pass_valid(self):
        if len(self.password.data) < 8:
            print('len')
            return False
        if not num.search(self.password.data):
            print('num')
            return False
        if not cap.search(self.password.data):
            print('cap')
            return False
        if not low.search(self.password.data):
            print('low')
            return False
        if not spc.search(self.password.data):
            print('spc')
            return False
        return True


@app.route('/password', methods=['GET', 'POST'])
@login_required
def password():
    if request.method == 'POST':
        form = PasswordForm()

        if form.validate_on_submit():

            user = current_user

            if not user or not user.check_pw(form.old.data):
                return redirect('/password?err=1')
            if form.password.data != form.repeat.data:
                return redirect('/password?err=2')
            if not form.pass_valid():
                return redirect('/password?err=3')

            p = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())
            mongo.db.users.update_one({'username': user.id}, {'$set': {'password': p, 'change': False}})

        return redirect('/')
    else:
        err = False
        if 'err' in request.args:
            err = request.args['err']
        return render_template('password.html', err=err, form=PasswordForm())


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(role)
