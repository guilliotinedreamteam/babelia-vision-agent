"""
Babelia Crawler

Fetches images from the Library of Babel's Babelia image archives.
"""

import requests
import time
import random
import logging
from typing import Dict, Optional, Any
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)


class BabeliaCrawler:
    """Fetches images from Babelia image archives"""
    
    BASE_URL = "https://babelia.libraryofbabel.info"
    
    def __init__(self, rate_limit: float = 2.0, sampling_mode: str = 'random'):
        """
        Initialize crawler
        
        Args:
            rate_limit: Seconds between requests
            sampling_mode: 'random' or 'sequential'
        """
        self.rate_limit = rate_limit
        self.sampling_mode = sampling_mode
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BabeliaVisionAgent/1.0 (Research Project)'
        })
        
        # For sequential mode
        self.current_hex = 0
        
        logger.info(f"Crawler initialized (mode: {sampling_mode}, rate_limit: {rate_limit}s)")
    
    def fetch_next_image(self) -> Optional[Dict[str, Any]]:
        """
        Fetch next image from Babelia
        
        Returns:
            Dictionary with 'image' (PIL Image) and 'coordinates' (dict)
        """
        # Respect rate limit
        self._respect_rate_limit()
        
        # Generate coordinates
        coords = self._generate_coordinates()
        
        # Construct URL
        url = self._build_url(coords)
        
        try:
            # Fetch image
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Load image
            image = Image.open(BytesIO(response.content))
            
            logger.debug(f"Fetched image from {coords['hex_name'][:12]}...")
            
            return {
                'image': image,
                'coordinates': coords,
                'url': url
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch image: {e}")
            return None
    
    def _generate_coordinates(self) -> Dict[str, str]:
        """
        Generate Babelia coordinates
        
        Format: {hex_name}-w{wall}-s{shelf}-v{volume}-p{page}
        """
        if self.sampling_mode == 'random':
            # Random sampling
            hex_name = self._generate_random_hex()
            wall = random.choice(['n', 'e', 's', 'w'])
            shelf = str(random.randint(1, 5))
            volume = str(random.randint(1, 32))
            page = f"{random.randint(1, 640):03d}"
        else:
            # Sequential sampling
            hex_name = f"{self.current_hex:040x}"
            wall = 'n'
            shelf = '1'
            volume = '1'
            page = '001'
            self.current_hex += 1
        
        return {
            'hex_name': hex_name,
            'wall': wall,
            'shelf': shelf,
            'volume': volume,
            'page': page
        }
    
    def _generate_random_hex(self, length: int = 40) -> str:
        """
        Generate random hexadecimal string
        
        Args:
            length: Length of hex string (default 40 for Babelia)
        """
        return ''.join(random.choices('0123456789abcdef', k=length))
    
    def _build_url(self, coords: Dict[str, str]) -> str:
        """
        Build Babelia image URL from coordinates
        
        Args:
            coords: Coordinate dictionary
        """
        # Format: imagebrowse.cgi?{hex}-w{wall}-s{shelf}-v{volume}-p{page}
        path = (
            f"{coords['hex_name']}-"
            f"w{coords['wall']}-"
            f"s{coords['shelf']}-"
            f"v{coords['volume']}-"
            f"p{coords['page']}"
        )
        
        return f"{self.BASE_URL}/imagebrowse.cgi?{path}"
    
    def _respect_rate_limit(self):
        """Ensure rate limit is respected"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def fetch_specific_image(self, coordinates: Dict[str, str]) -> Optional[Image.Image]:
        """
        Fetch a specific image by coordinates
        
        Args:
            coordinates: Babelia coordinates dictionary
        """
        self._respect_rate_limit()
        
        url = self._build_url(coordinates)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            logger.error(f"Failed to fetch specific image: {e}")
            return None