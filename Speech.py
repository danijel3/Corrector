import os
import wave
from io import BytesIO
from pathlib import Path

from flask import Blueprint, render_template, abort, send_file, request, make_response

from auth import edit_permission
from db import mongo

speech_page = Blueprint('speech_page', __name__, template_folder='templates')

root = Path('audio')


def format(secs):
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f'{int(h):02}:{int(m):02}:{s:0.2f}'


@speech_page.route('<name>', defaults={'page': 0})
@speech_page.route('<name>/<int:page>')
@edit_permission.require()
def speech(name, page):
    coll = 'speech_' + name
    corp = mongo.db[coll]
    if corp is None:
        return abort(404)

    page_num = corp.count_documents({})
    item = corp.find_one({'id': page})
    item['start_str'] = format(item['start'])
    item['end_str'] = format(item['end'])

    if not item:
        return abort(404)

    return render_template('speech.html', name=name, page=page, item=item, page_num=page_num)


@speech_page.route('<name>/wav/<int:page>')
@edit_permission.require()
def wav(name, page):
    coll = 'speech_' + name
    corp = mongo.db[coll]
    if corp is None:
        return abort(404)

    item = corp.find_one({'id': page})

    if not item:
        return abort(404)

    path = root / item['file']
    wav_s = item['start']
    wav_e = item['end']

    if not os.path.exists(path):
        return abort(404)

    if wav_s < 0 or wav_e < 0:
        return send_file(path, mimetype='audio/wav')
    else:
        f = wave.open(str(path), 'rb')
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
@edit_permission.require()
def modify(name):
    coll = 'speech_' + name
    corp = mongo.db[coll]
    if corp is None:
        return abort(404)

    if 'undo' in request.form:
        corp.update_one({'id': id}, {'$set': {'corr': ''}})
    else:
        value = request.form['value']
        corp.update_one({'id': id}, {'$set': {'corr': value}})

    return ''


@speech_page.route('<name>/regions', methods=['POST'])
@edit_permission.require()
def regions(name):
    coll = 'speech_' + name
    corp = mongo.db[coll]
    if corp is None:
        return abort(404)

    id = int(request.form['id'])
    reg_start = request.form.getlist('reg_start[]')
    reg_end = request.form.getlist('reg_end[]')

    reg = []
    for s, e in zip(reg_start, reg_end):
        reg.append((float(s), float(e)))

    corp.update_one({'id': id}, {'$set': {'regions': reg}})

    return ''


list_items_per_page = 10


@speech_page.route('<name>/list')
@edit_permission.require()
def list(name):
    coll = 'speech_' + name
    corp = mongo.db[coll]
    if corp is None:
        return abort(404)

    items = corp.find()

    itemlist = {}

    for item in items:
        if item['file'] not in itemlist:
            itemlist[item['file']] = []

        i = {'utt': f'{format(item["start"])} - {format(item["end"])}', 'id': item['id']}

        if ('corr' in item and item['corr']) or ('regions' in item and len(item['regions']) > 0):
            i['mod'] = True
        else:
            i['mod'] = False

        itemlist[item['file']].append(i)

    return render_template('speech_list.html', name=name, items=itemlist)
