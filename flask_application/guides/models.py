from flask_application.models import db, FlaskDocument


class Step(FlaskDocument):
    body = db.StringField()
    img = db.URLField()


class Guide(FlaskDocument):
    title = db.StringField(required=True, max_length=512)
    slug = db.StringField(required=True, max_length=64)
    abstract = db.StringField()
    steps = db.ListField(db.EmbeddedDocumentField('Step'))
