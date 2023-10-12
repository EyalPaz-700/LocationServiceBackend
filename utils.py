from consts import UserLocation, UserSchema, User
from db_handler import DBHandler
from shapely import wkb
from functools import wraps


def _get_user(username: str) -> User:
    db = DBHandler()
    res = db.get_db_session().query(UserSchema).filter(UserSchema.username == username).first()
    return User(username=res.username, user_id=res.id, password=res.password)


def _get_location(user_id: int) -> str:
    db = DBHandler().get_db_session()
    db_location = db.query(UserLocation).filter(UserLocation.user_id == user_id).first()
    return str(wkb.loads(db_location.geom.desc))


def check_user_id():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get("user_id")
            current_user_id = kwargs.get("current_user").user_id
            if user_id == current_user_id:
                return await func(*args, **kwargs)
            else:
                return {"message": "Auth Error"}

        return wrapper

    return decorator
