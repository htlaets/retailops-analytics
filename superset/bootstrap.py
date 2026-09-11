"""Executed inside `superset shell` to register the analytics warehouse."""

from superset import db
from superset.models.core import Database

name = "RetailOps Warehouse"
uri = "sqlite:////app/data/retailops.db"
database = db.session.query(Database).filter_by(database_name=name).one_or_none()
if database is None:
    database = Database(database_name=name, sqlalchemy_uri=uri, expose_in_sqllab=True)
    db.session.add(database)
else:
    database.sqlalchemy_uri = uri
    database.expose_in_sqllab = True
db.session.commit()
print(f"Configured {name}")
