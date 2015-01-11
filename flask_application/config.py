import logging
import os
from pymongo.uri_parser import parse_uri


class Config(object):
    def __init__(self):
        self.DEBUG = False
        self.TESTING = False
        self.HEROKU = False
        self.PRODUCTION = False

        # TODO you'll have to generate one of these
        self.SECRET_KEY = 'SUPER SECRET KEY'
        self.SITE_NAME = 'refurence.net'
        self.LOG_LEVEL = logging.DEBUG

        self.SYS_ADMINS = ['refurence@gmail.com']

        # Mongodb support
        self.MONGODB_SETTINGS = self.mongo_from_uri('mongodb://localhost:27017/development')

        # Configured for Gmail
        self.DEFAULT_MAIL_SENDER = 'Admin < refurence@gmail.com >'
        self.MAIL_SERVER = 'smtp.gmail.com'
        self.MAIL_PORT = 465
        self.MAIL_USE_SSL = True
        self.MAIL_USERNAME = 'refurence@gmail.com'
        self.MAIL_PASSWORD = os.getenv('GMAIL_PASSWD')

        # Flask-Security setup
        self.SECURITY_EMAIL_SENDER = 'Refurence-PasswordReset < refurence@gmail.com >'
        self.SECURITY_EMAIL_SUBJECT_PASSWORD_RESET = "Refurence Password Reset Instructions"
        self.SECURITY_LOGIN_WITHOUT_CONFIRMATION = False
        self.SECURITY_REGISTERABLE = True
        self.SECURITY_RECOVERABLE = True
        self.SECURITY_URL_PREFIX = '/auth'
        self.SECUIRTY_POST_LOGIN = '/'
        self.SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'

        # import uuid; salt = uuid.uuid4().hex
        # TODO you'll have to generate the salt as well
        self.SECURITY_PASSWORD_SALT = 'YOU NEED TO GENERATE SALT'

        self.SECURITY_SEND_REGISTER_EMAIL = False

        self.SECURITY_CONFIRMABLE = False
        self.SECURITY_LOGIN_WITHOUT_CONFIRMATION = False
        self.SECURITY_POST_REGISTER_VIEW = '/home/thankyou'

        # CACHE
        self.CACHE_TYPE = 'simple'

        # Recaptcha
        self.CSRF_ENABLED = True
        self.CSRF_SESSION_KEY = "iamahugefaggotiamahugefuckingfaggotalsoiamcum"
        self.RECAPTCHA_USE_SSL = False
        self.RECAPTCHA_PUBLIC_KEY = '6LdGs_4SAAAAAFer8LaWp3Tix8v37jLxdJRwkmgy'
        self.RECAPTCHA_PRIVATE_KEY = '6LdGs_4SAAAAAK74jFSmynOAQ0pTex3qTXRHLthZ'
        self.RECAPTCHA_OPTIONS = {'theme': 'black'}

    @staticmethod
    def mongo_from_uri(uri):
        config = parse_uri(uri)
        conn_settings = {
            'db': config['database'],
            'username': config['username'],
            'password': config['password'],
            'host': config['nodelist'][0][0],
            'port': config['nodelist'][0][1]
        }
        return conn_settings


class ProductionConfig(Config):
    def __init__(self):
        super(ProductionConfig, self).__init__()
        self.ENVIRONMENT = 'Production'
        self.HEROKU = True
        self.PRODUCTION = True
        self.LOG_LEVEL = logging.INFO

        self.MONGODB_SETTINGS = self.mongo_from_uri(os.getenv('MONGOHQ_URL'))


class DevelopmentConfig(Config):
    '''
    Use "if app.debug" anywhere in your code,
    that code will run in development mode.
    '''
    def __init__(self):
        super(DevelopmentConfig, self).__init__()
        self.ENVIRONMENT = 'Dev'
        self.DEBUG = True
        self.TESTING = False


class TestingConfig(Config):
    '''
    A Config to use when we are running tests.
    '''
    def __init__(self):
        super(TestingConfig, self).__init__()
        self.ENVIRONMENT = 'Testing'
        self.DEBUG = False
        self.TESTING = True

        self.MONGODB_SETTINGS = self.mongo_from_uri(
            'mongodb://localhost:27017/testing'
        )


environment = os.getenv('ENVIRONMENT', 'DEVELELOPMENT').lower()
# Alternatively this may be easier if you are managing multiple aws servers:
# environment = socket.gethostname().lower()

if environment == 'testing':
    app_config = TestingConfig()
elif environment == 'production':
    app_config = ProductionConfig()
else:
    app_config = DevelopmentConfig()
