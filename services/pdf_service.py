import requests
from configs.config import settings

class PdfService:
    PDF_URL = settings.PDF_URL
    OAUTH_DEFAULT_TOKEN = settings.OAUTH2_TOKEN

    REPORT_SERVICE_URL = settings.REPORT_SERVICE_URL
    async def get_pdf(self, data):
        try:
            url = "{}pdf/download".format(self.PDF_URL)

            headers = {
                'Authorization': 'Bearer ' + str(self.OAUTH_DEFAULT_TOKEN),
                'Content-Type': 'Application/Json'
            }

            body = {
                "template":data
            }
            response = requests.post(url, json=body, headers=headers)
            if 200 <= response.status_code <= 299:
                return response.content
            else:
                raise Exception
        except Exception as e:
            raise e
        
    async def get_pdf_from_report_service(self, data):
        try:
            url = "{}rs/pdf/file/generate".format(self.REPORT_SERVICE_URL)

            headers = {
                # 'Authorization': 'Bearer ' + str(self.OAUTH_DEFAULT_TOKEN),
                'Content-Type': 'Application/Json'
            }

            response = requests.post(url, json=data, headers=headers)
            if 200 <= response.status_code <= 299:
                return response.content
            else:
                raise Exception
        except Exception as e:
            raise e