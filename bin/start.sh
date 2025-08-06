#!/bin/bash

if [ "$DJANGO_ENV" = "production" ]; then
  exec ./bin/production.sh
else
  exec ./bin/dev.sh
fi
