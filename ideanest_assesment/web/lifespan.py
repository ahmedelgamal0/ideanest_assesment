from contextlib import asynccontextmanager
from typing import AsyncGenerator

import beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from ideanest_assesment.db.models import load_all_models
from ideanest_assesment.services.rabbit.lifespan import init_rabbit, shutdown_rabbit
from ideanest_assesment.services.redis.lifespan import init_redis, shutdown_redis
from ideanest_assesment.settings import settings


async def _setup_db(app: FastAPI) -> None:
    client = AsyncIOMotorClient(str(settings.db_url))  # type: ignore
    app.state.db_client = client
    await beanie.init_beanie(
        database=client[settings.db_base],
        document_models=load_all_models(),  # type: ignore
    )


@asynccontextmanager
async def lifespan_setup(
    app: FastAPI,
) -> AsyncGenerator[None, None]:  # pragma: no cover
    """
    Actions to run on application startup.

    This function uses fastAPI app to store data
    in the state, such as db_engine.

    :param app: the fastAPI application.
    :return: function that actually performs actions.
    """

    app.middleware_stack = None
    await _setup_db(app)
    init_redis(app)
    init_rabbit(app)
    app.middleware_stack = app.build_middleware_stack()

    yield
    await shutdown_redis(app)
    await shutdown_rabbit(app)
