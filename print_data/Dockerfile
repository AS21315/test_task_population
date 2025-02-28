FROM python:3.10-slim

WORKDIR /app

COPY . /tmp/build/
RUN pip install --no-cache-dir -r /tmp/build/requirements.txt

CMD ["python", "/app/print_data/print_data.py"]