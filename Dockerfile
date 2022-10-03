FROM python:3.8.0-slim
ENV LANG=C.UTF-8
EXPOSE 8080
WORKDIR /opt/app/

COPY requirements.txt /tmp/
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

COPY src/* /opt/app/

ENTRYPOINT ["python"]
CMD ["./app.py"]