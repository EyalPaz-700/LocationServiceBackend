from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from consts import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, OAUTH2_SCHEME, User
from utils import _get_user
from Crypto.Cipher import AES
from typing import Union
from secrets import token_bytes
import base64
from Crypto.Hash import BLAKE2s
import os


SECRET_EN_KEY = base64.b64decode(os.environ.get("SECRET_EN_KEY").encode())
SECRET_PASSWORD_KEY = os.environ.get("SECRET_PASSWORD_KEY")


def verify_password(input_password: str, db_password: str) -> bool:
    return input_password == db_password


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_PASSWORD_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def _encrypt_data(data: Union[str, int]) -> bytes:
    nonce = token_bytes(16)
    cipher = AES.new(SECRET_EN_KEY, AES.MODE_GCM, nonce)
    cipher_text = cipher.encrypt(data.encode())
    blake2 = BLAKE2s.new(digest_bits=128, key=SECRET_EN_KEY)
    blake2.update(cipher_text)
    tag = blake2.digest()
    return base64.b64encode(cipher_text + tag + nonce)


def _decrypt_data(data: bytes) -> str:
    data = base64.b64decode(data)
    ciphertext, tag, nonce = data[: -32], data[-32: - 16], data[-16:]
    cipher = AES.new(SECRET_EN_KEY, AES.MODE_GCM, nonce)
    decrypted_data = cipher.decrypt(ciphertext).decode()
    blake2 = BLAKE2s.new(digest_bits=128, key=SECRET_EN_KEY)
    blake2.update(ciphertext)
    calculated_tag = blake2.digest()
    if tag != calculated_tag:
        raise ValueError("Authentication tag verification failed. Data may be tampered with.")
    return decrypted_data


async def get_current_user(token: str = Depends(OAUTH2_SCHEME)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_PASSWORD_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user = _get_user(username)
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if user is None:
        raise credentials_exception
    return user


async def authenticate_user(username: str, password: str) -> Union[User, None]:
    user = _get_user(username)
    if not user or not verify_password(password, user.password):
        return None
    return user


async def create_access_token_route(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
