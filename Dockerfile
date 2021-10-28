FROM python:3.9-alpine 

WORKDIR /usr/src/app

RUN addgroup -S toriuser && adduser -S toriuser -G toriuser
USER toriuser

RUN pip3 install --no-cache bs4 python-dotenv requests

COPY tori.py ./

CMD [ "python", "-u", "./tori.py" ]
