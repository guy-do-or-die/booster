from mongoengine import connect, DynamicDocument
from mongoengine.fields import StringField, EmailField, IntField, FloatField

import config
import logging

logger = logging.getLogger('users')

db = connect(config.DB.pop('name'), **config.DB)


class Guy(DynamicDocument):
    meta = {'collection': 'guys'}

    ref_id = IntField()
    name = StringField()
    email = EmailField()
    pages_today = IntField()
    pages_total = IntField()
    shares_today = IntField()
    earnings = FloatField()
    level = IntField()

    def __repr__(self):
        return 'Guy({})'.format(str(self.to_json()))
