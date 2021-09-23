# Shengji Server
Flask app to facilitate playing shengji over network

## Run app locally
First make sure to have poetry installed then
```
poetry install
export FLASK_APP=shengji_server/app.py
poetry run flask run -h 0.0.0.0
```

## How I upload to the server
```
pscp -load renzhi -r ./ ec2-user@ec2-18-130-103-108.eu-west-2.compute.amazonaws.com:/home/ec2-user/shengji_server
```

## On AWS RHEL instance
I can't get poetry to work, so
```
export FLASK_APP=shengji_server/app.py
pip install flask-socketio=4.3.2
flask run -h 0.0.0.0 -p 5002
```
