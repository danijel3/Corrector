import os
import codecs
import urllib
import shutil
import re

from db import mongo
from pymongo import DESCENDING

re_sp = re.compile('\s+')


def list_import(path):
    corpora = []
    for file in os.listdir(path):
        if os.path.isdir(os.path.join(path, file)):
            corpora.append(file)

    return corpora


def corpus_import(path, type):
    name = urllib.quote_plus(os.path.basename(path))
    collname = type + '/' + name
    if collname in mongo.db.collection_names():
        mongo.db[collname].drop()
        mongo.db.corpora.delete_many({'coll': collname})
    coll = mongo.db[collname]

    if type == 'norm':
        db = []

        corr = None
        if os.path.exists(os.path.join(path, 'corr.txt')):
            corr = codecs.open(os.path.join(path, 'corr.txt'), encoding='utf-8')

        with codecs.open(os.path.join(path, 'input.txt'), encoding='utf-8') as orig:
            with codecs.open(os.path.join(path, 'output.txt'), encoding='utf-8') as norm:
                id = 0
                for ol in orig:
                    nl = norm.readline().strip()
                    cl = ''
                    if corr:
                        cl = corr.readline().strip()
                        if cl == nl:
                            cl = ''
                    item = {'id': id, 'orig': ol.strip(), 'norm': nl, 'corr': cl}
                    db.append(item)
                    id += 1
        if corr:
            corr.close()
        coll.insert_many(db)

    elif type == 'lex':
        with codecs.open(os.path.join(path, 'lexicon.txt'), encoding='utf-8') as f:
            id = 0
            db = {}
            for l in f:
                tok = re_sp.split(l.strip())
                orto = tok[0]
                phon = tok[1:]
                if not orto in db:
                    db[orto] = {'id': id, 'orto': orto, 'phon': [phon]}
                    id += 1
                else:
                    db[orto]['phon'].append(phon)
            db = sorted(db.values(), key=lambda x: x['id'])
            coll.insert_many(db)
    elif type == 'speech':
        with codecs.open(os.path.join(path, 'wav.scp'), encoding='utf-8') as f:
            wav = {}
            for l in f:
                s = l.find(' ')
                if s > 0:
                    id = l[:s].strip()
                    p = l[s + 1:].strip()
                    wav[id] = p

        edits = None
        if os.path.exists(os.path.join(path, 'edits.txt')):
            edits = {}
            with codecs.open(os.path.join(path, 'edits.txt'), encoding='utf-8') as f:
                for l in f:
                    s = l.find(' ')
                    if s > 0:
                        id = l[:s].strip()
                        ed = int(l[s + 1:].strip())
                        edits[id] = ed

        segs = None
        if os.path.exists(os.path.join(path, 'segments')):
            segs = {}
            with codecs.open(os.path.join(path, 'segments'), encoding='utf-8') as f:
                for l in f:
                    t = l.split(' ')
                    segs[t[0]] = (t[1], float(t[2]), float(t[3]))

        with codecs.open(os.path.join(path, 'text'), encoding='utf-8') as f:
            text = []
            id = 0
            for l in f:
                s = l.find(' ')
                if s > 0:
                    utt_id = l[:s].strip()
                    t = l[s + 1:].strip()
                    eds = 0
                    wer = 0
                    if (edits) and utt_id in edits:
                        eds = edits[utt_id]
                        wer = float(eds) / len(t.split(' '))
                    if segs:
                        seg = segs[utt_id]
                        wav_id = seg[0]
                        wav_s = seg[1]
                        wav_e = seg[2]
                    else:
                        wav_id = utt_id
                        wav_s = -1.0
                        wav_e = -1.0
                    text.append({'id': id, 'utt': utt_id, 'text': t, 'wav': wav[wav_id], 'corr': '', 'regions': [],
                                 'edits': eds, 'wer': wer, 'wav_s': wav_s, 'wav_e': wav_e})
                    id += 1

        coll.insert_many(text)
        coll.create_index([('edits', DESCENDING)])
        coll.create_index([('wer', DESCENDING)])

    corp = {'kind': type, 'name': name, 'coll': collname, 'num': id}
    mongo.db.corpora.insert_one(corp)


def corpus_export(path, name, type):
    if not name in mongo.db.collection_names():
        return

    coll = mongo.db[name]

    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)

    if type == 'norm':
        with codecs.open(os.path.join(path, 'corr.txt'), mode='w', encoding='utf-8') as f:
            for item in coll.find():
                f.write(item['corr'].replace('\n',' ') + '\n')
    elif type == 'lex':
        with codecs.open(os.path.join(path, 'lexicon.txt'), mode='w', encoding='utf-8') as f:
            for item in coll.find():
                ort = item['orto']
                for ph in item['phon']:
                    f.write(u'{} {}\n'.format(ort, ' '.join(ph)))

    elif type == 'speech':
        with codecs.open(os.path.join(path, 'text'), mode='w', encoding='utf-8') as f:
            with codecs.open(os.path.join(path, 'erase_segments'), mode='w', encoding='utf-8') as fseg:
                for item in coll.find():
                    if 'corr' in item and item['corr']:
                        f.write(u'{} {}\n'.format(item['utt'], item['corr']))
                    else:
                        f.write(u'{} {}\n'.format(item['utt'], item['text']))
                    if 'regions' in item:
                        for reg in item['regions']:
                            fseg.write(u'{} {} {}\n'.format(item['utt'], reg[0], reg[1] - reg[0]))


def corpus_remove(name):
    mongo.db[name].drop()
    mongo.db.corpora.delete_many({'coll': name})
