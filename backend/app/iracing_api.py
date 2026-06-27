import base64
import hashlib
import logging
from typing import Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class IRacingClient:
    def __init__(self) -> None:
        self.base_url = "https://members-ng.iracing.com"
        self.client = httpx.Client(follow_redirects=True)
        self.is_authenticated = False
        
    def _encode_password(self, password: str, email: str) -> str:
        """
        iRacing password hashing scheme:
        SHA256(password + email.lower()) and then base64 encoded.
        """
        combined = f"{password}{email.lower()}"
        hashed = hashlib.sha256(combined.encode("utf-8")).digest()
        return base64.b64encode(hashed).decode("utf-8")
        
    def login(self) -> bool:
        if not settings.iracing_username or not settings.iracing_password:
            logger.info("iRacing credentials not provided. Using Mock Mode.")
            return False
            
        try:
            encoded_password = self._encode_password(
                settings.iracing_password, 
                settings.iracing_username
            )
            
            payload = {
                "email": settings.iracing_username,
                "password": encoded_password
            }
            
            logger.info(f"Attempting to login to iRacing API as {settings.iracing_username}...")
            response = self.client.post(f"{self.base_url}/auth", json=payload, timeout=10.0)
            
            if response.status_code == 200:
                self.is_authenticated = True
                logger.info("Successfully authenticated with iRacing API!")
                return True
            else:
                logger.warning(f"iRacing auth failed with status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error authenticating with iRacing API: {e}")
            return False

    def _get_data(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """
        Fetch data from the iRacing members-ng API.
        The iRacing API often returns a JSON object containing a 'link' to a CDN.
        We must then fetch from that CDN link.
        """
        if not self.is_authenticated:
            if not self.login():
                raise Exception("Not authenticated with iRacing API.")
                
        try:
            response = self.client.get(f"{self.base_url}{endpoint}", params=params, timeout=15.0)
            
            # If we get unauthorized, try to login once more
            if response.status_code == 401:
                logger.info("Session expired, re-authenticating...")
                if self.login():
                    response = self.client.get(f"{self.base_url}{endpoint}", params=params, timeout=15.0)
                else:
                    raise Exception("Failed to re-authenticate with iRacing API.")
                    
            if response.status_code != 200:
                raise Exception(f"Failed to fetch data from {endpoint}. Status: {response.status_code}")
                
            data = response.json()
            
            # Check if the API response is a redirect to a CDN link
            if isinstance(data, dict) and "link" in data:
                cdn_url = data["link"]
                logger.info(f"Fetching actual payload from CDN link: {cdn_url[:60]}...")
                cdn_response = httpx.get(cdn_url, timeout=15.0)
                if cdn_response.status_code == 200:
                    return cdn_response.json()
                else:
                    raise Exception(f"Failed to fetch from CDN link: {cdn_response.status_code}")
                    
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data from iRacing endpoint {endpoint}: {e}")
            raise e

    def get_series_list(self) -> list[dict[str, Any]]:
        """
        Fetch all available series.
        Endpoint: /data/series/get
        """
        try:
            return self._get_data("/data/series/get")
        except Exception:
            logger.warning("Falling back to mock series list")
            return []

    def get_seasons(self) -> list[dict[str, Any]]:
        """
        Fetch active seasons/schedules.
        Endpoint: /data/series/seasons
        """
        try:
            return self._get_data("/data/series/seasons")
        except Exception:
            logger.warning("Falling back to mock seasons")
            return []

iracing_client = IRacingClient()
