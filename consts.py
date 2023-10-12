from pydantic import BaseModel
from sqlalchemy import (Column, Integer, Text)
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()


class Location(BaseModel):
    latitude: float
    longitude: float


class UserLocation(Base):
    __tablename__ = "locations"
    user_id = Column(Integer, primary_key=True, index=True)
    geom = Column(Geometry('POINT'))


class UserSchema(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(Text)
    password = Column(Text)


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    user_id: int
    password: str


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="token")
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
