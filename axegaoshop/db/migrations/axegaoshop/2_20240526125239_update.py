from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "faqs" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "title" VARCHAR(100) NOT NULL
);
COMMENT ON TABLE "faqs" IS 'пользовательское соглашение';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "faqs";"""
