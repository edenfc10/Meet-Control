import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)

class CMS:
    """Cisco Meeting Server API Client"""
    
    def __init__(self, base_url: str = None, username: str = None, password: str = None, cms_type: str = None):
        """
        Initialize CMS client

        Args:
            base_url: Base URL for CMS API (e.g., "https://cms.example.com:8443")
                     If None, uses CMS_AUDIO_URL or CMS_VIDEO_URL based on cms_type
            username: CMS admin username. If None, uses CMS_USERNAME environment variable
            password: CMS admin password. If None, uses CMS_PASSWORD environment variable
            cms_type: Type of CMS server - "audio" or "video". If provided, uses CMS_AUDIO_URL or CMS_VIDEO_URL
        """
        api_prefix = os.getenv('CMS_API_PREFIX', '/api/v1').rstrip('/')
        if base_url:
            self.base_url = base_url.rstrip('/') + api_prefix
        elif cms_type:
            if cms_type.lower() == 'audio':
                self.base_url = os.getenv('CMS_AUDIO_URL', '').rstrip('/') + api_prefix
            elif cms_type.lower() == 'video':
                self.base_url = os.getenv('CMS_VIDEO_URL', '').rstrip('/') + api_prefix
            else:
                self.base_url = os.getenv('CMS_URL', '').rstrip('/') + api_prefix
        else:
            self.base_url = os.getenv('CMS_URL', '').rstrip('/') + api_prefix

        self.username = username or os.getenv('CMS_USERNAME', '')
        self.password = password or os.getenv('CMS_PASSWORD', '')
        self.timeout = int(os.getenv('CMS_TIMEOUT', '30'))
        self.verify_ssl = os.getenv('CMS_VERIFY_SSL', 'false').lower() == 'true'
        
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.verify = self.verify_ssl
        
        if not self.verify_ssl:
            requests.packages.urllib3.disable_warnings()
        
        logger.info(f"CMS Client initialized for {self.base_url}")
    
    # HTTP Methods
    def cms_get(self, endpoint: str) -> requests.Response:
        """Make GET request to CMS API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            logger.info(f"GET {url} - Status: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {url} failed: {e}")
            raise
    
    def cms_post(self, endpoint: str, data: Optional[Dict] = None, xml: Optional[str] = None) -> requests.Response:
        """Make POST request to CMS API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if xml:
            headers['Content-Type'] = 'application/xml'
            response = self.session.post(url, data=xml.encode('utf-8'), headers=headers, timeout=self.timeout)
        else:
            headers['Content-Type'] = 'application/json'
            response = self.session.post(url, json=data, headers=headers, timeout=self.timeout)
        
        logger.info(f"POST {url} - Status: {response.status_code}")
        return response
    
    def cms_put(self, endpoint: str, data: Optional[Dict] = None, xml: Optional[str] = None) -> requests.Response:
        """Make PUT request to CMS API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if xml:
            headers['Content-Type'] = 'application/xml'
            response = self.session.put(url, data=xml.encode('utf-8'), headers=headers, timeout=self.timeout)
        else:
            headers['Content-Type'] = 'application/json'
            response = self.session.put(url, json=data, headers=headers, timeout=self.timeout)
        
        logger.info(f"PUT {url} - Status: {response.status_code}")
        return response
    
    def cms_delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request to CMS API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.delete(url, timeout=self.timeout)
            logger.info(f"DELETE {url} - Status: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE {url} failed: {e}")
            raise
    
    # CoSpace Management
    def create_cospace(self, name: str, uri: Optional[str] = None, passcode: Optional[str] = None) -> Dict:
        """Create a new CoSpace"""
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <coSpace>
            <name>{name}</name>
            {'<uri>' + uri + '</uri>' if uri else ''}
            {'<passcode>' + passcode + '</passcode>' if passcode else ''}
        </coSpace>'''
        
        response = self.cms_post('coSpaces', xml=xml_data)
        if response.status_code in (200, 201):
            return self._parse_xml_response(response.text) if response.text.strip() else {"status": "created"}
        else:
            raise Exception(f"Failed to create CoSpace: {response.status_code} - {response.text}")
    
    def delete_cospace(self, cospace_id: str) -> bool:
        """Delete a CoSpace"""
        response = self.cms_delete(f'coSpaces/{cospace_id}')
        return response.status_code == 204
    
    def update_cospace_passcode(self, cospace_id: str, passcode: str) -> Dict:
        """Update CoSpace passcode"""
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <coSpace>
            <passcode>{passcode}</passcode>
        </coSpace>'''
        
        response = self.cms_put(f'coSpaces/{cospace_id}', xml=xml_data)
        if response.status_code == 200:
            return self._parse_xml_response(response.text)
        else:
            raise Exception(f"Failed to update CoSpace passcode: {response.status_code} - {response.text}")
    
    def get_cospace_details(self, cospace_id: str) -> Dict:
        """Get CoSpace details"""
        response = self.cms_get(f'coSpaces/{cospace_id}')
        if response.status_code == 200:
            return self._parse_xml_response(response.text)
        else:
            raise Exception(f"Failed to get CoSpace details: {response.status_code} - {response.text}")
    
    def list_cospaces(self) -> List[Dict]:
        """List all CoSpaces"""
        response = self.cms_get('coSpaces')
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            cospaces = []
            for cospace in root.findall('coSpace'):
                cospaces.append(self._xml_element_to_dict(cospace))
            return cospaces
        else:
            raise Exception(f"Failed to list CoSpaces: {response.status_code} - {response.text}")
    
    # Call Management
    def get_active_calls(self) -> List[Dict]:
        """Get all active calls"""
        response = self.cms_get('calls')
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            calls = []
            for call in root.findall('call'):
                calls.append(self._xml_element_to_dict(call))
            return calls
        else:
            raise Exception(f"Failed to get active calls: {response.status_code} - {response.text}")
    
    def get_call_details(self, call_id: str) -> Dict:
        """Get call details"""
        response = self.cms_get(f'calls/{call_id}')
        if response.status_code == 200:
            return self._parse_xml_response(response.text)
        else:
            raise Exception(f"Failed to get call details: {response.status_code} - {response.text}")
    
    def get_call_participants(self, call_id: str) -> List[Dict]:
        """Get call participants"""
        response = self.cms_get(f'calls/{call_id}')
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            participants = []
            for participant in root.findall('.//participant'):
                participants.append(self._xml_element_to_dict(participant))
            return participants
        else:
            raise Exception(f"Failed to get call participants: {response.status_code} - {response.text}")
    
    # Participant Management
    def get_participant_leg_id(self, call_id: str, participant_name: str) -> Optional[str]:
        """Get participant leg ID by name"""
        participants = self.get_call_participants(call_id)
        for participant in participants:
            if participant.get('name') == participant_name:
                return participant.get('legId')
        return None
    
    def mute_participant(self, call_id: str, participant_name: str, mute: bool = True) -> bool:
        """Mute or unmute a participant"""
        leg_id = self.get_participant_leg_id(call_id, participant_name)
        if not leg_id:
            raise Exception(f"Participant {participant_name} not found in call {call_id}")
        
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <participant>
            <mute>{"true" if mute else "false"}</mute>
        </participant>'''
        
        response = self.cms_put(f'calls/{call_id}/participants/{leg_id}', xml=xml_data)
        return response.status_code == 200
    
    def mute_participant_by_leg_id(self, call_id: str, leg_id: str, mute: bool = True) -> bool:
        """Mute or unmute a participant directly by leg_id"""
        xml_data = f'<participant><mute>{"true" if mute else "false"}</mute></participant>'
        response = self.cms_put(f'calls/{call_id}/participants/{leg_id}', xml=xml_data)
        return response.status_code == 200

    def kick_participant_by_leg_id(self, call_id: str, leg_id: str) -> bool:
        """Kick a participant directly by leg_id"""
        response = self.cms_delete(f'calls/{call_id}/participants/{leg_id}')
        return response.status_code == 204

    def kick_participant(self, call_id: str, participant_name: str) -> bool:
        """Kick a participant from call"""
        leg_id = self.get_participant_leg_id(call_id, participant_name)
        if not leg_id:
            raise Exception(f"Participant {participant_name} not found in call {call_id}")
        
        response = self.cms_delete(f'calls/{call_id}/participants/{leg_id}')
        return response.status_code == 204
    
    def set_participant_layout(self, call_id: str, participant_name: str, layout: str) -> bool:
        """Set participant layout"""
        leg_id = self.get_participant_leg_id(call_id, participant_name)
        if not leg_id:
            raise Exception(f"Participant {participant_name} not found in call {call_id}")
        
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <participant>
            <layout>{layout}</layout>
        </participant>'''
        
        response = self.cms_put(f'calls/{call_id}/participants/{leg_id}', xml=xml_data)
        return response.status_code == 200
    
    def get_participant_ids(self, call_id: str) -> List[str]:
        """Get all participant IDs in a call"""
        participants = self.get_call_participants(call_id)
        return [p.get('legId') for p in participants if p.get('legId')]
    
    def get_participants_by_meeting_number(self, m_number: str) -> List[Dict]:
        """Find the active call matching m_number and return its participants"""
        calls = self.get_active_calls()
        for call in calls:
            name = call.get('name', '')
            if str(name) == str(m_number):
                call_id = call.get('id') or call.get('callId') or call.get('@id')
                if call_id:
                    return self.get_call_participants(call_id)
        return []

    # Utility Methods
    def _parse_xml_response(self, xml_text: str) -> Dict:
        """Parse XML response to dictionary"""
        try:
            root = ET.fromstring(xml_text)
            return self._xml_element_to_dict(root)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
            raise Exception(f"Invalid XML response: {e}")
    
    def _xml_element_to_dict(self, element: ET.Element) -> Dict:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            else:
                result['text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_element_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def test_connection(self) -> bool:
        """Test connection to CMS"""
        try:
            response = self.cms_get('system/status')
            return response.status_code == 200
        except Exception as e:
            logger.error(f"CMS connection test failed: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Get CMS system information"""
        response = self.cms_get('system')
        if response.status_code == 200:
            return self._parse_xml_response(response.text)
        else:
            raise Exception(f"Failed to get system info: {response.status_code} - {response.text}")
    
    @classmethod
    def create_default(cls) -> 'CMS':
        """Create CMS client with default configuration"""
        return cls()
    
    @classmethod
    def create_from_env(cls) -> 'CMS':
        """Create CMS client from environment variables"""
        return cls(
            base_url=os.getenv('CMS_URL'),
            username=os.getenv('CMS_USERNAME'),
            password=os.getenv('CMS_PASSWORD')
        )
    
    def get_config_summary(self) -> Dict:
        """Get current configuration summary"""
        return {
            "base_url": self.base_url,
            "username": self.username,
            "timeout": self.timeout,
            "verify_ssl": self.verify_ssl,
            "connected": self.test_connection()
        }
