import requests
from configs.config import settings

class PdfService:
    PDF_URL = settings.PDF_URL
    OAUTH_DEFAULT_TOKEN = settings.OAUTH2_TOKEN
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