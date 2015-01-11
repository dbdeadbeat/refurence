import datetime
import math, re

from flask_application import app

from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter('time_ago')
def time_ago(value):
    delta = datetime.datetime.now() - value
    if delta.days == 0:
        formatting = 'today'
    elif delta.days < 10:
        formatting = '{0} days ago'.format(delta.days)
    elif delta.days < 28:
        formatting = '{0} weeks ago'.format(int(math.ceil(delta.days/7.0)))
    elif value.year == datetime.datetime.now().year:
        formatting = 'on %d %b'
    else:
        formatting = 'on %d %b %Y'
    return value.strftime(formatting)

@app.template_filter('nl2br')
@evalcontextfilter
def nl2br(eval_ctx, value):
    # result = u'\n'.join(u'%s' % p.replace('\n', Markup('<br/>')) \
        # for p in _paragraph_re.split(escape(value)))
    # if eval_ctx.autoescape:
        # result = Markup(result)
    # return result
    return value
