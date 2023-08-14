
import datetime
import uuid
import io
from typing import TypeVar, Tuple

from fastapi import UploadFile
from google.cloud import storage
from sqlmodel import SQLModel

from configs.config import settings
# from models.sub_project_image import SubProjectImage

# if TYPE_CHECKING:

ModelType = TypeVar("ModelType", bound=SQLModel)


class GCStorageService:
    def __init__(self) -> None:
        self.storage_client = storage.Client()
        self.bucket_name = settings.GS_BUCKET_NAME

    @staticmethod
    async def path_and_rename(model_type: ModelType, upload_file: UploadFile) -> str:
        # if isinstance(model_type, SubProjectImage):
        #     upload_to = 'marketing/sub_project_image/'

        # else:
        upload_to = 'upload_bulking/'
        ext = upload_file.filename.split('.')[-1]
        # get filename
        if model_type.id:
            filename = f'{model_type.id}.{ext}'
        else:
            # set filename as random string
            filename = f'{uuid.uuid4().hex}.{ext}'
        # return the whole path to the file
        return upload_to+filename
    
    @staticmethod
    async def path_and_rename_dokumen(upload_file: UploadFile, file_name:str = None) -> str:
        
        upload_to = 'upload_dokumen/'
        ext = upload_file.filename.split('.')[-1]
        
        if file_name:
            filename = f'{filename}.{ext}'
        else:
            # set filename as random string
            filename = f'{uuid.uuid4().hex}.{ext}'
        # return the whole path to the file
        return upload_to+filename
    
    @staticmethod
    async def path_and_rename_zip(upload_file: UploadFile) -> Tuple[str | None, str | None]:
        # if isinstance(model_type, SubProjectImage):
        #     upload_to = 'marketing/sub_project_image/'

        # else:
        upload_to = 'upload_bulking/'
        files = upload_file.filename.split('.')
        # get filename
        # if model_type.id:
        #     filename = f'{model_type.id}.{ext}'
        # else:
        #     # set filename as random string
        #     filename = f'{uuid.uuid4().hex}.{ext}'
        filename = f'{files[0]}-{str(datetime.datetime.now())}.{files[1]}'
        # return the whole path to the file
        return upload_to+filename, filename

    async def upload_image(self, file: UploadFile, obj_current: ModelType) -> str:
        bucket = self.storage_client.get_bucket(self.bucket_name)
        file_path = await self.path_and_rename(model_type=obj_current, upload_file=file)
        blob = bucket.blob(file_path)
        blob.upload_from_file(file_obj=file.file, content_type='image/jpeg')

        return file_path

    async def upload_file_dokumen(self, file: UploadFile, file_name:str = None) -> str:
        bucket = self.storage_client.get_bucket(self.bucket_name)
        file_path = await self.path_and_rename_dokumen(upload_file=file, file_name=file_name)
        blob = bucket.blob(file_path)
        blob.upload_from_file(file_obj=file.file,
                              content_type=file.content_type)

        return file_path
    
    async def upload_excel(self, file: UploadFile) -> Tuple[str | None, str | None]:
        bucket = self.storage_client.get_bucket(self.bucket_name)
        file_path, file_name = await self.path_and_rename_zip(upload_file=file)
        blob = bucket.blob(file_path)
        blob.upload_from_file(file_obj=file.file,
                              content_type=file.content_type)

        return file_path, file_name
    
    async def upload_zip(self, file: UploadFile) -> Tuple[str | None, str | None]:
        bucket = self.storage_client.get_bucket(self.bucket_name)
        file_path, file_name = await self.path_and_rename_zip(upload_file=file)
        blob = bucket.blob(file_path)
        blob.upload_from_file(file_obj=file.file,
                              content_type='application/zip')

        return file_path, file_name
    
    async def download_file(self, file_path:str | None):
        bucket = self.storage_client.get_bucket(self.bucket_name)
        blob = bucket.blob(file_path)
        file_content = blob.download_as_bytes()

        return io.BytesIO(file_content)
    
    async def download_dokumen(self, file_path:str | None):
        bucket = self.storage_client.get_bucket(self.bucket_name)
        blob = bucket.blob(file_path)
        file_content = blob.download_as_bytes()

        return file_content


    def generate_upload_signed_url_v4(self, blob_name) -> str | None:
        if blob_name is not None:
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)

            url = blob.generate_signed_url(
                version="v4",
                # This URL is valid for 24 hours
                expiration=datetime.timedelta(seconds=86400),
                method="GET"
            )
        else:
            url = None

        return url

    async def delete_blob(self, blob_name) -> None:
        if blob_name is not None:
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete
