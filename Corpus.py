import re
import shutil
from pathlib import Path

from db import mongo

re_sp = re.compile('\s+')


def list_import(path: Path):
    corpora = []
    for file in path.iterdir():
        if file.is_dir():
            corpora.append(file.name)

    return corpora


def corpus_import(path: Path, type: str):
    name = path.name
    collname = type + '/' + name
    if collname in mongo.db.collection_names():
        mongo.db[collname].drop()
        mongo.db.corpora.delete_many({'coll': collname})
    coll = mongo.db[collname]

    id = 0
    indices_num = {}

    if type == 'norm':
        db = []

        corr = None
        if (path / 'corr.txt').exists():
            corr = open(path / 'corr.txt')

        with open(path / 'input.txt') as orig:
            with open(path / 'output.txt')as norm:
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
        with open(path / 'lexicon.txt')as f:
            id = 0
            db = {}
            for l in f:
                tok = re_sp.split(l.strip())
                orto = tok[0]
                phon = tok[1:]
                if orto not in db:
                    db[orto] = {'id': id, 'orto': orto, 'phon': [phon]}
                    id += 1
                else:
                    db[orto]['phon'].append(phon)
            db = sorted(list(db.values()), key=lambda x: x['id'])
            coll.insert_many(db)
    elif type == 'speech':
        with open(path / 'wav.scp') as f:
            wav = {}
            for l in f:
                s = l.find(' ')
                if s > 0:
                    id = l[:s].strip()
                    p = l[s + 1:].strip()
                    wav[id] = p

        edits = None
        if (path / 'edits.txt').exists():
            edits = {}
            with open(path / 'edits.txt')as f:
                for l in f:
                    s = l.find(' ')
                    if s > 0:
                        id = l[:s].strip()
                        ed = int(l[s + 1:].strip())
                        edits[id] = ed

        segs = None
        if (path / 'segments').exists():
            segs = {}
            with open(path / 'segments') as f:
                for l in f:
                    t = l.split(' ')
                    segs[t[0]] = (t[1], float(t[2]), float(t[3]))

        index = {}
        indices = []
        if (path / 'index').exists():
            with open(path / 'index') as f:
                indices = f.readline().strip().split(' ')
                for idx in indices:
                    indices_num[idx] = 0

                for l in f:
                    ind = {}
                    i = l.split(' ')
                    for x, n in enumerate(i[1:]):
                        n = int(n)
                        if n >= 0:
                            idx = indices[x]
                            ind[idx] = n
                            indices_num[idx] += 1
                    index[i[0]] = ind

        with open(path / 'text') as f:
            text = []
            id = 0
            for l in f:
                s = l.find(' ')
                if s > 0:
                    utt_id = l[:s].strip()
                    t = l[s + 1:].strip()
                    eds = 0
                    wer = 0
                    if edits and utt_id in edits:
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

                    idx = {}
                    if utt_id in index:
                        idx = index[utt_id]

                    text.append({'id': id, 'utt': utt_id, 'text': t, 'wav': wav[wav_id], 'corr': '', 'regions': [],
                                 'edits': eds, 'wer': wer, 'wav_s': wav_s, 'wav_e': wav_e, 'index': idx})
                    id += 1

        coll.insert_many(text)
        for idx in indices:
            coll.create_index(f'index.{idx}', sparse=True)

    corp = {'kind': type, 'name': name, 'coll': collname, 'num': id, 'index_num': indices_num}
    mongo.db.corpora.insert_one(corp)


def corpus_export(path: Path, name: str, type: str):
    if name not in mongo.db.collection_names():
        return

    coll = mongo.db[name]

    if path.exists():
        shutil.rmtree(str(path))

    path.mkdir(parents=True)

    if type == 'norm':
        with open(path / 'corr.txt', 'w') as f:
            for item in coll.find():
                f.write(item['corr'].replace('\n', ' ') + '\n')
    elif type == 'lex':
        with open(path / 'lexicon.txt', 'w') as f:
            for item in coll.find():
                ort = item['orto']
                for ph in item['phon']:
                    f.write(f'{ort} {" ".join(ph)}\n')

    elif type == 'speech':
        with open(path / 'text', 'w') as f:
            with open(path / 'erase_segments', 'w') as fseg:
                for item in coll.find():
                    if 'corr' in item and item['corr']:
                        f.write(f'{item["utt"]} {item["corr"]}\n')
                    else:
                        f.write(f'{item["utt"]} {item["text"]}\n')
                    if 'regions' in item:
                        for reg in item['regions']:
                            fseg.write(f'{item["utt"]} {reg[0]} {reg[1] - reg[0]}\n')


def corpus_remove(name):
    mongo.db[name].drop()
    mongo.db.corpora.delete_many({'coll': name})
