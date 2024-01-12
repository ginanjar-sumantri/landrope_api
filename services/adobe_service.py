import requests
import time
from fastapi import HTTPException
from configs.config import settings
from schemas.adobe_sch import ResponseAssetSch, ResponseExportExcel
from io import BytesIO

class PDFToExcelService:

    
    async def export_pdf_to_excel(self, data) -> BytesIO | None:

        excel_content = None
        token = await self.get_token()
        asset = await self.create_asset(token=token)
        ok = await self.upload_file_to_asset(data=data, asset=asset)
        if ok:
            location = await self.export_to_excel(asset=asset, token=token)
            result = await self.get_file_from_location(location=location, token=token)
            try:
                # Mengunduh file dari URL
                response = requests.get(url=result.downloadUri)
                response.raise_for_status()  # Membuang exception jika permintaan gagal

                # Membaca konten sebagai objek bytes
                excel_content = BytesIO(response.content)

            except requests.RequestException as e:
                raise HTTPException(status_code=500, detail=f"Error dalam mengunduh file: {str(e)}")

        return excel_content
    
    async def get_token(self) -> str:

        url = "https://pdf-services.adobe.io/token"

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        body = {
            "client_id" : str(settings.ADOBE_CLIENT_ID),
            "client_secret" : str(settings.ADOBE_CLIENT_SECRET)
        }

        response = requests.post(url=url, headers=headers, data=body)
        if 200 <= response.status_code <=299:
            r = response.json()
            token = r["access_token"]
            return token
        else:
            raise HTTPException(status_code=422, detail="Failed Export Excel. Detail : Can't create token")
    
    # Membuat asset (file pdf) pada internal storage adobe
    async def create_asset(self, token:str) -> ResponseAssetSch:

        response_asset:ResponseAssetSch = None

        url = "https://pdf-services.adobe.io/assets"
        headers = {
                'Authorization': 'Bearer ' + str(token),
                'Content-Type': 'Application/Json',
                'x-api-key' : str(settings.ADOBE_CLIENT_ID)
            }
        body = {
                    "mediaType": "application/pdf"
            }

        response = requests.post(url=url, json=body, headers=headers)
        if 200 <= response.status_code <=299:
            r = response.json()
            response_asset = ResponseAssetSch(**r)
        else:
            raise HTTPException(status_code=422, detail="Failed Export Excel. Detail : Can't create asset")
        
        return response_asset
    
    async def upload_file_to_asset(self, data, asset:ResponseAssetSch) -> bool:

        headers = {
            'Content-Type': 'application/pdf'
        }

        response = requests.put(url=asset.uploadUri, data=data, headers=headers)
        if 200 <= response.status_code <=299:
            return True
        else:
            raise HTTPException(status_code=422, detail="Failed Export Excel. Detail : Failed upload to asset")
    
    async def export_to_excel(self, asset:ResponseAssetSch, token:str) -> str:

        url = "https://pdf-services-ue1.adobe.io/operation/exportpdf"
        headers = {
                'Authorization': 'Bearer ' + str(token),
                'Content-Type': 'Application/Json',
                'x-api-key' : str(settings.ADOBE_CLIENT_ID)
            }
        body = {
                "assetID": str(asset.assetID),
                "targetFormat": "xlsx",
                "ocrLang" : "ru-RU"
            }
        response = requests.post(url=url, json=body, headers=headers)

        if 200 <= response.status_code <=299:
            location = response.headers.get('location', None)
            if location is None:
                raise HTTPException(status_code=422, detail="Failed Export Excel. Detail : Failed to Export")
            
            return location
        else:
            raise HTTPException(status_code=422, detail="Failed Export Excel. Detail : Failed to Export")
    
    async def get_file_from_location(self, location:str, token) -> ResponseExportExcel:

        url = location
        headers = {
                'Authorization': 'Bearer ' + token,
                'x-api-key' : str(settings.ADOBE_CLIENT_ID)
            }
        
        response_export:ResponseExportExcel = None
        status:str = "inprogress"

        while status == "inprogress":
            response = requests.get(url=url, headers=headers)
            r = response.json()
            if r['status'] == "done":
                response_export = ResponseExportExcel(downloadUri=r['asset']['downloadUri'], type=r['asset']['metadata']['type'], assetID=r['asset']['assetID'])
                status = "done"
                break
            elif r['status'] == "failed":
                status = "failed"
                break

            time.sleep(2)

        if status == "failed":
            raise HTTPException(status_code=422, detail="Failed Export Excel. Detail : Failed to get from asset")
        
        return response_export
        


    



