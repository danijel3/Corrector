import pickle
from os.path import exists

import bcrypt

users = []
secret_key = ''


def hash(p):
    return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt())


if exists('passwords.db'):
    with open('passwords.db', 'rb') as f:
        db = pickle.load(f)
        for u, p, a in db['users']:
            users.append((u, p, a))
        secret_key = db['secret']

# users.append(('admin', hash('password'), True))
# users.append(('user', hash('password'), False))
# secret_key='secret_key'

with open('passwords.db', 'wb') as f:
    db = {'users': users, 'secret': secret_key}
    pickle.dump(db, f)

print('Saved users:')
for u, p, a in users:
    print('user: {}, pw: {}, admin: {}'.format(u, p, a))
print('Secret: {}'.format(secret_key))
