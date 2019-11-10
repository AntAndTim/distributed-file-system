FROM python:3.8.0
EXPOSE 8081
COPY . /naming_server
WORKDIR /naming_server
RUN pip install --no-cache-dir -r requirements.txt
CMD python server.py