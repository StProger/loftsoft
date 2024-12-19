from tortoise import fields
from tortoise.models import Model


class Partner(Model):
    """таблица с партнерами (фоторгафии полноразмерные, сжимаются для
    админки на фронте)"""

    id = fields.IntField(pk=True)

    created_datetime = fields.DatetimeField(auto_now_add=True)

    photo = fields.CharField(max_length=100)

    class Meta:
        table = "partners"

    class PydanticMeta:
        exclude = ("created_datetime",)
