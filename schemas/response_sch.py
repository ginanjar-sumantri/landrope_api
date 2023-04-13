import math
from typing import Any, Dict, Generic, Sequence, Union, Optional, TypeVar
from fastapi_pagination import Params, Page
from fastapi_pagination.bases import AbstractPage, AbstractParams
from pydantic.generics import GenericModel

T = TypeVar("T")

class PageBase(Page[T], Generic[T]):
    pages: int
    next_page: int | None
    previous_page: int | None


class ResponseBaseSch(GenericModel, Generic[T]):
    message: str = ""
    meta: Dict = {}
    data: T | None


class ResponsePageSch(AbstractPage[T], Generic[T]):
    message: str = ""
    meta: Dict = {}
    data: PageBase[T]

    __params_type__ = Params  # Set params related to Page

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        params: AbstractParams,
    ) -> PageBase[T] | None:
        pages = math.ceil(total / params.size)
        return cls(
            data=PageBase(
                items=items,
                page=params.page,
                size=params.size,
                total=total,
                pages=pages,
                next_page=params.page + 1 if params.page < pages else None,
                previous_page=params.page - 1 if params.page > 1 else None,
            )
        )


class GetResponseBaseSch(ResponseBaseSch[T], Generic[T]):
    message: str = "Data got correctly"


class GetResponsePaginatedSch(ResponsePageSch[T], Generic[T]):
    message: str = "Data got correctly"


class PostResponseBaseSch(ResponseBaseSch[T], Generic[T]):
    message: str = "Data created correctly"


class PutResponseBaseSch(ResponseBaseSch[T], Generic[T]):
    message: str = "Data updated correctly"


class DeleteResponseBaseSch(ResponseBaseSch[T], Generic[T]):
    message: str = "Data deleted correctly"

class ImportResponseBaseSch(ResponseBaseSch[T], Generic[T]):
    message: str = "Import file Successfully"


def create_response(
    data: T | None,
    message: str | None = None,
    meta: Dict | Any | None = {},
) -> Dict[str, T] | T:
    if isinstance(data, ResponsePageSch):
        data.message = "Data paginated correctly" if not message else message
        data.meta = meta
        return data
    body_response = {"data": data, "message": message, "meta": meta}
    # It returns a dictionary to avoid doble
    # validation https://github.com/tiangolo/fastapi/issues/3021
    return dict((k, v) for k, v in body_response.items() if v is not None)