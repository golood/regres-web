FROM python:3.8.6
COPY . /app
WORKDIR /app
#RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev g++ build-base linux-headers pcre-dev tzdata
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
ENTRYPOINT [ "python" ] 
CMD [ "app.py" ]
