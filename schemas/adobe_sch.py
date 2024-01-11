from sqlmodel import SQLModel

class ResponseAssetSch(SQLModel):
    uploadUri:str|None
    assetID:str|None

class ResponseExportExcel(SQLModel):
    type:str|None
    downloadUri:str|None
    assetID:str|None