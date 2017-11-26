import os.path
import pickle

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
from auth import user_permission, admin_permission, login_manager, get_user, users, User
from db import mongo

app = Flask(__name__)

with open(os.path.join(os.path.dirname(__file__), 'passwords.db'), 'rb') as f:
    db = pickle.load(f)
    for user, pw, admin in db['users']:
        users[user] = User(user, pw, is_admin=admin)
    app.secret_key = db['secret']

app.register_blueprint(speech_page, url_prefix='/speech/')
app.register_blueprint(norm_page, url_prefix='/norm/')
app.register_blueprint(lex_page, url_prefix='/lex/')

principals = Principal(app)

login_manager.init_app(app)
mongo.init_app(app)

root = os.path.dirname(__file__)


@app.route('/')
@user_permission.require()
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
        corpus_import(os.path.join(root, 'import', corpus), corp_type)
        return redirect('/')

    corpora = list_import(os.path.join(root, 'import'))
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

    path = os.path.join(root, 'export', corpus)

    corpus_export(path, corpus, corp_type)

    return redirect('/')


@app.errorhandler(PermissionDenied)
def permission_denied(e):
    return redirect(url_for('login'))


class LoginForm(FlaskForm):
    user = StringField()
    passwd = PasswordField()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = LoginForm()

        if form.validate_on_submit():
            user = get_user(form.user.data)

            if user and user.check_pw(form.passwd.data):
                login_user(user)
                identity_changed.send(app, identity=Identity(user.id))
                return redirect(request.args.get('next') or '/')

        return redirect('/login?err')
    else:
        err = False
        if 'err' in request.args:
            err = True
        return render_template('login.html', err=err, form=LoginForm())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    identity_changed.send(app, identity=AnonymousIdentity())
    return redirect(request.args.get('next') or '/')


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(role)


if __name__ == '__main__':
    app.run(debug=True)
