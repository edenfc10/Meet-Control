#!/usr/bin/env python3
"""
CMS Configuration Script for Ubuntu Server
This script sets up the CMS admin credentials and configuration
"""

import os

def setup_cms_config():
    """Setup CMS configuration for Ubuntu server"""
    
    # CMS Configuration
    cms_config = {
        "CMS_URL": "https://192.168.1.24:445",
        "CMS_USERNAME": "admin",
        "CMS_PASSWORD": "S@p180tech",
        "CMS_TIMEOUT": "30",
        "CMS_VERIFY_SSL": "false"
    }
    
    # Write to .env file
    env_file = ".env"
    
    # Read existing .env if exists
    existing_env = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value
    
    # Update with CMS config
    existing_env.update(cms_config)
    
    # Write back to .env
    with open(env_file, 'w') as f:
        for key, value in existing_env.items():
            f.write(f"{key}={value}\n")
    
    print("✅ CMS Configuration updated successfully!")
    print(f"📋 Configuration:")
    for key, value in cms_config.items():
        print(f"   {key}={value}")
    
    print(f"\n📁 Updated file: {env_file}")
    print("🚀 Ready to start the system!")

if __name__ == "__main__":
    setup_cms_config()
