#!/bin/bash

echo "Importando students.json..."

mongoimport \
  --username admin \
  --password admin123 \
  --authenticationDatabase admin \
  --db school \
  --collection students \
  --file /data/import/students.json \
  --jsonArray