# Dockerfile

FROM python:3.10.11
EXPOSE 9000
RUN pip3 install gevent
RUN pip3 install flask
RUN pip3 install flask
RUN pip3 install requests
RUN pip3 install openai
RUN mkdir -p /data/api
COPY app.py /data/api/app.py
CMD ["python3", "/data/api/app.py"]