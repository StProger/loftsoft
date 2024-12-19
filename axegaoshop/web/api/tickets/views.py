import asyncio
import typing

from fastapi import APIRouter, Depends, HTTPException
from tortoise.expressions import Q

from axegaoshop.db.models.ticket import (
    Ticket,
    TicketMessage,
    TicketMessageAttachment,
    get_or_create_ticket,
)
from axegaoshop.db.models.user import User
from axegaoshop.services.notifications.mailing.mailing import Mailer
from axegaoshop.services.security.jwt_auth_bearer import JWTBearer
from axegaoshop.services.security.users import current_user_is_admin, get_current_user
from axegaoshop.settings import executor
from axegaoshop.web.api.tickets.schema import TicketIn_Pydantic, TicketMessageSend

router = APIRouter()


@router.post(
    path="/tickets/send",
    dependencies=[Depends(JWTBearer())],
    response_model=TicketIn_Pydantic | list[TicketIn_Pydantic],
)
async def send_or_create_ticket(
    ticket_message_request: TicketMessageSend, user: User = Depends(get_current_user)
):
    """функционал:

    Человек пишет сообщение, отправляет, если есть открытый тикет от этого человека - сообщение просто
    попадает в этот тикет. Если открытого тикета нет - создается новый.

    У админа соответственно эти тикеты отображаются.

    И админ и пользователь стучатся в одно место, сообщения в зависимости от роли распределяются.
    """
    if not user.is_admin and not user.email:
        raise HTTPException(status_code=401, detail="EMAIL_REQUIRED")

    if not ticket_message_request.id:
        ticket: Ticket = await get_or_create_ticket(user)
    else:
        ticket: Ticket = await Ticket.get_or_none(id=ticket_message_request.id)
        if not ticket or ticket.status == "closed":
            raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")

    role: typing.Literal["user", "admin"] = "user" if not user.is_admin else "admin"

    ticket_message = await TicketMessage.create(
        ticket=ticket, role=role, text=ticket_message_request.text
    )

    # отправка текста тикета человеку на почту
    if role == "admin":
        mailer = Mailer(recipient=(await ticket.user.get()).email)

        executor.submit(mailer.send_ticket_message(content=ticket_message_request.text))

    await TicketMessageAttachment.bulk_create(
        [
            TicketMessageAttachment(file=f, ticket_message=ticket_message)
            for f in ticket_message_request.attachments
        ]
    )

    if role == "admin":
        return await TicketIn_Pydantic.from_queryset_single(
            Ticket.filter(id=ticket.id).first()
        )
    else:
        return await TicketIn_Pydantic.from_queryset(Ticket.filter(user=user).all())


@router.get(
    path="/ticket/{id}",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=TicketIn_Pydantic,
)
async def get_ticket_by_id(id: int):
    ticket = await Ticket.get_or_none(id=id)

    if not ticket:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")

    return await TicketIn_Pydantic.from_tortoise_orm(ticket)


@router.get(
    path="/tickets",
    dependencies=[Depends(JWTBearer())],
    response_model=list[TicketIn_Pydantic],
)
async def get_tickets_all(user: User = Depends(get_current_user)):
    """получение всех сообщения из всех тикетов для пользователя"""
    return await TicketIn_Pydantic.from_queryset(Ticket.filter(user=user).all())


@router.get(
    path="/tickets/opened",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[TicketIn_Pydantic],
)
async def get_opened_tickets():
    """получение открытых тикетов (админка)"""
    return await TicketIn_Pydantic.from_queryset(Ticket.filter(status="opened").all())


@router.get(
    path="/tickets/closed",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=list[TicketIn_Pydantic],
)
async def get_closed_tickets():
    """получение закрытых тикетов (история) (админка)"""
    return await TicketIn_Pydantic.from_queryset(Ticket.filter(status="closed").all())


@router.post(
    path="/ticket/{id}/close",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    response_model=TicketIn_Pydantic,
)
async def close_ticket_by_id(id: int):
    """закрытие тикета из админки"""
    ticket = await Ticket.get_or_none(Q(id=id), Q(status="opened"))

    if not ticket:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")

    await ticket.close()

    await ticket.refresh_from_db()

    return await TicketIn_Pydantic.from_tortoise_orm(ticket)


@router.post(
    path="/ticket/{id}/delete",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=200,
)
async def delete_ticket_by_id(id: int):
    """удаление тикета из админки"""
    ticket = await Ticket.get_or_none(
        Q(id=id), Q(Q(status="opened") | Q(status="closed"))
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="TICKET_NOT_FOUND")

    await ticket.delete()


@router.post(
    path="/tickets/close",
    dependencies=[Depends(JWTBearer()), Depends(current_user_is_admin)],
    status_code=201,
)
async def close_all_tickets():
    """закрытие всех тикетов из админки"""
    await Ticket.filter(status="opened").update(status="closed")
