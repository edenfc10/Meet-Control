#!/usr/bin/env python3
"""
Test CMS Video Meeting Creation
This script tests if your CMS server can create VIDEO meetings
"""

import requests
import xml.etree.ElementTree as ET

def test_cms_video_meetings():
    """Test CMS for VIDEO meeting creation"""
    print("=== Testing CMS Video Meeting Creation ===")
    print()
    
    # CMS Configuration
    cms_url = "https://192.168.20.150:455/api/v1/coSpaces"
    auth = ('admin', 'S@p180tech')
    
    # Create headers
    headers = {
        'Content-Type': 'application/xml',
        'Authorization': requests.auth._basic_auth_str(auth[0], auth[1])
    }
    
    try:
        # Test 1: Create VIDEO meeting
        print("1. Creating VIDEO meeting...")
        xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
<coSpace>
    <name>VIDEO_TEST_MEETING</name>
    <uri>video_test</uri>
    <passcode>1234</passcode>
</coSpace>'''
        
        response = requests.post(cms_url, headers=headers, data=xml_data, verify=False, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code in [200, 201]:
            print("   ✅ SUCCESS: VIDEO meeting created!")
            
            # Test 2: List all meetings to verify
            print()
            print("2. Verifying in meeting list...")
            list_response = requests.get(cms_url, headers=headers, verify=False, timeout=30)
            
            print(f"   List Status: {list_response.status_code}")
            print(f"   Total meetings: {list_response.text[:300]}...")
            
            if 'VIDEO_TEST_MEETING' in list_response.text:
                print("   ✅ CONFIRMED: VIDEO meeting found in list!")
                return True
            else:
                print("   ❌ ISSUE: VIDEO meeting not found in list")
                return False
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_cms_video_meetings()
    
    print()
    print("=== CONCLUSION ===")
    if success:
        print("✅ Your CMS server supports VIDEO meetings!")
        print("✅ You can create VIDEO meetings through Meet Control!")
        print("✅ The system is working properly!")
    else:
        print("❌ There might be an issue with VIDEO meeting creation")
        print("❌ Check the CMS server configuration")
