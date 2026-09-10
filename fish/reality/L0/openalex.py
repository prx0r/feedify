"""
openalex Adapter
"""

import json
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional
from ..event_store import GenericEvent, EventType, Evidence


class OpenalexAdapter:
    """openalex adapter"""
    
    def __init__(self):
        pass
    
    def fetch(self) -> List[Dict]:
        return []
    
    def to_events(self, data: List[Dict]) -> List[GenericEvent]:
        return []


# TODO: Implement openalex adapter
