import enum
import os.path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

executor = ThreadPoolExecutor(max_workers=6)


class LogLevel(enum.StrEnum):
    """Возможные уровни логгирования."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class PaymentType(enum.StrEnum):
    """доступные типы оплаты"""

    SBP: str = "sbp"
    SITE_BALANCE: str = "site_balance"


# разрешенные типы данных для загрузки в /api/upload
ALLOWED_UPLOAD_TYPES = ["image/jpeg", "image/png", "text/plain", "image/svg+xml"]


class ProductExt:
    """типы расширений для файлов-товаров для проверки при выдаче"""

    TXT = ".txt"


class Settings(BaseSettings):
    """
    Настройки приложения

    Изменяются и задаются в .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AXEGAOSHOP_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # конфигурация uvicorn
    scheme: str = "http"
    host: str = "127.0.0.1"
    port: int = 8000

    # host name of front server
    front_hostname: str = ""
    back_hostname: str = ""
    # количество воркеров uvicorn
    workers_count: int = 1

    # Обновление uvicorn
    reload: bool = False

    # Текущее окружение
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO

    # типы оплаты (платежки)
    payment_types: list[str] = [PaymentType.SBP, PaymentType.SITE_BALANCE]

    # Данные от базы данных
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = ""
    db_password: str = ""
    db_base: str = "axegaoshop"
    db_echo: bool = 0

    # конфигурация Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    # дб редиса для кеша
    redis_cache_db: int = 2

    redis_amounts_key: str = "payment:amounts"

    mail_host: str = ""
    mail_port: int = 465
    mail_user: str = ""
    mail_password: str = ""

    # конфигурация Sentry SDK
    sentry_dsn: Optional[str] = None
    sentry_sample_rate: float = 1.0

    storage_folder: str = "axegaoshop/data/storage"

    # картинки сайта
    storage_folder_uploads: str = storage_folder + "/uploads"

    jwt_secret_key: str = "jwt_key"
    jwt_refresh_secret_key: str = "jwt_refresh_key"

    logs_dir: str = "axegaoshop/data/logs"

    @property
    def base_hostname(self) -> URL:
        """создание хостнейма на сайт"""
        return URL.build(scheme=self.scheme, host=self.host, port=self.port)

    @property
    def db_url(self) -> URL:
        """
        Создание ссылки для подключения к базе данных

        :return: database URL.
        """
        return URL.build(
            scheme="asyncpg",
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_password,
            path=f"/{self.db_base}",
        )

    def __build__(self) -> None:
        """создание папок для хранилища"""
        os.makedirs(self.storage_folder, exist_ok=True)
        os.makedirs(self.storage_folder_uploads, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)


settings = Settings()
settings.__build__()
