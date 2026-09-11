import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"
PREVENT_UNSAFE_DB_CONNECTIONS = False
WTF_CSRF_ENABLED = True
TALISMAN_ENABLED = False
