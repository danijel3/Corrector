import os

from flask import Blueprint, render_template, abort, send_file, request

from db import mongo

from pymongo import DESCENDING

speech_page = Blueprint('speech_page', __name__, template_folder='templates')

items_per_page = 10


@speech_page.route('<name>', defaults={'page': 0})
@speech_page.route('<name>/<int:page>')
def speech(name, page):
    coll = 'speech/' + name
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    item_num = mongo.db.corpora.find_one({'coll': coll})['num']

    item = corp.find_one({'id': page})

    pagination_start = page - 10
    if pagination_start < 1:
        pagination_start = 1
    pagination_end = pagination_start + 22
    if pagination_end > item_num:
        pagination_end = item_num
        pagination_start = pagination_end - 22
        if pagination_start < 1:
            pagination_start = 1

    return render_template('speech.html', name=name, page=page, item=item, item_num=item_num,
                           pagination_start=pagination_start, pagination_end=pagination_end)


@speech_page.route('<name>/wav/<int:page>')
def wav(name, page):
    coll = 'speech/' + name
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    path = corp.find_one({'id': page})['wav']

    if not os.path.exists(path):
        return abort(404)

    return send_file(path, mimetype='audio/wav')


@speech_page.route('<name>/modify', methods=['POST'])
def modify(name):
    coll = 'speech/' + name
    id = int(request.form['id'])
    value = request.form['value']
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    text = corp.find_one({'id': id})['text']

    if text != value:
        corp.update_one({'id': id}, {'$set': {'corr': value}})
    else:
        corp.update_one({'id': id}, {'$set': {'corr': ''}})

    return ''


@speech_page.route('<name>/regions', methods=['POST'])
def regions(name):
    coll = 'speech/' + name
    id = int(request.form['id'])
    reg_start = request.form.getlist('reg_start[]');
    reg_end = request.form.getlist('reg_end[]');
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    reg = []
    for s, e in zip(reg_start, reg_end):
        reg.append((float(s), float(e)))

    corp.update_one({'id': id}, {'$set': {'regions': reg}})

    return ''


list_items_per_page = 10


@speech_page.route('<name>/list', defaults={'offset': 0})
@speech_page.route('<name>/list/<int:offset>')
def list(name, offset):
    coll = 'speech/' + name
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    index_by = 'edits'
    page_args = ''
    if 'wer' in request.args:
        page_args = '?wer'
        index_by = 'wer'

    items = corp.find().sort(index_by, DESCENDING).limit(list_items_per_page).skip(offset)

    return render_template('speech_list.html', collname=name, items=items, next=offset + list_items_per_page,
                           prev=offset - list_items_per_page, page_args=page_args)
