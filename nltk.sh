#!/bin/bash

echo "Installing NLTK data..."

python << EOF
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
EOF

echo "NLTK data installed."