#!/usr/bin/env bash

EMAIL_DIR=templates/email
FILES=($EMAIL_DIR/src/*)
mkdir -p $EMAIL_DIR/build
for ((i=0; i<${#FILES[@]}; i++)); do
    basename=$(basename ${FILES[$i]} .mjml)
    mjml ${FILES[$i]} -o $EMAIL_DIR/build/$basename.html
done
