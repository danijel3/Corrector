from flask import Flask, render_template, request, redirect, url_for
import os.path

from Normalization import norm_page
from Lexicon import lex_page
from Speech import speech_page

from Corpus import *

app = Flask(__name__)
app.register_blueprint(speech_page, url_prefix='/speech/')
app.register_blueprint(norm_page, url_prefix='/norm/')
app.register_blueprint(lex_page, url_prefix='/lex/')

from db import mongo

mongo.init_app(app)

root = os.path.dirname(__file__)

io_pwd = 'olaujelajajo'


@app.route('/')
def index():
    corpora = mongo.db.corpora.find();
    return render_template('index.html', corpora=corpora)


@app.route('/import', methods=['GET'])
def import_list():
    pwd = request.args['pass']
    if pwd != io_pwd:
        return redirect(url_for('static', filename='incorrect_password.html'))

    corpus = request.args.get('corp')
    type = request.args.get('type')

    if corpus and type:
        corpus_import(os.path.join(root, 'import', corpus), type)
        return redirect('/')

    corpora = list_import(os.path.join(root, 'import'))
    return render_template('import.html', corpora=corpora, pwd=pwd)


@app.route('/remove', methods=['GET'])
def remove_corpus():
    pwd = request.args['pass']
    corpus = request.args['corp']
    if pwd != io_pwd:
        return redirect(url_for('static', filename='incorrect_password.html'))

    corpus_remove(corpus)

    return redirect('/')


@app.route('/export', methods=['GET'])
def export_corpus():
    pwd = request.args['pass']
    corpus = request.args['corp']
    type = request.args['type']
    if pwd != io_pwd:
        return redirect(url_for('static', filename='incorrect_password.html'))

    path = os.path.join(root, 'export', corpus)

    corpus_export(path, corpus, type)

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
