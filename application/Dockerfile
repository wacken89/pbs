FROM python:3.7.3-alpine3.8
RUN mkdir -p /opt/bin
WORKDIR /opt/bin

COPY ./codebase /opt/bin
CMD [ "python", "-u", "logsGenerator.py" ]