from typing import List

from axegaoshop.settings import settings

MODELS_MODULES_PREFIX: str = "axegaoshop.db.models"

MODELS_MODULES: List[str] = [
    f"{MODELS_MODULES_PREFIX}.user",
    f"{MODELS_MODULES_PREFIX}.token",
    f"{MODELS_MODULES_PREFIX}.category",
    f"{MODELS_MODULES_PREFIX}.product",
    f"{MODELS_MODULES_PREFIX}.shop_cart",
    f"{MODELS_MODULES_PREFIX}.subcategory",
    f"{MODELS_MODULES_PREFIX}.promocode",
    f"{MODELS_MODULES_PREFIX}.order",
    f"{MODELS_MODULES_PREFIX}.review",
    f"{MODELS_MODULES_PREFIX}.partner",
    f"{MODELS_MODULES_PREFIX}.payment_settings",
    f"{MODELS_MODULES_PREFIX}.password_reset",
    f"{MODELS_MODULES_PREFIX}.replenish",
    f"{MODELS_MODULES_PREFIX}.telegram_settings",
    f"{MODELS_MODULES_PREFIX}.ticket",
    f"{MODELS_MODULES_PREFIX}.faq",
]

TORTOISE_CONFIG = {
    "connections": {
        "default": str(settings.db_url),
    },
    "apps": {
        "axegaoshop": {
            "models": MODELS_MODULES + ["aerich.models"],
            "default_connection": "default",
        },
    },
}
