#!/bin/sh

# Initialize the database
flask db upgrade

# Start the gunicorn server
exec gunicorn --bind 0.0.0.0:8080 app:app