from flask import Blueprint, render_template, abort, request
import math
import re

from db import mongo

lex_page = Blueprint('lex_page', __name__, template_folder='templates')
items_per_page = 100


@lex_page.route('<name>', defaults={'page': 0})
@lex_page.route('<name>/<int:page>')
def show(name, page):
    coll = 'lex/' + name
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    item_num = mongo.db.corpora.find_one({'coll': coll})['num']
    page_num = int(math.ceil(item_num / float(items_per_page)))

    if page >= page_num:
        return abort(403)

    start = page * items_per_page

    items = corp.find({'id': {'$gte': start}}).limit(items_per_page)

    pagination_start = page - 10
    if pagination_start < 1:
        pagination_start = 1
    pagination_end = pagination_start + 22
    if pagination_end > page_num:
        pagination_end = page_num
        pagination_start = pagination_end - 22
        if pagination_start < 1:
            pagination_start = 1

    return render_template('lex.html', name=name, page=page, items=items, page_num=page_num,
                           pagination_start=pagination_start, pagination_end=pagination_end)


re_sp = re.compile('\s+')


@lex_page.route('<name>/modify', methods=['POST'])
def modify(name):
    coll = 'lex/' + name
    id = int(request.form['id'])
    idx = request.form['index']
    value = request.form['value']
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    value = re_sp.split(value.strip())

    corp.update_one({'id': id}, {'$set': {'phon.' + idx: value}})

    return ''


@lex_page.route('<name>/add', methods=['POST'])
def add(name):
    coll = 'lex/' + name
    id = int(request.form['id'])
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    corp.update_one({'id': id}, {'$push': {'phon': []}})

    return ''


@lex_page.route('<name>/rem', methods=['POST'])
def rem(name):
    coll = 'lex/' + name
    id = int(request.form['id'])
    idx = int(request.form['index'])
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    phones = corp.find_one({'id': id})['phon']

    phones.pop(idx);

    corp.update_one({'id': id}, {'$set': {'phon': phones}})

    return ''
