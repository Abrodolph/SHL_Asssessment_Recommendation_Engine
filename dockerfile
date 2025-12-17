FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

# Create a writable directory for ChromaDB if needed, though usually fine in Docker
RUN chmod -R 777 /code

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]