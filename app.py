from flask import Flask

from app_config import Configuration
from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView

from flask_security import SQLAlchemyUserDatastore, Security, current_user

from flask import redirect, url_for, request

app = Flask(__name__)
app.config.from_object(Configuration)

db = SQLAlchemy(app)

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


from models import *


class AdminMixin:
    def is_accessible(self):
        return current_user.has_role('admin')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('security.login', next=request.url))


class AdminView(AdminMixin, ModelView):
    pass


class HomeAdminView(AdminMixin, AdminIndexView):
    pass


admin = Admin(app, 'FlaskApp', url='/', index_view=HomeAdminView(name='Home'))

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class MessageView(ModelView):
    column_labels = {
        'tariffs': 'Tariffs',
        'periods': 'Periods',
        'blockchains': 'Blockchains',
        'channels': 'Channels'
    }
    form_ajax_refs = {
        'tariffs': {
            'fields': ['name']
        },
        'periods': {
            'fields': ['name']
        },
        'blockchains': {
            'fields': ['name']
        },
        'channels': {
            'fields': ['name']
        }
    }


admin.add_view(MessageView(Message, db.session))
admin.add_view(ModelView(Tariff, db.session))
admin.add_view(ModelView(Period, db.session))
admin.add_view(ModelView(Blockchain, db.session))
admin.add_view(ModelView(Channel, db.session))

