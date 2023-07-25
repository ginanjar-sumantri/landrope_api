from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union
from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class ContentNoChangeException(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers
        )

class ImportFailedException(HTTPException):
    def __init__(
        self,
        filename:str|None = None,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        if filename:
            super().__init__(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"Import file {filename} failed, please check data of file", 
                headers=headers
            )
        
        super().__init__(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"Import file {filename} failed, please check data of file", 
                headers=headers
            )

class DocumentFileNotFoundException(HTTPException):
    def __init__(
        self,
        dokumenname: Type[ModelType],
        headers: Dict[str, Any] | None = None,
    ) -> None:
        
        super().__init__(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=f"{dokumenname} file, failed to download", 
                headers=headers
            )


class IdNotFoundException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        id: UUID | str | None = None,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        if id:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find the {model.__name__} with id {id}.",
                headers=headers,
            )
            return

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} id not found.",
            headers=headers,
        )


class NameNotFoundException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        name: str | None = None,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        if name:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find the {model.__name__} named {name}.",
                headers=headers,
            )
        else:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find the {model.__name__} named {name}.",
                headers=headers,
            )


class NameExistException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        name: str | None = None,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        if name:
            super().__init__(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The {model.__name__} name {name} already exists.",
                headers=headers,
            )
            return

        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The {model.__name__} name already exists.",
            headers=headers,
        )

class CodeExistException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        code: str | None = None,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        if code:
            super().__init__(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The {model.__name__} code {code} already exists.",
                headers=headers,
            )
            return

        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The {model.__name__} code already exists.",
            headers=headers,
        )

class EmailExistException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        email: str | None = None,
        headers: Dict[str, Any] | None = None,
    ) -> None:
        if email:
            super().__init__(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The {model.__name__} email {email} already exists.",
                headers=headers,
            )
            return

        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The {model.__name__} email already exists.",
            headers=headers,
        )