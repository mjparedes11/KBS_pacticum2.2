#!/bin/bash

echo "Importando jsons..."
#active_versions
mongoimport \
  --username admin \
  --password admin123 \
  --authenticationDatabase admin \
  --db edx \
  --collection active_versions \
  --file /data/import/modulestore.active_versions.json

#definitions
mongoimport \
  --username admin \
  --password admin123 \
  --authenticationDatabase admin \
  --db edx \
  --collection definitions \
  --file /data/import/modulestore.definitions.json

#structures
mongoimport \
  --username admin \
  --password admin123 \
  --authenticationDatabase admin \
  --db edx \
  --collection structures \
  --file /data/import/modulestore.structures.json

#structure02
mongoimport \
  --username admin \
  --password admin123 \
  --authenticationDatabase admin \
  --db edx \
  --collection structure02 \
  --file /data/import/modulestore.structure02es.json \
  --jsonArray