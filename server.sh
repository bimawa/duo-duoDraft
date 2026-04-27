#!/bin/bash
PORT=${1:-8080}
DIR=$(dirname "$0")
python3 -m http.server $PORT --directory "$DIR"
