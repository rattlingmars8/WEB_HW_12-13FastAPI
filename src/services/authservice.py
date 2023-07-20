from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.db import get_db
from src.repository import users_repo as user_repository
from src.conf.config import settings


# config.read(config_ini)


class Auth:
    pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGR = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

    def generate_password_hash(self, password: str):
        return self.pwd_cxt.hash(password)

    def check_password_hash(self, hashed_password: str, password: str):
        return self.pwd_cxt.verify(password, hashed_password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()

        if expires_delta:
            expires = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expires = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({"iat": datetime.utcnow(), "exp": expires, "scope": "access_token"})
        access_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()

        if expires_delta:
            expires = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expires = datetime.utcnow() + timedelta(days=7)

        to_encode.update({"iat": datetime.utcnow(), "exp": expires, "scope": "access_token"})
        refresh_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return refresh_token

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") != "access_token":
                raise credentials_exception
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await user_repository.repo_user_authentication_by_email(email, db)
        if user is None:
            raise credentials_exception

        return user

    def create_email_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "email_token"})
        token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return token

    async def decode_refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "refresh_token":
                email = payload.get("sub")
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    def get_email_from_token(self, token: str):
        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "email_token":
                email = payload.get("sub")
                return email
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email confirmation.")

    def create_reset_token(self, data: dict, expire=1):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=expire)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh"})
        reset_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return reset_token

    def get_email_from_reset_token(self, token: str):
        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "refresh":
                email = payload.get("sub")
                return email
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for password reset.")


authservice = Auth()
