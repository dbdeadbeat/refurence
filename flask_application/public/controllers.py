import datetime

from flask import Blueprint, current_app, render_template

from flask_application.controllers import TemplateView

from flask.ext.mobility.decorators import mobilized

public = Blueprint('public', __name__)


class IndexView(TemplateView):
    blueprint = public
    route = '/'
    route_name = 'home'
    template_name = 'home/index.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'now': datetime.datetime.now(),
            'config': current_app.config
        }


    def get(self, *args, **kwargs):
        return self.process(*args, **kwargs)


    @mobilized(get)
    def get(self):
        return render_template('mobile/home/index.html')

class ThankYouView(TemplateView):
    blueprint = public
    route = '/home/thankyou'
    route_name = 'thankyou'
    template_name = 'home/register_thankyou.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'now': datetime.datetime.now(),
            'config': current_app.config
        }


    def get(self, *args, **kwargs):
        return self.process(*args, **kwargs)

class AboutView(TemplateView):
    blueprint = public
    route = '/home/about'
    route_name = 'about'
    template_name = 'home/about.html'
