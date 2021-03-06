from flask import Flask, url_for

from flask_sqlalchemy import SQLAlchemy

from flask_uploads import configure_uploads, patch_request_class, UploadSet

from sqlalchemy import event
from sqlalchemy.engine import Engine

from bpaint.config import Config

@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()

app = Flask(__name__)
app.config.from_object(Config)

uploads = UploadSet(name='images', extensions=app.config['ALLOWED_FILES'], default_dest=lambda _: '/static/images')
configure_uploads(app, uploads)
patch_request_class(app, 10 * 1024 * 1024)

db = SQLAlchemy(app=app, session_options={'expire_on_commit':False})
from bpaint.models import Color, Inventory, Recipe
db.create_all()
db.session.commit()

from bpaint.base import bp as base_bp
from bpaint.admin.routes import bp as admin_bp, load_db
from bpaint.details.routes import bp as details_bp
from bpaint.inv.routes import bp as inv_bp
from bpaint.search.routes import bp as search_bp
from bpaint.search.pic.routes import bp as pic_search_bp
from bpaint.search.text.routes import bp as text_search_bp
from bpaint.splash.routes import bp as splash_bp

app.register_blueprint(base_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(details_bp)
app.register_blueprint(inv_bp)
app.register_blueprint(search_bp)
app.register_blueprint(pic_search_bp)
app.register_blueprint(text_search_bp)
app.register_blueprint(splash_bp)
