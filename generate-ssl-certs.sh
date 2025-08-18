#!/bin/bash

# SSL Certificate Generation Script for Document Annotation System
# Generates self-signed certificates for local HTTPS development

set -e

echo "🔒 Generating SSL certificates for HTTPS development..."

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Generate private key
echo "🔑 Generating private key..."
openssl genrsa -out ssl/key.pem 2048

# Generate certificate signing request
echo "📝 Generating certificate signing request..."
openssl req -new -key ssl/key.pem -out ssl/cert.csr -subj "/C=US/ST=Local/L=Development/O=Document Annotation/CN=localhost"

# Generate self-signed certificate
echo "📜 Generating self-signed certificate..."
openssl x509 -req -in ssl/cert.csr -signkey ssl/key.pem -out ssl/cert.pem -days 365 \
  -extensions v3_req -extfile <(cat <<EOF
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
)

# Clean up CSR file
rm ssl/cert.csr

# Set proper permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo "✅ SSL certificates generated successfully!"
echo "📁 Certificate files:"
echo "   - Private key: ssl/key.pem"
echo "   - Certificate: ssl/cert.pem"
echo ""
echo "⚠️ These are self-signed certificates for development only."
echo "   Your browser will show a security warning - click 'Advanced' and 'Proceed to localhost'"
echo ""
echo "🚀 You can now start the backend with HTTPS support:"
echo "   ./start-backend.sh 8000 [database_type]"