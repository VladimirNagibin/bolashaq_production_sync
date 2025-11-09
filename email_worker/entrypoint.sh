#!/bin/bash

set -e

echo "Starting Email Worker Service..."

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ at ${RABBITMQ_HOST}:${RABBITMQ_PORT}..."
while ! nc -z ${RABBITMQ_HOST} ${RABBITMQ_PORT}; do
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
