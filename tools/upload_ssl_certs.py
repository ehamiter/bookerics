#!/usr/bin/env python3
"""Upload SSL certificates to FeralHosting for bookerics.com."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bookerics.database import upload_file_via_sftp


async def upload_certs():
    """Upload SSL certificate files to FeralHosting."""
    
    # Paths to your local certificate files (update these paths)
    local_cert = Path.home() / "Downloads" / "certificate.crt"
    local_key = Path.home() / "Downloads" / "private.key"
    
    # Remote paths on FeralHosting
    remote_cert = "/media/sdc1/eddielomax/www/bookerics.com/https.crt"
    remote_key = "/media/sdc1/eddielomax/www/bookerics.com/https.key"
    
    print("Uploading SSL certificates to FeralHosting...")
    
    if not local_cert.exists():
        print(f"❌ Certificate file not found: {local_cert}")
        print("Please download your certificate files and update the paths in this script.")
        return
    
    if not local_key.exists():
        print(f"❌ Private key file not found: {local_key}")
        print("Please download your private key file and update the paths in this script.")
        return
    
    try:
        await upload_file_via_sftp(str(local_cert), remote_cert)
        print(f"✅ Uploaded certificate to {remote_cert}")
        
        await upload_file_via_sftp(str(local_key), remote_key)
        print(f"✅ Uploaded private key to {remote_key}")
        
        print("\n🎉 SSL certificates uploaded successfully!")
        print("⏰ FeralHosting will automatically apply the configuration within 5 minutes.")
        print("🔒 Your site will then be accessible at https://bookerics.com")
        
    except Exception as e:
        print(f"❌ Error uploading certificates: {e}")


if __name__ == "__main__":
    asyncio.run(upload_certs())
