FROM python:3

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /app
CMD ["python", "src/main/python/gateway.py", "--log-level debug"]
#CMD ["gunicorn" , "-w", "3" , "--pythonpath src/main/python/", "--log-level", "debug", "src/main/python/gateway:application"]