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
    
    @staticmethod
    def check_connection(ip_address: str, port: int, username: str, password: str, timeout: int = 10) -> bool:
        """בודק חיבור ל-CMS לפני שמירה ב-DB. מחזיר True אם השרת מגיב תקין."""
        import urllib3
        urllib3.disable_warnings()
        base_url = f"https://{ip_address}:{port}/api/v1"
        try:
            resp = requests.get(
                f"{base_url}/coSpaces",
                auth=(username, password),
                verify=False,
                timeout=timeout,
            )
            return resp.status_code == 200
        except Exception:
            return False

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
        form_data = {"name": name}
        if uri:
            form_data["uri"] = uri
        if passcode:
            form_data["passcode"] = passcode

        url = f"{self.base_url}/coSpaces"
        response = self.session.post(url, data=form_data, timeout=self.timeout)
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
        url = f"{self.base_url}/coSpaces/{cospace_id}"
        response = self.session.put(url, data={"passcode": passcode}, timeout=self.timeout)
        if response.status_code == 200:
            return {"status": "updated"}
        else:
            raise Exception(f"Failed to update CoSpace passcode: {response.status_code} - {response.text}")
    
    def get_cospace_by_uri(self, uri: str) -> Optional[Dict]:
        """Find a CoSpace by its URI (meeting number)"""
        cospaces = self.list_cospaces()
        for cs in cospaces:
            cs_id = cs.get("id") or cs.get("@id")
            if not cs_id:
                continue
            try:
                details = self.get_cospace_details(cs_id)
                if str(details.get("uri", "")).strip() == str(uri).strip():
                    if "id" not in details:
                        details["id"] = cs_id
                    return details
            except Exception:
                continue
        return None
    
    def delete_cospace_by_uri(self, uri: str) -> bool:
        """Delete a CoSpace by its URI. Returns False if not found (already gone)."""
        cospace = self.get_cospace_by_uri(uri)
        if not cospace:
            return False
        cospace_id = cospace.get("id") or cospace.get("@id")
        if not cospace_id:
            return False
        return self.delete_cospace(cospace_id)
    
    def update_cospace_passcode_by_uri(self, uri: str, passcode: str) -> Dict:
        """Update CoSpace passcode by its URI"""
        cospace = self.get_cospace_by_uri(uri)
        if not cospace:
            raise Exception(f"CoSpace with uri '{uri}' not found")
        cospace_id = cospace.get("id") or cospace.get("@id")
        if not cospace_id:
            raise Exception(f"CoSpace with uri '{uri}' has no id")
        return self.update_cospace_passcode(cospace_id, passcode)

    
    
    def get_cospace_details(self, cospace_id: str) -> Dict:
        """Get CoSpace details"""
        response = self.cms_get(f'coSpaces/{cospace_id}')
        if response.status_code == 200:
            return self._parse_xml_response(response.content)
        else:
            raise Exception(f"Failed to get CoSpace details: {response.status_code} - {response.text}")
    
    def list_cospaces(self, full_details: bool = False) -> List[Dict]:
        """List all CoSpaces. If full_details=True, fetches each CoSpace individually to include uri/name/passcode."""
        response = self.cms_get('coSpaces')
        if response.status_code != 200:
            raise Exception(f"Failed to list CoSpaces: {response.status_code} - {response.text}")
        root = ET.fromstring(response.content)
        cospaces = []
        for cospace in root.findall('coSpace'):
            cs = self._xml_element_to_dict(cospace)
            if full_details:
                cs_id = cs.get("id") or cs.get("@id")
                if cs_id:
                    try:
                        details = self.get_cospace_details(cs_id)
                        details["id"] = cs_id
                        cs = details
                    except Exception:
                        pass
            cospaces.append(cs)
        return cospaces
    
    # Call Management
    def get_active_calls(self) -> List[Dict]:
        """Get all active calls"""
        response = self.cms_get('calls')
        if response.status_code == 200:
            root = ET.fromstring(response.content)
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
            return self._parse_xml_response(response.content)
        else:
            raise Exception(f"Failed to get call details: {response.status_code} - {response.text}")
    
    def get_call_participants(self, call_id: str) -> List[Dict]:
        """Get call participants"""
        response = self.cms_get(f'calls/{call_id}')
        if response.status_code == 200:
            root = ET.fromstring(response.content)
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
    def _parse_xml_response(self, xml_text) -> Dict:
        """Parse XML response to dictionary"""
        try:
            content = xml_text if isinstance(xml_text, bytes) else xml_text.encode('utf-8')
            root = ET.fromstring(content)
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


class CMSFactory:
    """
    Factory שמחזיר CMS מחובר לפי access_level.
    מנסה שרתים מה-DB לפי priority (1=ראשי, 2=גיבוי...).
    אם אף שרת DB לא זמין — נופל חזרה ל-env vars.
    """

    @staticmethod
    def get(session, cms_type: str) -> 'CMS':
        """
        מחזיר CMS מחובר עבור cms_type ("audio"/"video").
        מנסה שרתים מה-DB לפי priority עולה.
        זורק HTTPException 503 אם אף שרת לא זמין.
        """
        from app.models.server import Server
        from fastapi import HTTPException

        servers = (
            session.query(Server)
            .filter(Server.accessLevel == cms_type)
            .order_by(Server.priority.asc())
            .limit(8)
            .all()
        )

        for server in servers:
            reachable = CMS.check_connection(
                server.ip_address, server.port, server.username, server.password
            )
            if reachable:
                logger.info(
                    "CMSFactory: using server %s (%s:%s) priority=%s for %s",
                    server.server_name, server.ip_address, server.port,
                    server.priority, cms_type,
                )
                server.is_active = True
                try:
                    session.commit()
                except Exception:
                    session.rollback()
                return CMS(
                    base_url=f"https://{server.ip_address}:{server.port}",
                    username=server.username,
                    password=server.password,
                )
            else:
                if server.is_active:
                    server.is_active = False
                    try:
                        session.commit()
                    except Exception:
                        session.rollback()

        if servers:
            logger.error("CMSFactory: all %s DB servers unreachable", cms_type)
            raise HTTPException(
                status_code=503,
                detail=f"All {cms_type} CMS servers are unreachable.",
            )

        logger.warning("CMSFactory: no DB servers for %s, falling back to env vars", cms_type)
        return CMS(cms_type=cms_type)
