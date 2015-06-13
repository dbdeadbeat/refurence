import json, os

from flask import current_app, url_for

from flask.ext.script import Command
from flask.ext.security.confirmable import confirm_user

from flask_application.models import FlaskDocument
from flask_application.profiles.models import Profile, ImageTable
from flask_application.guides.models import Guide, Step


class ResetDB(Command):
    """Drops all tables and recreates them"""
    def run(self, **kwargs):
        self.drop_collections()

    @staticmethod
    def drop_collections():
        for klass in FlaskDocument.all_subclasses():
            klass.drop_collection()


class PopulateDB(Command):
    """Fills in predefined data to DB"""
    users = (
                ('user', 'user@user.com', 'password', ['user'], True),
            )
    def run(self, **kwargs):
        self.create_roles()
        self.create_users()
        self.create_profiles()
        self.create_guides()

    @staticmethod
    def create_roles():
        for role in ('admin', 'editor', 'author', 'user'):
            current_app.user_datastore.create_role(name=role, description=role)
        current_app.user_datastore.commit()

    @staticmethod
    def create_users():
        for u in PopulateDB.users:
            user = current_app.user_datastore.create_user(
                username=u[0],
                email=u[1],
                password=u[2],
                roles=u[3],
                active=u[4]
            )
            confirm_user(user)

            current_app.user_datastore.commit()

    @staticmethod
    def create_profiles():
        for u in PopulateDB.users:
            profile = Profile(username=u[0])
            profile = Profile.initialize_to_default(profile)
            profile.is_example = True
            profile.save()

    @staticmethod
    def create_guides():
        guides = PopulateDB._get_guides_data()
        for g in guides:
            g.save()

    @staticmethod
    def _get_guides_data():
        with open('resources/guides.json', 'r') as f:
            content = f.read()
        guides = json.loads(content)['guides']
        out = []
        for g in guides:
            newGuide = Guide(title=g['title'], slug=g['slug'], abstract=g['abstract'])
            for s in g['steps']:
                if s['img']:
                    newStep = Step(body=s['body'], img=s['img'])
                else:
                    newStep = Step(body=s['body'])
                newGuide.steps.append(newStep)
            out.append(newGuide)
        return out

class UpdateDB(PopulateDB):
    def run(self, **kwargs):
        self.update_guides()

    @staticmethod
    def update_guides():
        Guide.drop_collection()
        guides = UpdateDB._get_guides_data()
        for g in guides:
            g.save()

class AddDefaultProfile(PopulateDB):
    def run(self, **kwargs):
        self._add_defaultprofile()

    @staticmethod
    def _add_defaultprofile():
        profile = Profile.objects(is_default=True)
        if profile:
            profile.delete()

        profile = Profile.create_default_profile()

