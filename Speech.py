import os
import wave
from io import BytesIO

from flask import Blueprint, render_template, abort, send_file, request, make_response
from pymongo import ASCENDING

from auth import user_permission
from db import mongo

speech_page = Blueprint('speech_page', __name__, template_folder='templates')


@speech_page.route('<name>/index')
@user_permission.require()
def index(name):
    coll = 'speech/' + name
    if coll not in mongo.db.collection_names():
        return abort(404)

    corp_info = mongo.db.corpora.find_one({'coll': coll})

    indices = ['default']

    if 'index_num' in corp_info:
        for index in corp_info['index_num'].keys():
            indices.append(index)

    return render_template('speech_index.html', name=name, indices=indices)


@speech_page.route('<name>', defaults={'index': 'default', 'page': 0})
@speech_page.route('<name>/<index>/<int:page>')
@user_permission.require()
def speech(name, index, page):
    coll = 'speech/' + name
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    corp_info = mongo.db.corpora.find_one({'coll': coll})

    if index == 'default':
        item = corp.find_one({'id': page})
        page_num = corp_info['num']
    else:
        if 'index_num' in corp_info and index in corp_info['index_num']:
            item = corp.find_one({'index.{}'.format(index): page})
            page_num = corp_info['index_num'][index]
        else:
            return abort(404)

    if not item:
        return abort(404)

    return render_template('speech.html', name=name, index=index, page=page, item=item, page_num=page_num)


@speech_page.route('<name>/<index>/wav/<int:page>')
@user_permission.require()
def wav(name, index, page):
    coll = 'speech/' + name
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    corp_info = mongo.db.corpora.find_one({'coll': coll})

    if index == 'default':
        item = corp.find_one({'id': page})
    else:
        if 'index_num' in corp_info and index in corp_info['index_num']:
            item = corp.find_one({'index.{}'.format(index): page})
        else:
            return abort(404)

    if not item:
        return abort(404)
    path = item['wav']
    if 'wav_s' in item:
        wav_s = item['wav_s']
        wav_e = item['wav_e']
    else:
        wav_s = -1.0
        wav_e = -1.0

    if not os.path.exists(path):
        return abort(404)

    if wav_s < 0 or wav_e < 0:
        return send_file(path, mimetype='audio/wav')
    else:
        f = wave.open(path, 'rb')
        start = int(wav_s * f.getframerate())
        end = int(wav_e * f.getframerate())
        len = int(end - start)
        f.setpos(start)
        data = f.readframes(len)
        params = f.getparams()
        f.close()

        wav_mem = BytesIO()

        f = wave.open(wav_mem, 'wb')
        f.setparams(params)
        f.setnframes(len)
        f.writeframes(data)
        f.close()

        response = make_response(wav_mem.getvalue())
        response.headers['Content-Type'] = 'audio/wav'
        return response


@speech_page.route('<name>/modify', methods=['POST'])
@user_permission.require()
def modify(name):
    coll = 'speech/' + name
    id = int(request.form['id'])
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    text = corp.find_one({'id': id})['text']

    if 'undo' in request.form:
        corp.update_one({'id': id}, {'$set': {'corr': ''}})
    else:
        value = request.form['value']
        corp.update_one({'id': id}, {'$set': {'corr': value}})

    return ''


@speech_page.route('<name>/regions', methods=['POST'])
@user_permission.require()
def regions(name):
    coll = 'speech/' + name
    id = int(request.form['id'])
    reg_start = request.form.getlist('reg_start[]')
    reg_end = request.form.getlist('reg_end[]')
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


@speech_page.route('<name>/<index>/list')
@user_permission.require()
def list(name, index):
    coll = 'speech/' + name
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    if index == 'default':
        items = corp.find()
    else:
        idx = 'index.{}'.format(index)
        items = corp.find({}, sort=[(idx, ASCENDING)], hint=[(idx, ASCENDING)])

    itemlist = []

    for item in items:
        i = {}
        i['utt'] = item['utt']

        if index == 'default':
            i['id'] = item['id']
        else:
            i['id'] = item['index'][index]

        if item['corr'] or len(item['regions']) > 0:
            i['mod'] = True
        else:
            i['mod'] = False

        itemlist.append(i)

    return render_template('speech_list.html', name=name, index=index, items=itemlist)
