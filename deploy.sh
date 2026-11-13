#!/bin/bash
set -e

cd ./frontend && bash ./deploy.sh && cd ..

echo "iracing-schedule complete!"
