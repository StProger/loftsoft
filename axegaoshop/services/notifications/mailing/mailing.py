from dataclasses import dataclass

import yagmail

from axegaoshop.services.notifications.mailing.utils import render_template
from axegaoshop.settings import settings


@dataclass
class MessageTypes:
    """типы почтовых сообщений"""

    RESET_PASSWORD = "reset.html"
    SHIPPING = "shipping.html"
    PURCHASE = "purchase.html"
    TICKET_MESSAGE = "message.html"


class Mailer:
    """модуль для работы с почтовыми сообщениями"""

    def __init__(self, recipient: str):
        self.mailer_ = yagmail.SMTP(
            user=settings.mail_user,
            password=settings.mail_password,
            host=settings.mail_host,
            port=settings.mail_port,
        )
        # получатель письма
        self.recipient = recipient

    def send_reset(self, reset_url: str):
        """письмо на сброс пароля"""
        self.mailer_.send(
            self.recipient,
            subject="LoftSoft Сброс Пароля",
            contents=render_template(MessageTypes.RESET_PASSWORD, reset_url=reset_url),
        )

    def send_shipping(
        self,
        parameters: list[dict],
        total_sum: float,
        total_count: int,
        hand: bool = True,
    ):
        """письмо на покупку товара"""
        if not hand:
            self.mailer_.send(
                self.recipient,
                subject="LoftSoft Покупка Товара",
                contents=render_template(
                    MessageTypes.PURCHASE,
                    parameters=parameters,
                    total_sum=total_sum,
                    total_count=total_count,
                ),
            )
        else:
            self.mailer_.send(
                self.recipient,
                subject="LoftSoft Покупка Товара",
                contents=render_template(
                    MessageTypes.SHIPPING,
                    parameters=parameters,
                    total_sum=total_sum,
                    total_count=total_count,
                ),
            )

    def send_ticket_message(self, content: str):
        """отправка сообщения из тикета"""
        self.mailer_.send(
            self.recipient,
            subject="LoftSoft Сообщение от Поддержки",
            contents=render_template(MessageTypes.TICKET_MESSAGE, content=content),
        )
