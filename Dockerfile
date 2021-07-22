FROM python:3

WORKDIR /app

COPY . /app
RUN pip3 install -r requirements.txt

CMD [ "python3", "-m", "flask", "run", "--host=0.0.0.0"]
EXPOSE 5000