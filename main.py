from fastapi import FastAPI, Depends, HTTPException
from auth import create_access_token_route, get_current_user
from sqlalchemy.ext.declarative import declarative_base
from consts import Location, UserLocation, User, Token
from db_handler import DBHandler
from utils import _get_location, check_user_id
from auth import _encrypt_data
from sqlalchemy.sql import func
from shapely import wkb

Base = declarative_base()

app = FastAPI()


@app.post("/update_location/{user_id}", response_model=dict)
@check_user_id()
async def update_location(
        user_id: int,
        location: Location,
        current_user: User = Depends(get_current_user)
):
    db = DBHandler().get_db_session()
    try:
        db_location = db.query(UserLocation).filter(UserLocation.user_id == user_id).first()
        if db_location:
            db_location.geom = f"POINT({location.latitude} {location.longitude})"
        else:
            db_location = (user_id, f"POINT({location.latitude} {location.longitude})")
        db.add(db_location)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update location")
    finally:
        db.close()

    return {"message": "Location updated successfully"}


@app.get("/get_location/{user_id}", response_model=dict)
@check_user_id()
async def get_location(
        user_id: int,
        current_user: dict = Depends(get_current_user)
) -> dict:
    try:
        db_location = _get_location(user_id)
        if not db_location:
            raise HTTPException(status_code=404, detail="No Current Location")
        return {"user_id": _encrypt_data(user_id), "location": _encrypt_data(str(db_location))}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve location")


@app.get("/get_closest_people_location/{user_id}", response_model=dict)
@check_user_id()
async def get_location(
        user_id: int,
        current_user: dict = Depends(get_current_user)
) -> dict:
    db = DBHandler().get_db_session()
    try:
        query = db.query(UserLocation)
        query = query.order_by(func.ST_Distance(UserLocation.geom, f'SRID=3857;{_get_location(user_id)}'))
        query = query.limit(5)
        result = query.all()
        return {"result": [[_encrypt_data(x.user_id), _encrypt_data(str(wkb.loads(x.geom.desc)))] for x in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve location")
    finally:
        db.close()


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: create_access_token_route = Depends()) -> dict:
    return {"access_token": (_encrypt_data(form_data["access_token"])), "token_type": "bearer"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
