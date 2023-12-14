from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.environ.get(
    "DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

postgres_migrations_repo = os.path.join(BASE_DIR,'migrations','postgresql')


# POSTGRES_DATABASE = 'postgresql://shamsk:Materials2016!@localhost/tobot'

POSTGRES_DATABASE = f'postgresql://{os.getenv("DB_Username")}:{os.getenv("DB_Password")}@{os.getenv("DB_Host")}/{os.getenv("DB_name")}'


app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_DATABASE

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Define metadata, instantiate db
metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)

migrate = Migrate(app, db, directory=postgres_migrations_repo)

db.init_app(app)