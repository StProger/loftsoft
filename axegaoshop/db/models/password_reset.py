from tortoise import fields
from tortoise.models import Model


class PasswordReset(Model):
    """таблица сбросов пароля (можно использовать ссылку единожды)"""

    id = fields.UUIDField(pk=True)

    email = fields.TextField(null=False)
    hashed_password = fields.TextField(null=False)

    is_active = fields.BooleanField(null=False, default=True)

    class Meta:
        table = "password_resets"
