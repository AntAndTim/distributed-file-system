FROM python:3.8.0
EXPOSE 8080
COPY . /file_container
WORKDIR /file_container
RUN pip install --no-cache-dir -r requirements.txt
CMD python server.py

