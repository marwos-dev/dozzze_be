#!/bin/bash

echo "Esperando a Redis..."
while ! nc -z redis 6379; do
  sleep 1
done

echo "Iniciando worker de Celery..."