# Signum Explorer
This documentation is a work in progress. More details to follow.


## Requirements

 - A [Signum Node](https://github.com/signum-network/signum-node) with MariaDB version 3.3.0 or up is required.
 - Python3, Redis server, and many python modules.

### Linux

Install the following packages

```
sudo apt install python3-dev default-libmysqlclient-dev build-essential redis-server gunicorn supervisor
```

### Windows

(python and other tools equivalent to the above list)

### Modules (all platforms)

The following python modules are required as well:
```
pip3 install celery django django-cache-memoize django-cors-headers django-filter django-redis djangorestframework django-static-fontawesome gunicorn jsonschema mysqlclient pycoingecko python-redis-lock requests sentry-sdk simplejson supervisor whitenoise python-dotenv
```

Download the [free version of fontawesome](https://use.fontawesome.com/releases/v5.15.4/fontawesome-free-5.15.4-web.zip) and extract to the `static` folder:
```
cd static
wget https://use.fontawesome.com/releases/v5.15.4/fontawesome-free-5.15.4-web.zip
unzip fontawesome-free-5.15.4-web.zip
```

## Set-up

Make a copy of the default environment configuration:

`cp .env.default .env`

Edit the `.env` to suit your needs.

To initilize the explorer database (DB_DEFAULT) run the following command:
```python manage.py migrate --no-input```

Start the django webserver as development:
```python manage.py runserver 0.0.0.0:5000```

Start with gunicorn:
```gunicorn config.wsgi -c gunicorn.conf.py```

To run in production use the provided supervisord.conf to run the service with supervisord:
```/path/to/your/supervisord -c /supervisord.conf```
