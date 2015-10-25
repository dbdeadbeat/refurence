from flask.ext.security import UserMixin, RoleMixin, user_registered

from flask_application.models import db, FlaskDocument
from flask_application import app
from flask import redirect

from flask_application.profiles.models import Profile


class Role(FlaskDocument, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)


class User(FlaskDocument, UserMixin):
    email = db.StringField(max_length=255, unique=True)
    username = db.StringField(max_length=64, unique=True)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])
    profiles = db.ListField(db.ReferenceField(Profile))

    maximum_profiles = 20

    def _initialize(self):
        pass


@user_registered.connect_via(app)
def user_registered_sighandler(app, user, confirm_token):
    # default_role = app.user_datastore.find_role("User")
    # app.user_datastore.add_role_to_user(user, default_role)

    for rule in app.url_map.iter_rules():
        str_rule = str(rule)
        str_rule = str_rule[1:len(str_rule)]
        if str_rule.startswith(user.username):
            user.delete()
            return redirect('404')
    user.save()

    profile = Profile(username=user.username)
    profile = Profile.initialize_to_default(profile)
    profile.save()
