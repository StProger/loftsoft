from fastapi.routing import APIRouter

from axegaoshop.web.api import (
    categories,
    faqs,
    healthcheck,
    orders,
    partners,
    products,
    promocodes,
    reviews,
    shop_carts,
    slugs,
    subcategories,
    tickets,
    uploads,
    users,
)
from axegaoshop.web.api.notifications import telegram
from axegaoshop.web.api.payment_settings.sbp import ozone_bank
from axegaoshop.web.api.products import options, parameters, photos, request

api_router = APIRouter()

api_router.include_router(router=users.router, prefix="", tags=["Users"])

api_router.include_router(router=categories.router, prefix="", tags=["Category"])

api_router.include_router(router=subcategories.router, prefix="", tags=["Subcategory"])

api_router.include_router(router=products.router, prefix="", tags=["Products"])

api_router.include_router(router=options.router, prefix="", tags=["Product options"])
api_router.include_router(router=photos.router, prefix="", tags=["Product photos"])
api_router.include_router(
    router=parameters.router, prefix="", tags=["Product parameters"]
)

api_router.include_router(router=faqs.router, prefix="", tags=["User FAQ"])

api_router.include_router(router=orders.router, prefix="", tags=["Orders"])

api_router.include_router(router=promocodes.router, prefix="", tags=["Promocodes"])

api_router.include_router(router=shop_carts.router, prefix="", tags=["Shop Cart"])

api_router.include_router(router=partners.router, prefix="", tags=["Partners"])

api_router.include_router(router=uploads.router, prefix="", tags=["Uploads"])

api_router.include_router(router=reviews.router, prefix="", tags=["Reviews"])

api_router.include_router(
    router=ozone_bank.router, prefix="", tags=["SBP Ozone Bank Settings"]
)

api_router.include_router(router=slugs.router, prefix="", tags=["Slugs"])

api_router.include_router(router=healthcheck.router, prefix="", tags=["Healthcheck"])

api_router.include_router(
    router=telegram.router, prefix="", tags=["Telegram Notifications"]
)

api_router.include_router(router=tickets.router, prefix="", tags=["Tickets"])

api_router.include_router(router=request.router, prefix="", tags=["Request Product"])
