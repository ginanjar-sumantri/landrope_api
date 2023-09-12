import datetime
import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from configs.config import settings
from models.import_log_model import ImportLog
from typing import Dict, Any


class GCloudTaskService:
    client = tasks_v2.CloudTasksClient()

    def _delete_task(self, path: str):
        try:
            self.client.delete_task(name=path)
        except Exception as e:
            print(f'raised exc when deleting task -> {str(e)}')

    def _create_task(self,
                     url: str,
                     payload: dict | None = None,
                     http_method: str = 'POST',
                     with_token: str = 'SETTING',
                     in_seconds: int = 1,
                     queue_name: str = 'landrope-queue',
                     task_name: str | None = None,
                     execute_at=None) -> str:
        parent = self.client.queue_path(
            project=settings.GS_PROJECT_ID,
            location=settings.QUEUE_LOCATION,
            queue=queue_name
        )

        if http_method == 'POST':
            http_method = tasks_v2.HttpMethod.POST
        elif http_method == 'GET':
            http_method = tasks_v2.HttpMethod.GET
        else:
            http_method = tasks_v2.HttpMethod.POST

        task = {
            "http_request": {  # Specify the type of request.
                "http_method": http_method,
                "url": url,  # The full url path that the task will be sent to.
            }
        }

        if with_token:
            token = settings.OAUTH2_TOKEN if with_token == 'SETTING' else with_token
            task["http_request"]["headers"] = {"Authorization": "Bearer " + token}

        if payload is not None:
            if isinstance(payload, dict):
                # Convert dict to JSON string
                payload = json.dumps(payload)
                # specify http content-type to application/json
                task["http_request"]["headers"]["Content-type"] = "application/json"

            # The API expects a payload of type bytes.
            converted_payload = payload.encode()

            # Add the payload to the request.
            task["http_request"]["body"] = converted_payload

        if execute_at:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(execute_at)
            task["schedule_time"] = timestamp
        elif in_seconds is not None:
            # Convert "seconds from now" into an rfc3339 datetime string.
            d = datetime.datetime.utcnow() + datetime.timedelta(seconds=in_seconds)

            # Create Timestamp protobuf.
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(d)

            # Add the timestamp to the tasks.
            task["schedule_time"] = timestamp

        if task_name is not None:
            # Add the name to tasks.
            task["name"] = self.client.task_path(settings.PROJECT_NAME, settings.QUEUE_LOCATION,
                                                 queue_name, task_name)

        # Use the client to build and send the task.
        response = self.client.create_task(request={"parent": parent, "task": task})

        print("Created task {}".format(response.name))

        return response.name

    def create_task_import_data(self, import_instance: ImportLog, base_url: str):
        url = base_url
        url = url.replace('http://', 'https://')

        payload = {
            "import_log_id": str(import_instance.id),
            "file_path": import_instance.file_path,
        }
        try:
            task = self._create_task(
                url=url,
                queue_name='landrope-queue',
                payload=payload
            )
        except Exception as e:
            print(e)
        return import_instance
    
    def create_task(self, payload: Dict[str, Any], base_url:str):
        url = base_url
        url = url.replace('http://', 'https://')

        payload = payload
        try:
            task = self._create_task(
                url=url,
                queue_name='landrope-queue',
                payload=payload
            )
        except Exception as e:
            print(e)
        return payload