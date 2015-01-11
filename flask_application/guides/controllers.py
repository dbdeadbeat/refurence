import datetime

from flask import Blueprint, current_app, render_template

from flask_application.controllers import TemplateView
from flask_application.guides.models import Guide

from flask.ext.mobility.decorators import mobilized

guides = Blueprint('guides', __name__)


class ListView(TemplateView):
    blueprint = guides
    route = '/guides'
    route_name = 'list'
    template_name = 'guides/list.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'content': 'This is the guide page'
        }

    def get(self):
        return render_template('guides/list.html', guides=Guide.objects)

    @mobilized(get)
    def get(self):
        return render_template('mobile/guides/list.html', guides=Guide.objects)

class DetailView(TemplateView):
    blueprint = guides
    route = '/guides/<slug>'
    route_name = 'detail'
    template_name = 'guides/detail.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'content': 'This is the guide page'
        }

    def get(self, slug):
        guide = Guide.objects.get_or_404(slug=slug)
        return render_template('guides/detail.html', guide=guide)

    @mobilized(get)
    def get(self, slug):
        guide = Guide.objects.get_or_404(slug=slug)
        return render_template('mobile/guides/detail.html', guide=guide)
