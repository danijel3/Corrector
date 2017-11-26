import bcrypt
from flask_login import LoginManager, UserMixin
from flask_principal import Permission, RoleNeed

admin_role = RoleNeed('admin')
user_role = RoleNeed('user')

admin_permission = Permission(admin_role)
user_permission = Permission(user_role)

login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, id, pw, is_admin=False):
        self.id = id
        self.pw = pw
        self.roles = [user_role]
        if is_admin:
            self.roles.append(admin_role)

    def check_pw(self, pw):
        return bcrypt.hashpw(pw.encode('utf-8'), self.pw) == self.pw


users = {}


def get_user(username):
    if username in users:
        return users[username]
    return


@login_manager.user_loader
def user_loader(username):
    return get_user(username)
