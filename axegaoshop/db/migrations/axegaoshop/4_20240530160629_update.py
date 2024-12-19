from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DELETE FROM faqs;
        ALTER TABLE "faqs" ADD "order_id" INT NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "faqs" DROP COLUMN "order_id";"""
