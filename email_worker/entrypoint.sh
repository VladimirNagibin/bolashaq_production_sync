#!/bin/bash

set -e

echo "Starting Email Worker Service..."

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ at ${RABBIT_HOST}:${RABBIT_PORT}..."
while ! nc -z ${RABBIT_HOST} ${RABBIT_PORT}; do
  sleep 1
done
echo "RabbitMQ is ready!"

# Wait for email server to be ready
echo "Waiting for email server at ${EMAIL_IMAP_SERVER}:${EMAIL_IMAP_PORT}..."
while ! nc -z ${EMAIL_IMAP_SERVER} ${EMAIL_IMAP_PORT}; do
  sleep 1
done
echo "Email server is ready!"

echo "Starting email worker..."
exec python main.py
