from datetime import datetime

from tortoise import fields
from tortoise.exceptions import NoValuesFetched
from tortoise.expressions import Q
from tortoise.models import Model

from axegaoshop.db.models.user import User


class Ticket(Model):
    """таблица с данными по тикетам"""

    id = fields.IntField(pk=True, unique=True)

    user = fields.ForeignKeyField("axegaoshop.User", related_name="tickets")

    status = fields.TextField(
        null=False, default="opened"
    )  # статусы тикета: opened, closed

    created_at = fields.DatetimeField(
        auto_now_add=True, null=False
    )  # дата-время закрытия
    closed_at = fields.DatetimeField(null=True)  # дата-время закрытия

    messages: fields.ReverseRelation["TicketMessage"]

    def last_message(self) -> str:
        """получение последнего сообщения из тикета"""
        try:
            return self.messages[-1].text
        except NoValuesFetched:
            return ""

    class Meta:
        table = "tickets"
        ordering = ["created_at"]

    class PydanticMeta:
        computed = ("last_message",)
        exclude = (
            "user.reviews",
            "user.orders",
            "user.shop_cart",
            "user.tickets",
            "user.reg_datetime",
            "user.balance",
            "user.username",
            "user.is_active",
            "user.is_anonymous",
            "user.is_admin",
            "user.photo",
            "user.replenishes",
        )

    async def close(self):
        """закрытие тикета"""
        self.status = "closed"
        self.closed_at = datetime.now()
        await self.save()


class TicketMessage(Model):
    """таблица с диалогами и сообщениями админа/юзера"""

    id = fields.IntField(pk=True, unique=True)

    ticket = fields.ForeignKeyField("axegaoshop.Ticket", related_name="messages")

    role = fields.CharField(max_length=20, null=False)  # роль написавшего - user/admin

    text = fields.TextField(null=False)  # текст сообщения

    created_at = fields.DatetimeField(auto_now_add=True)

    attachments: fields.ReverseRelation["TicketMessageAttachment"]

    class Meta:
        table = "ticket_messages"
        ordering = ["created_at"]


class TicketMessageAttachment(Model):
    """прикрепленные файлы к сообщениям в ТП"""

    id = fields.IntField(pk=True, unique=True)

    file = fields.TextField(null=False)  # айди файла из /uploads

    ticket_message = fields.ForeignKeyField(
        "axegaoshop.TicketMessage", related_name="attachments"
    )

    class Meta:
        table = "ticket_attachments"


async def get_or_create_ticket(user: User) -> Ticket:
    """получение текущего тикета или создание нового у пользователя"""
    return (await Ticket.get_or_create(user=user, status="opened"))[0]


async def get_user_all_dialog(user: User) -> list[dict]:
    """получение всех сообщений из тикетов пользователя"""
    data = []
    all_messages = await TicketMessage.filter(ticket__user=user).all()

    for message in all_messages:
        data.append(
            {
                "role": message.role,
                "message": message.text,
                "created_at": message.created_at,
                "attachments": await message.attachments.all().values_list(
                    "file", flat=True
                ),
            }
        )

    return data
