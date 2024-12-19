import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from loguru import logger
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from starlette.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

import axegaoshop.db.config
from axegaoshop.db.config import TORTOISE_CONFIG
from axegaoshop.logging import configure_logging
from axegaoshop.settings import settings
from axegaoshop.web.lifetime import register_startup_event


def get_app() -> FastAPI:
    """
    конфигурирование приложения
    """
    configure_logging()

    if settings.sentry_dsn:
        logger.info("Initializing Sentry connection...")
        # Интеграция с sentry
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=settings.sentry_sample_rate,
            environment=settings.environment,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.getLevelName(
                        settings.log_level.value,
                    ),
                    event_level=logging.ERROR,
                ),
            ],
        )

        logger.success("Sentry connected successfully!")

    app = FastAPI(
        title="Axegao Shop",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=UJSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # регистрация события startup
    register_startup_event(app)

    # Конфигурирование Tortoise ORM
    Tortoise.init_models(axegaoshop.db.config.MODELS_MODULES, "axegaoshop")

    register_tortoise(
        app,
        config=TORTOISE_CONFIG,
        add_exception_handlers=True,
    )

    from axegaoshop.web.api.router import api_router

    # Загрузка всех роутеров из головного
    app.include_router(router=api_router, prefix="")

    return app
