web: gunicorn --workers=2 --worker-class=eventlet --max-requests=1000 --max-requests-jitter=100 -b 0.0.0.0:8080 app:app
