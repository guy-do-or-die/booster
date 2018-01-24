import logging

from datetime import datetime

from mongoengine import connect, DynamicDocument
from mongoengine.fields import (StringField, EmailField, IntField, FloatField,
                                DateTimeField, ListField, ReferenceField)
import config

logger = logging.getLogger('users')

db = connect(config.DB.pop('name'), alias='default', connect=False, **config.DB)


class Guy(DynamicDocument):
    meta = {'collection': 'guys'}

    ref_id = StringField()
    ref_name = StringField()

    name = StringField()
    email = EmailField()
    pages_today = IntField(default=0)
    pages_total = IntField(default=0)
    shares_today = IntField(default=0)
    updated = DateTimeField(default=datetime.now())
    earnings = FloatField()
    level = IntField()

    ref = ReferenceField('Guy')
    refs = ListField(ReferenceField('Guy'))

    def next_ref_name(self, n):
        return '{}_{}'.format(self.ref_name, n)

    def next_email(self, n):
        name, domain = self.email.split('@')
        return '@'.join(['{}+{}'.format(name, n), domain])

    def __repr__(self):
        return 'Guy({})'.format(str(self.to_json()))
