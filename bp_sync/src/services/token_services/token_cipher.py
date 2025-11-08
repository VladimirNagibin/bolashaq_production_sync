import asyncio
from functools import lru_cache

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken

from core.logger import logger
from core.settings import settings

from ..exceptions import (
    InvalidEncryptionKeyError,
    TokenCipherError,
    TokenDecryptionError,
    TokenEncryptionError,
)


class TokenCipher:
    """Сервис для симметричного шифрования токенов с использованием Fernet."""

    def __init__(self, encryption_key: str):
        """
        Инициализация шифровальщика.

        Args:
            encryption_key: Ключ шифрования в виде строки

        Raises:
            InvalidEncryptionKeyError: Если ключ некорректен
        """

        if not encryption_key:
            raise InvalidEncryptionKeyError("Encryption key cannot be empty")

        try:
            key_bytes = encryption_key.encode("utf-8")
            self.cipher = Fernet(key_bytes)

            # Проверяем что ключ валидный путем шифрования/дешифрования
            # тестовых данных
            test_data = "test"
            encrypted = self.cipher.encrypt(test_data.encode())
            decrypted = self.cipher.decrypt(encrypted).decode()

            if decrypted != test_data:
                raise InvalidEncryptionKeyError(
                    "Encryption key verification failed"
                )

        except (ValueError, TypeError, InvalidKey) as e:
            logger.critical(
                "Invalid encryption key provided",
                extra={"key_length": len(encryption_key)},
            )
            raise InvalidEncryptionKeyError(
                f"Invalid encryption key: {e}"
            ) from e
        except Exception as e:
            logger.critical(
                "Unexpected error during cipher initialization",
                extra={"error": str(e)},
            )
            raise TokenCipherError(f"Cipher initialization failed: {e}") from e

    async def encrypt(self, data: str) -> bytes:
        """
        Асинхронное шифрование строки в байты.

        Args:
            data: Строка для шифрования

        Returns:
            Зашифрованные данные в виде bytes

        Raises:
            TokenEncryptionError: Если шифрование не удалось
        """
        if not data:
            raise ValueError("Data to encrypt cannot be empty")

        try:
            encrypted_data = await asyncio.to_thread(self._encrypt_sync, data)
            return encrypted_data
        except Exception as e:
            logger.error(
                "Token encryption failed",
                extra={"data_length": len(data), "error": str(e)},
            )
            raise TokenEncryptionError(f"Token encryption error: {e}") from e

    async def decrypt(self, encrypted_data: bytes) -> str:
        """
        Асинхронное дешифрование байтов в строку.

        Args:
            encrypted_data: Зашифрованные данные

        Returns:
            Расшифрованная строка

        Raises:
            TokenDecryptionError: Если дешифрование не удалось
            InvalidToken: Если токен поврежден или невалиден
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")

        try:
            decrypted_str = await asyncio.to_thread(
                self._decrypt_sync, encrypted_data
            )
            return decrypted_str
        except InvalidToken as e:
            logger.warning(
                "Invalid token during decryption",
                extra={"data_length": len(encrypted_data)},
            )
            raise TokenDecryptionError("Invalid or corrupted token") from e
        except Exception as e:
            logger.error(
                "Token decryption failed",
                extra={"data_length": len(encrypted_data), "error": str(e)},
            )
            raise TokenDecryptionError(f"Token decryption error: {e}") from e

    def _encrypt_sync(self, data: str) -> bytes:
        """Синхронное шифрование строки."""
        return self.cipher.encrypt(  # type: ignore[no-any-return]
            data.encode()
        )

    def _decrypt_sync(self, encrypted_data: bytes) -> str:
        """Синхронное дешифрование в строку."""
        return self.cipher.decrypt(  # type: ignore[no-any-return]
            encrypted_data
        ).decode()

    def encrypt_sync(self, data: str) -> bytes:
        """
        Синхронная версия шифрования для использования в синхронном контексте.

        Args:
            data: Строка для шифрования

        Returns:
            Зашифрованные данные
        """
        return self._encrypt_sync(data)

    def decrypt_sync(self, encrypted_data: bytes) -> str:
        """
        Синхронная версия дешифрования для использования в синхронном
        контексте.

        Args:
            encrypted_data: Зашифрованные данные

        Returns:
            Расшифрованная строка
        """
        return self._decrypt_sync(encrypted_data)


@lru_cache(maxsize=1)
def get_token_cipher() -> TokenCipher:
    """
    Фабрика для внедрения зависимостей TokenCipher.

    Returns:
        Экземпляр TokenCipher

    Raises:
        InvalidEncryptionKeyError: Если ключ шифрования некорректен
    """
    if not settings.ENCRYPTION_KEY:
        logger.critical("Encryption key is not configured")
        raise InvalidEncryptionKeyError("ENCRYPTION_KEY is not set")

    return TokenCipher(settings.ENCRYPTION_KEY)
