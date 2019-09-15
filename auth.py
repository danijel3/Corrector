import bcrypt
from flask_login import LoginManager, UserMixin
from flask_principal import RoleNeed, Permission

from db import mongo

admin_role = RoleNeed('admin')
corrector_role = RoleNeed('corrector')

roles = {'admin': admin_role, 'editor': corrector_role}

admin_permission = Permission(admin_role)
edit_permission = Permission(corrector_role, admin_role)

login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, id, str_roles, retry_count):
        self.id = id
        self.str_roles = str_roles
        self.roles = []
        for r in str_roles:
            self.roles.append(roles[r])
        self.retry_count = retry_count

    def check_pw(self, pw):
        db_pw = mongo.db.users.find_one({'username': self.id})['password']
        return bcrypt.hashpw(pw.encode('utf-8'), db_pw) == db_pw

    def need_change_pw(self):
        user = mongo.db.users.find_one({'username': self.id})
        if 'change' in user:
            return user['change']
        else:
            return False

    def has_role(self, role):
        return role in self.str_roles


def get_user(username):
    user = mongo.db.users.find_one({'username': username})
    if not user:
        return None

    if 'retry_count' not in user:
        user['retry_count'] = 0

    return User(username, user['roles'], user['retry_count'])


@login_manager.user_loader
def user_loader(username):
    return get_user(username)
