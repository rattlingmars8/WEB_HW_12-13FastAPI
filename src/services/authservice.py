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


class Auth:
    """
    Клас Auth надає різні методи для генерації, перевірки та роботи з токенами
    аутентифікації, а також для отримання аутентифікованого користувача.

    Attributes:
        pwd_cxt (CryptContext): Об'єкт для хешування паролів за допомогою bcrypt.
        SECRET_KEY (str): Секретний ключ для підпису JWT.
        ALGR (str): Алгоритм підпису JWT.
        oauth2_scheme (OAuth2PasswordBearer): Об'єкт для отримання токену з HTTP-запиту.
    """
    pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGR = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

    def generate_password_hash(self, password: str):
        """
        Генерує хеш пароля за допомогою bcrypt.

        Args:
            password (str): Пароль у відкритому вигляді.

        Returns:
            str: Хеш пароля, створений за допомогою bcrypt.
        """
        return self.pwd_cxt.hash(password)

    def check_password_hash(self, hashed_password: str, password: str):
        """
        Перевіряє, чи відповідає наданий пароль збереженому хешу пароля.

        Args:
            hashed_password (str): Збережений хеш пароля, створений за допомогою bcrypt.
            password (str): Пароль у відкритому вигляді для перевірки.

        Returns:
            bool: True, якщо паролі відповідають один одному, False - у протилежному випадку.
        """
        return self.pwd_cxt.verify(password, hashed_password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Створює токен доступу.

        Args:
            data (dict): Дані для включення в пейлоад токена.
            expires_delta (float, optional): Термін дії токена у секундах. За замовчуванням - 15 хвилин.

        Returns:
            str: Токен доступу у вигляді рядка JWT.
        """
        to_encode = data.copy()

        if expires_delta:
            expires = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expires = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({"iat": datetime.utcnow(), "exp": expires, "scope": "access_token"})
        access_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Створює токен оновлення.

        Args:
            data (dict): Дані для включення в пейлоад токена.
            expires_delta (float, optional): Термін дії токена у секундах. За замовчуванням - 7 днів.

        Returns:
            str: Токен оновлення у вигляді рядка JWT.
        """
        to_encode = data.copy()

        if expires_delta:
            expires = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expires = datetime.utcnow() + timedelta(days=7)

        to_encode.update({"iat": datetime.utcnow(), "exp": expires, "scope": "access_token"})
        refresh_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return refresh_token

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        """
        Отримати поточного автентифікованого користувача за допомогою токена доступу.
        Args:
            token (str, optional): Токен доступу у форматі Bearer. За замовчуванням: Depends(oauth2_scheme).
            db (AsyncSession, optional): Асинхронний сеанс бази даних. За замовчуванням: Depends(get_db).

        Returns:
            User: Об'єкт автентифікованого користувача.

        Raises:
            HTTPException(401): Якщо токен недійсний або користувач не автентифікований.
        """

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
        """
        Створити токен підтвердження електронної пошти.

        Args:
            data (dict): Дані, які будуть включені в тіло токену.

        Returns:
            str: Токен підтвердження електронної пошти у форматі JWT (JSON Web Token) у вигляді рядка.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "email_token"})
        token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Розкодувати токен оновлення і видобути електронну пошту.

        Args:
            refresh_token (str): Токен оновлення у форматі JWT (JSON Web Token) у вигляді рядка.

        Returns:
            str: Електронна пошта, видобута з токену оновлення.

        Raises:
            HTTPException(401): Якщо токен недійсний або має неправильний обсяг.
        """
        try:
            payload = jwt.decode(refresh_token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "refresh_token":
                email = payload.get("sub")
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    def get_email_from_token(self, token: str):
        """
        Отримати електронну пошту з токеном підтвердження електронної пошти.

        Args:
            token (str): Токен підтвердження електронної пошти у форматі JWT (JSON Web Token) у вигляді рядка.

        Returns:
            str: Електронна пошта, видобута з токену.

        Raises:
            HTTPException(422): Якщо токен недійсний для підтвердження електронної пошти.
        """
        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "email_token":
                email = payload.get("sub")
                return email
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email confirmation.")

    def create_reset_token(self, data: dict, expire=1):
        """
        Створити токен для скидання пароля.

        Args:
            data (dict): Дані, які будуть включені в тіло токена.
            expire (int, optional): Час дії токена в годинах. За замовчуванням: 1 година.

        Returns:
            str: Токен для скидання пароля у форматі JWT (JSON Web Token) у вигляді рядка.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=expire)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh"})
        reset_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return reset_token

    def get_email_from_reset_token(self, token: str):
        """
        Отримати електронну пошту з токену для скидання пароля.

        Args:
            token (str): Токен для скидання пароля у форматі JWT (JSON Web Token) у вигляді рядка.

        Returns:
            str: Електронна пошта, видобута з токену.

        Raises:
            HTTPException(422): Якщо токен недійсний для скидання пароля.
        """
        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "refresh":
                email = payload.get("sub")
                return email
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for password reset.")


authservice = Auth()
