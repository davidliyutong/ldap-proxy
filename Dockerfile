FROM python:3.8.0-slim
ENV LANG=C.UTF-8
EXPOSE 8080
WORKDIR /opt/app/

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install ldap3==2.9.1 flask==2.0.2 flask-httpauth==4.7.0
COPY src/* /opt/app/

ENTRYPOINT ["python"]
CMD ["./app.py"]