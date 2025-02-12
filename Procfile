web: gunicorn roboticCertifier.wsgi --log-file -

web: python manage.py migrate && python manage.py collectstatic --noinput  && gunicorn roboticCertifier.wsgi