# 
FROM --platform=linux/amd64 python:3.10.9-slim
RUN apt-get update
RUN apt-get install -y gcc
RUN apt-get install -y default-libmysqlclient-dev
ENV PYTHONBUFFERED 1

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./ /code

# 
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8305"]
CMD ["sh", "-c", "gunicorn main:app --bind :8602 --workers 4 -k uvicorn.workers.UvicornWorker"]