FROM python:3.9-slim

WORKDIR /app

COPY . /tmp/build/
RUN pip install --no-cache-dir -r /tmp/build/requirements.txt

# Options: 'wikipedia' or 'statisticstimes'
ENV DATA_SOURCE=statisticstimes

CMD ["python", "/app/get_data/get_data.py"]