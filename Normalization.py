from flask import Blueprint, render_template, abort, request
import math

from db import mongo

norm_page = Blueprint('norm_page', __name__, template_folder='templates')
items_per_page = 1


@norm_page.route('<name>', defaults={'page': 0})
@norm_page.route('<name>/<int:page>')
def norm(name, page):
    coll = 'norm/' + name
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
    if pagination_end > page_num + 1:
        pagination_end = page_num + 1
        pagination_start = pagination_end - 22
        if pagination_start < 1:
            pagination_start = 1

    return render_template('norm.html', name=name, page=page, items=items, page_num=page_num,
                           pagination_start=pagination_start, pagination_end=pagination_end)


@norm_page.route('<name>/modify', methods=['POST'])
def modify(name):
    coll = 'norm/' + name
    id = int(request.form['id'])
    value = request.form['value']
    if coll in mongo.db.collection_names():
        corp = mongo.db[coll]
    else:
        return abort(404)

    corp.update_one({'id': id}, {'$set': {'corr': value}})

    return ''
