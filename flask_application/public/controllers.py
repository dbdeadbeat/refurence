import datetime

from flask import Blueprint, current_app, render_template, url_for

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

# class ThankYouView(TemplateView):
    # blueprint = public
    # route = '/home/thankyou'
    # route_name = 'thankyou'
    # template_name = 'home/register_thankyou.html'

    # def get_context_data(self, *args, **kwargs):
        # return {
            # 'now': datetime.datetime.now(),
            # 'config': current_app.config
        # }


    # def get(self, *args, **kwargs):
        # return self.process(*args, **kwargs)

class AboutView(TemplateView):
    blueprint = public
    route = '/home/about'
    route_name = 'about'
    template_name = 'home/about.html'

    def get(self):
        class Contributor(object):
            def __init__(self, name, img, description, url):
                self.name = name
                self.image = img
                self.description = description
                self.url = url

        contributors = [
                Contributor('deadbeat', 
                    url_for('static', filename='img/contributor-db.png'),
                    'programmer - emo bitch',
                    'http://www.furaffinity.net/user/deadbeathyena/'
                    ),
                Contributor('vixe', 
                    url_for('static', filename='img/contributor-vixe.png'),
                    'programmer - fox with mad skillz; rolls her own, gives no fucks',
                    'http://www.furaffinity.net/user/vixe'
                    ),
                Contributor('ruxley', 
                    url_for('static', filename='img/contributor-ruxley.png'),
                    'consultant - caribou guru',
                    'http://www.furaffinity.net/user/ruxley'
                    ),
                ]
        return render_template('home/about.html', contributors=contributors)
