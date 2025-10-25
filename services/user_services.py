from typing import Optional
import hashlib
import secrets
from app.db.database import database
from app.db.models import User, UserCreate


class UserService:
    def _hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        salt = secrets.token_hex(16)
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex() + ':' + salt

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            stored_hash, salt = hashed_password.split(':')
            computed_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            ).hex()
            return secrets.compare_digest(computed_hash, stored_hash)
        except:
            return False

    async def create_user(self, user_data: UserCreate) -> Optional[User]:
        """Создать пользователя"""
        # Проверяем существование
        existing = await database.fetch_one(
            'SELECT id FROM users WHERE email = ?',
            (user_data.email,)
        )

        if existing:
            return None

        hashed_password = self._hash_password(user_data.password)

        result = await database.execute(
            'INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)',
            (user_data.email, user_data.name, hashed_password)
        )

        row = await database.fetch_one(
            'SELECT id, email, name, created_at FROM users WHERE id = ?',
            (result.lastrowid,)
        )

        return User(id=row[0], email=row[1], name=row[2], created_at=row[3])

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        row = await database.fetch_one(
            'SELECT id, email, name, password_hash, created_at FROM users WHERE email = ?',
            (email,)
        )

        if not row:
            return None

        if not self._verify_password(password, row[3]):
            return None

        return User(id=row[0], email=row[1], name=row[2], created_at=row[4])

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        row = await database.fetch_one(
            'SELECT id, email, name, created_at FROM users WHERE id = ?',
            (user_id,)
        )

        if not row:
            return None

        return User(id=row[0], email=row[1], name=row[2], created_at=row[3])

    async def update_user(self, user_id: int, name: str, email: str) -> Optional[User]:
        """Обновить пользователя"""
        result = await database.execute(
            'UPDATE users SET name = ?, email = ? WHERE id = ?',
            (name, email, user_id)
        )

        if result.rowcount == 0:
            return None

        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя"""
        result = await database.execute(
            'DELETE FROM users WHERE id = ?',
            (user_id,)
        )

        return result.rowcount > 0

    async def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        rows = await database.fetch_all(
            'SELECT id, email, name, created_at FROM users ORDER BY created_at DESC'
        )

        return [
            User(id=row[0], email=row[1], name=row[2], created_at=row[3])
            for row in rows
        ]


user_service = UserService()