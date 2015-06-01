from flask import Blueprint, render_template, current_app, redirect, g, get_template_attribute
import flask_sijax

from flask_application.controllers import TemplateView
from flask_application.profiles.models import *
from flask_application.users.models import User

from flask_application.utils.html import convert_html_entities, sanitize_html

from flask.ext.mobility.decorators import mobilized

from copy import deepcopy
from random import randint
from flask.ext.security import login_required

from flask_application.controllers import TemplateView

users = Blueprint('users', __name__)


class ControlPanelView(TemplateView):
    blueprint = users

    def get(self):
        user = self._get_current_user()
        profiles = user.profiles
        return render_template('users/controlpanel.html', user=user,
                profiles=profiles)

    def create_new_refurence_handler(self, obj_response, content):
        profile_name = content['name']

        err_macro = get_template_attribute('users/_macros.html', 'render_error')
        if not profile_name:
            err_html = err_macro('cannot enter blank name')
            obj_response.html('#error-msg', err_html)
            return

        user = self._get_current_user()

        if len(user.profiles) > 20:
            err_html = err_macro('cannot create more refurences: 20 MAX')
            obj_response.html('#error-msg', err_html)
            return 

        if not Profile.is_name_valid(profile_name):
            err_html = err_macro('name: "' + profile_name + '" already taken')
            obj_response.html('#error-msg', err_html)
            return 

        profile = Profile(username=profile_name)
        profile = Profile.initialize_to_default(profile)
        profile.owner_email = user.email
        profile.save()

        user.profiles.append(profile)
        user.save()

        profiles = user.profiles
        profile_macro = get_template_attribute('users/_macros.html',
                'render_profile_list')
        obj_response.html('#error-msg', '')
        obj_response.html('#profile-list', profile_macro(profiles))

    def delete_refurence_handler(self, obj_response, content):
        profile_name = content['name']

        err_macro = get_template_attribute('users/_macros.html', 'render_error')
        if not profile_name:
            err_html = err_macro('cannot delete blank profile')
            obj_response.html('#error-msg', err_html)
            return

        try:
            profile = Profile.objects.get(username=profile_name)
        except Exception:
            err_html = err_macro('could not find profile: ' + profile_name)
            obj_response.html('#error-msg', err_html)
            return

        user = self._get_current_user()

        for idx in range(0, len(user.profiles)):
            p = user.profiles[idx]
            if p == profile:
                del user.profiles[idx]
                break

        user.save()
        profile.delete()
        profile.save()

        profiles = user.profiles
        profile_macro = get_template_attribute('users/_macros.html',
                'render_profile_list')
        obj_response.html('#error-msg', '')
        obj_response.html('#profile-list', profile_macro(profiles))

    def register_sijax(self):
        g.sijax.register_callback('create_new_refurence',
                self.create_new_refurence_handler)
        g.sijax.register_callback('delete_refurence',
                self.delete_refurence_handler)

    def _get_current_user(self):
        if not current_app.dropbox.is_authenticated:
            return redirect('404')
        dropbox_email = current_app.dropbox.account_info['email']
        try:
            user = User.objects.get(email=dropbox_email)
        except Exception:
            user = User(email=dropbox_email, username=dropbox_email)
            user.save()
        return user

users.add_url_rule('/controlpanel/', view_func=ControlPanelView.as_view('controlpanel'))
