import typing
from datetime import datetime

from tortoise import fields
from tortoise.models import Model

from axegaoshop.db.models.user import User


class Token(Model):
    user_id = fields.IntField()
    created_datetime = fields.DatetimeField(default=datetime.now)
    access_token = fields.CharField(max_length=500, pk=True)
    refresh_token = fields.CharField(max_length=500, null=False)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "tokens"

    async def get_user(self) -> typing.Optional[User]:
        return await User.get_or_none(id=self.user_id)

    async def save(self, *args, **kwargs):
        # tokens = await Token.filter(user_id=self.user_id).all()
        #
        # for token in tokens:
        #     token.is_active = False
        #
        # await Token.bulk_update(tokens, fields=['is_active'])

        await super().save(*args, **kwargs)
