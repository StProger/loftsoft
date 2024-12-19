from fastapi import APIRouter

from axegaoshop.web.api.products.request.schema import ItemRequest

router = APIRouter()


@router.post(path="/product/request", status_code=200)
async def create_item_request(item_request: list[ItemRequest]):

    print(item_request)

    # return await PhotoIn_Pydantic.from_queryset(ProductPhoto.filter(product_id=id))
