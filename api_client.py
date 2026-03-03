"""BoTTube API client for video uploads."""
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import json


class BoTTubeClient:
    """Client for BoTTube API interactions."""
    
    def __init__(self, config: dict):
        bottube_config = config.get('bottube', {})
        self.api_url = bottube_config.get('api_url', '')
        self.api_key = bottube_config.get('api_key', '')
        
        if not self.api_url:
            raise ValueError("BoTTube API URL not configured")
        if not self.api_key:
            raise ValueError("BoTTube API key not configured")
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a video to BoTTube.
        
        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of tags
        
        Returns:
            Tuple of (success, video_id, error_message)
        """
        video_file = Path(video_path)
        
        if not video_file.exists():
            return False, None, f"Video file not found: {video_path}"
        
        try:
            with open(video_file, 'rb') as f:
                files = {
                    'video': (video_file.name, f, 'video/mp4')
                }
                
                data = {
                    'title': title,
                    'description': description,
                    'tags': json.dumps(tags),
                }
                
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Accept': 'application/json',
                }
                
                response = requests.post(
                    self.api_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=300  # 5 minute timeout for uploads
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    result = response.json()
                    video_id = result.get('id') or result.get('video_id') or result.get('data', {}).get('id')
                    return True, video_id, None
                else:
                    error_msg = f"Upload failed: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message') or error_data.get('error') or error_msg
                    except:
                        error_msg = f"{error_msg} - {response.text[:200]}"
                    return False, None, error_msg
                    
        except requests.exceptions.Timeout:
            return False, None, "Upload timed out"
        except requests.exceptions.ConnectionError as e:
            return False, None, f"Connection error: {str(e)}"
        except Exception as e:
            return False, None, f"Upload error: {str(e)}"
    
    def check_connection(self) -> Tuple[bool, str]:
        """Check if the API is reachable."""
        try:
            # Try a simple GET request to the base URL
            base_url = self.api_url.rsplit('/upload', 1)[0]
            response = requests.get(
                base_url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=10
            )
            
            if response.status_code in (200, 401, 403, 404):
                return True, "API is reachable"
            else:
                return False, f"API returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to API"
        except requests.exceptions.Timeout:
            return False, "API connection timed out"
        except Exception as e:
            return False, f"Connection check failed: {str(e)}"
