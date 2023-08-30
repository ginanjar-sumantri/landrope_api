# from sqlmodel import SQLModel, Field, Relationship
# from sqlalchemy import Column
# from models.base_model import BaseUUIDModel
# from uuid import UUID
# from pydantic import condecimal

# class GiroBase(SQLModel):
#     code:str = Field(sa_column=(Column(unique=True)), nullable=False)
#     amount:condecimal(decimal_places=2) = Field(nullable=False, default=0)
#     is_active:bool = Field(default=True)

# class GiroFullBase(BaseUUIDModel, GiroBase):
#     pass

# class Giro(GiroFullBase, table=True):
#     pass