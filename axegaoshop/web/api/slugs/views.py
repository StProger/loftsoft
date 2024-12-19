import typing

from fastapi import APIRouter, HTTPException

from axegaoshop.db.models.category import Category
from axegaoshop.db.models.product import Product
from axegaoshop.db.models.subcategory import Subcategory

router = APIRouter()


@router.get(
    path="/get_slug",
    description="Получение slug для роутинга для категории/подкатегории/товара",
)
async def get_slug(
    obj: typing.Literal["category", "subcategory", "product"], obj_id: int
):
    if obj == "category":
        category_: Category = await Category.get_or_none(id=obj_id)
        if not category_:
            raise HTTPException(status_code=404, detail="NOT_FOUND")

        return category_.slug()

    elif obj == "subcategory":
        subcategory_: Subcategory = await Subcategory.get_or_none(id=obj_id)

        if not subcategory_:
            raise HTTPException(status_code=404, detail="NOT_FOUND")

        return (await subcategory_.category.get()).slug() + "/" + subcategory_.slug()

    elif obj == "product":
        product_: Product = await Product.get_or_none(id=obj_id)

        if not product_:
            raise HTTPException(status_code=400, detail="NOT_FOUND")

        return (
            (await (await product_.subcategory.get()).category.get()).slug()
            + "/"
            + (await product_.subcategory.get()).slug()
            + "/"
            + product_.slug()
        )

    else:
        raise HTTPException(status_code=404, detail="OBJ_NOT_FOUND")
