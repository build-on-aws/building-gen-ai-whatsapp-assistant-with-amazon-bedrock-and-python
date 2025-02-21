# Improved session management component
# The original implementation had session management logic mixed in the handler
# This implementation provides better separation of concerns and more robust handling

import time
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """Data class for session information"""
    session_id: str
    is_new: bool
    session_time: int

class SessionManager:
    """Handles conversation session management with improved logic"""
    
    def __init__(self, table_session_active, session_timeout: int = 240):
        self.table = table_session_active
        self.session_timeout = session_timeout
    
    def get_or_create_session(self, phone_number: str) -> SessionInfo:
        """Get existing session or create new one with improved error handling
        
        Args:
            phone_number: The user's phone number
            
        Returns:
            SessionInfo object containing session details
        """
        try:
            # Try to get existing session
            session_data = self._query_session(phone_number)
            now = int(time.time())
            
            if session_data is None:
                # No existing session, create new one
                return self._create_new_session(phone_number, now)
            
            # Check if existing session has timed out
            time_diff = now - session_data["session_time"]
            if time_diff > self.session_timeout:
                return self._create_new_session(phone_number, now)
            
            # Return existing valid session
            session_id = f"{phone_number}_{session_data['session_time']}"
            return SessionInfo(
                session_id=session_id,
                is_new=False,
                session_time=session_data["session_time"]
            )
            
        except Exception as e:
            logger.error(f"Error managing session for {phone_number}: {str(e)}")
            # Fallback to new session if error occurs
            now = int(time.time())
            return self._create_new_session(phone_number, now)
    
    def _query_session(self, phone_number: str) -> Optional[dict]:
        """Query existing session with error handling"""
        try:
            response = self.table.get_item(
                Key={"phone_number": phone_number}
            )
            return response.get("Item")
        except Exception as e:
            logger.error(f"Error querying session: {str(e)}")
            return None
    
    def _create_new_session(self, phone_number: str, timestamp: int) -> SessionInfo:
        """Create new session with error handling"""
        try:
            new_session = {
                "phone_number": phone_number,
                "session_time": timestamp
            }
            self.table.put_item(Item=new_session)
            
            session_id = f"{phone_number}_{timestamp}"
            return SessionInfo(
                session_id=session_id,
                is_new=True,
                session_time=timestamp
            )
        except Exception as e:
            logger.error(f"Error creating new session: {str(e)}")
            raise