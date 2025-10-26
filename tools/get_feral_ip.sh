#!/bin/bash
# Get the IP address of your FeralHosting server

echo "Getting FeralHosting server IP..."
echo ""

# Replace with your actual server hostname from .env
# Format: servername.feralhosting.com
SERVER="geryon.feralhosting.com"

IP=$(dig +short $SERVER | head -n 1)

if [ -z "$IP" ]; then
    echo "❌ Could not resolve IP for $SERVER"
    echo "Please check your FERAL_SERVER in .env"
else
    echo "✅ FeralHosting Server: $SERVER"
    echo "✅ IP Address: $IP"
    echo ""
    echo "📋 Use this IP in Cloudflare DNS settings:"
    echo "   Type: A"
    echo "   Name: @"
    echo "   Content: $IP"
    echo "   Proxy: ON (orange cloud)"
fi
