from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import os
class DBHandler():
    def __init__(self):
        self._engine =  create_engine(os.environ.get("DATABASE_URL"))
        self._db_session = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    def __delete__(self) -> None:
        self._db_session.close()

    def get_db_session(self) -> Session:
        return self._db_session()
