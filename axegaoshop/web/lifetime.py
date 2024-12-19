from typing import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from axegaoshop.services.crons.clear_database import clear_amount_of_purchasing

async_scheduler = AsyncIOScheduler()


def register_startup_event(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:
    """
    События, вызывающиеся при начале работы нашего приложения

     - Удаление "старых" запросов на пополнение/покупку товара
    """

    @app.on_event("startup")
    async def _startup() -> None:
        logger.info("Creating orders and replenishes clearing job...")
        async_scheduler.add_job(
            clear_amount_of_purchasing, "interval", seconds=4, misfire_grace_time=10
        )

        async_scheduler.start()
        logger.success("Clearing jobs created successfully!")

    return _startup
