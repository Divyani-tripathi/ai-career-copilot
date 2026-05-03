import pymysql
pymysql.install_as_MySQLdb()
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "mysql+mysqldb://4BXvMxYydEeTpuw.root:ZEC2zUfNh2NP3hNK@gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com:4000/test"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
    }
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

