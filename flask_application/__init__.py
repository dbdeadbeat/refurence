import os
import imp
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, request

FLASK_APP_DIR = os.path.dirname(os.path.abspath(__file__))
print 'app dir', FLASK_APP_DIR


app = Flask(
    __name__,
    template_folder=os.path.join(FLASK_APP_DIR, '..', 'templates'),
    static_folder=os.path.join(FLASK_APP_DIR, '..', 'static')
)

#  Config
app.config.from_object('flask_application.config.app_config')
app.logger.info("Config: %s" % app.config['ENVIRONMENT'])

#  Logging
import logging
logging.basicConfig(
    level=app.config['LOG_LEVEL'],
    format='%(asctime)s %(levelname)s: %(message)s '
           '[in %(pathname)s:%(lineno)d]',
    datefmt='%Y%m%d-%H:%M%p',
)

#  Email on errors
if not app.debug and not app.testing:
    import logging.handlers
    mail_handler = logging.handlers.SMTPHandler(
        'localhost',
        os.getenv('USER'),
        app.config['SYS_ADMINS'],
        '{0} error'.format(app.config['SITE_NAME']),
    )
    mail_handler.setFormatter(logging.Formatter('''
        Message type:       %(levelname)s
        Location:           %(pathname)s:%(lineno)d
        Module:             %(module)s
        Function:           %(funcName)s
        Time:               %(asctime)s

        Message:

        %(message)s
    '''.strip()))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
    app.logger.info("Emailing on error is ENABLED")
else:
    app.logger.info("Emailing on error is DISABLED")

# Bootstrap
from flask_bootstrap import Bootstrap
Bootstrap(app)

# Assets
from flask.ext.assets import Environment
assets = Environment(app)
# Ensure output directory exists
assets_output_dir = os.path.join(FLASK_APP_DIR, '..', 'static', 'gen')
if not os.path.exists(assets_output_dir):
    os.mkdir(assets_output_dir)

# Email
from flask.ext.mail import Mail
app.mail = Mail(app)

# Memcache
from flask.ext.cache import Cache
app.cache = Cache(app)

# MongoEngine
from flask_application.models import db
app.db = db
app.db.init_app(app)

from flask.ext.security import Security, MongoEngineUserDatastore, RegisterForm
from flask_application.users.models import User, Role
from flask.ext.wtf import RecaptchaField
from wtforms import TextField
from wtforms.validators import Required, ValidationError

# Dropbox
from flask.ext.dropbox import Dropbox, DropboxBlueprint
app.dropbox = Dropbox(app)
app.dropbox.register_blueprint(url_prefix='/dropbox')


class ExtendedRegisterForm(RegisterForm):
  recaptcha = RecaptchaField()

  def unique_check(form, field):
      field.data = field.data.replace(" ", "")
      if len(User.objects(username__iexact=field.data)) > 0:
          raise ValidationError('username is not unique')

  def route_check(form, field):
    for rule in app.url_map.iter_rules():
        str_rule = str(rule)
        str_rule = str_rule[1:len(str_rule)]
        if str_rule.startswith(field.data):
          raise ValidationError('invalid username')

  username = TextField('Name', [
      Required(),
      unique_check,
      route_check
      ])

# Setup Flask-Security
app.user_datastore = MongoEngineUserDatastore(app.db, User, Role)
app.security = Security(app, app.user_datastore,
        register_form=ExtendedRegisterForm)

from flask_sijax import Sijax
app.sijax = Sijax(app)

from flask_mobility import Mobility
Mobility(app)

# Business Logic
# http://flask.pocoo.org/docs/patterns/packages/
# http://flask.pocoo.org/docs/blueprints/
from flask_application.public.controllers import public
app.register_blueprint(public)

from flask_application.users.controllers import users
app.register_blueprint(users)

from flask_application.admin.controllers import admin
app.register_blueprint(admin)

from flask_application.profiles.controllers import profiles
app.register_blueprint(profiles)

from flask_application.guides.controllers import guides
app.register_blueprint(guides)


def scan_and_import(name):
    for root, _, files in os.walk(FLASK_APP_DIR):
        if ('%s.py' % name) in files:
            fp, pathname, description = imp.find_module(name, [root])
            try:
                imp.load_module(name, fp, pathname, description)
            finally:
                if fp:
                    fp.close()

# Filters need to be explicity imported in order to be registered.
scan_and_import('filters')

@app.route('/')
def index():
    return self.render('home/index.html')

@app.route('/site/upload-file', methods=["POST"])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file[]')
        for f in files:
            filename = (f.filename)
            file_size = 500
            print 'file', f
        return jsonify(name='gorb', size=500)
