from flask import Blueprint, render_template, current_app, redirect, g, get_template_attribute
from flask_application.controllers import TemplateView
from flask_application.profiles.models import Profile
from flask_application.users.models import User
#  from flask.ext.mobility.decorators import mobilized

import re


users = Blueprint('users', __name__)


class ControlPanelView(TemplateView):
    blueprint = users

    def get(self):
        user = self._get_current_user()
        self.make_dropbox_coherent(user)
        return render_template('users/controlpanel.html', user=user,
                profiles=user.profiles, maximum_profiles=User.maximum_profiles)

    #  @mobilized(get)
    #  def get(self):
        #  user = self._get_current_user()
        #  profiles = user.profiles
        #  return render_template('mobile/users/controlpanel.html', user=user,
                #  profiles=profiles, maximum_profiles=User.maximum_profiles)

    def create_new_refurence_handler(self, obj_response, content):
        profile_name = content['name']

        user = self._get_current_user()
        err_macro = get_template_attribute('users/_macros.html', 'render_error')
        if len(user.profiles) >= User.maximum_profiles:
            err_html = err_macro('cannot create more refurences: maximum reached')
            obj_response.html('#error-msg', err_html)
            return

        try:
            ControlPanelView.validate_refurence_name(profile_name)
        except Exception as e:
            err_html = err_macro("error: " + str(e))
            obj_response.html('#error-msg', err_html)
            return

        profile_name = profile_name.lower()

        if not Profile.is_name_valid(profile_name):
            err_html = err_macro('name: "' + profile_name + '" already taken')
            obj_response.html('#error-msg', err_html)
            return

        profile = Profile(username=profile_name)
        profile = Profile.initialize_to_default(profile)
        profile.owner_email = user.email
        profile.save()
        profile.dropbox_root().share()

        #  profiles = user.profiles
        user.profiles.append(profile)
        user.save()

        profile_macro = get_template_attribute('users/_macros.html', 'render_profile_list')
        obj_response.html('#error-msg', '')
        obj_response.html('#profile-list', profile_macro(user.profiles,
            User.maximum_profiles))

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
        profile.delete()
        profile.save()
        user.save()

        user = self._get_current_user()
        profile_macro = get_template_attribute('users/_macros.html', 'render_profile_list')
        obj_response.html('#error-msg', '')
        obj_response.html('#profile-list', profile_macro(user.profiles,
            User.maximum_profiles))

    def make_dropbox_coherent(self, user):
        refurences = current_app.dropbox.client.metadata('/')['contents']

        for p in user.profiles:
            pass

    def register_sijax(self):
        g.sijax.register_callback('create_new_refurence', self.create_new_refurence_handler)
        g.sijax.register_callback('delete_refurence', self.delete_refurence_handler)

    def _get_current_user(self):
        if not current_app.dropbox.is_authenticated:
            return redirect('404')
        try:
            dropbox_email = current_app.dropbox.account_info['email']
        except Exception as e:
            return redirect('404')

        try:
            user = User.objects.get(email=dropbox_email)
        except Exception:
            user = User(email=dropbox_email, username=dropbox_email)
            user.save()
        user.profiles = Profile.objects(owner_email=user.username)
        return user

    @staticmethod
    def validate_refurence_name(name):
        if not name:
            raise Exception('name cannot be empty')
        if re.match('^[\w-]+$', name) is None:
            raise Exception('name can only contain alphanumeric characters or dashes')
        if len(name) > 80:
            raise Exception('name is too long')

users.add_url_rule('/controlpanel/', view_func=ControlPanelView.as_view('controlpanel'))
