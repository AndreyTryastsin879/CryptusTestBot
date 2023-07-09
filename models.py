from app import db
from datetime import datetime
from flask_security import UserMixin, RoleMixin
from sqlalchemy import BigInteger


message_tariffs = db.Table(
    'message_tariffs',
    db.Column('message_id', db.Integer, db.ForeignKey('message.id')),
    db.Column('tariff_id', db.Integer, db.ForeignKey('tariff.id'))
)


message_periods = db.Table(
    'message_periods',
    db.Column('message_id', db.Integer, db.ForeignKey('message.id')),
    db.Column('period_id', db.Integer, db.ForeignKey('period.id'))
)


message_blockchains = db.Table(
    'message_blockchains',
    db.Column('message_id', db.Integer, db.ForeignKey('message.id')),
    db.Column('blockchain_id', db.Integer, db.ForeignKey('blockchain.id'))
)


message_channels = db.Table(
    'message_channels',
    db.Column('message_id', db.Integer, db.ForeignKey('message.id')),
    db.Column('channel_id', db.Integer, db.ForeignKey('channel.id'))
)


class Message(db.Model):
    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), unique=True)
    slug = db.Column(db.String(300), unique=True)
    text = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.now())

    tariffs = db.relationship('Tariff', secondary=message_tariffs, backref=db.backref('messages', lazy='dynamic'))
    periods = db.relationship('Period', secondary=message_periods, backref=db.backref('messages', lazy='dynamic'))
    blockchains = db.relationship('Blockchain', secondary=message_blockchains, backref=db.backref('messages',
                                                                                                  lazy='dynamic'))
    channels = db.relationship('Channel', secondary=message_channels, backref=db.backref('messages', lazy='dynamic'))

    def __repr__(self):
        return '<Message: {}>'.format(self.id, self.name)


class Tariff(db.Model):
    def __init__(self, *args, **kwargs):
        super(Tariff, self).__init__(*args, **kwargs)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), unique=True)
    channel_id = db.Column(BigInteger)
    price = db.Column(db.Integer())
    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return 'Tariff: {}'.format(self.name)


class Period(db.Model):
    def __init__(self, *args, **kwargs):
        super(Period, self).__init__(*args, **kwargs)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), unique=True)
    period_in_months = db.Column(db.Integer())
    percentage_of_tariff_price = db.Column(db.Integer())
    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return 'Period: {}'.format(self.name)


class Blockchain(db.Model):
    def __init__(self, *args, **kwargs):
        super(Blockchain, self).__init__(*args, **kwargs)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), unique=True)
    address_for_payments = db.Column(db.String(300), unique=True)
    tx_hash_api_endpoint = db.Column(db.String(300), unique=True)
    api_key = db.Column(db.String(300), unique=True)
    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return 'Blockchain for payments: {}'.format(self.name)


class Channel(db.Model):
    def __init__(self, *args, **kwargs):
        super(Channel, self).__init__(*args, **kwargs)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True)
    created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return 'Our Channels: {}'.format(self.name)


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    active = db.Column(db.Boolean())
#    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(250))