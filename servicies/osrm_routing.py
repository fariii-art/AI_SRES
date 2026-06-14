"""
services/osrm_routing.py — Efficient Open Source Routing Machine integration
With caching, connection pooling, and graceful fallbacks
"""

import requests
import polyline
import hashlib
import json
import os
import threading
import time
from typing import Tuple, Optional, Dict, List
from datetime import datetime

# Cache file for routes
CACHE_FILE = "osrm_cache.json"
CACHE_DURATION_HOURS = 24  # Cache routes for 24 hours


class OSRMRouter:
    """
    Efficient OSRM router with:
    - Disk and memory caching
    - Connection pooling
    - Automatic retry with backoff
    - Graceful fallback to Haversine
    """
    
    def __init__(self, use_local_server: bool = False, local_url: str = None):
        # Try multiple OSRM servers for redundancy
        self.servers = []
        
        if use_local_server and local_url:
            self.servers.append(local_url)
        else:
            # Public OSRM servers (multiple for redundancy)
            self.servers = [
                "http://router.project-osrm.org",
                "https://routing.openstreetmap.de",
            ]
        
        self.current_server_index = 0
        self.session = self._create_session()
        self.available = True
        self.cache = self._load_cache()
    
    def _create_session(self) -> requests.Session:
        """Create a session with connection pooling"""
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=5,
            pool_maxsize=10,
            max_retries=1
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update({
            'User-Agent': 'SERS-Emergency-System/1.0',
            'Accept': 'application/json'
        })
        return session
    
    def _load_cache(self) -> Dict:
        """Load cached routes from disk"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    # Remove expired entries
                    now = datetime.now().timestamp()
                    return {k: v for k, v in cache.items() 
                           if v.get('expires', 0) > now}
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(CACHE_FILE, 'w') as f:
                # Limit cache size to 500 entries
                limited_cache = dict(list(self.cache.items())[:500])
                json.dump(limited_cache, f)
        except:
            pass
    
    def _get_cache_key(self, from_coords: Tuple, to_coords: Tuple) -> str:
        """Generate cache key from coordinates"""
        key_str = f"{from_coords[0]:.3f},{from_coords[1]:.3f}|{to_coords[0]:.3f},{to_coords[1]:.3f}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _switch_server(self):
        """Switch to next available server"""
        self.current_server_index = (self.current_server_index + 1) % len(self.servers)
        return self.servers[self.current_server_index]
    
    def get_route(self, from_coords: Tuple[float, float], 
                  to_coords: Tuple[float, float],
                  timeout: int = 5) -> Optional[Dict]:
        """
        Get route with caching and automatic retry
        """
        # Check cache first
        cache_key = self._get_cache_key(from_coords, to_coords)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Check if still valid
            if cached.get('expires', 0) > datetime.now().timestamp():
                return cached.get('data')
        
        from_lon, from_lat = from_coords[1], from_coords[0]
        to_lon, to_lat = to_coords[1], to_coords[0]
        
        # Try each server
        for attempt in range(len(self.servers)):
            server = self.servers[self.current_server_index]
            url = f"{server}/route/v1/driving/{from_lon},{from_lat};{to_lon},{to_lat}"
            params = {
                "overview": "simplified",
                "geometries": "polyline",
                "steps": "false",
                "alternatives": "false"
            }
            
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == "Ok" and data.get("routes"):
                        route = data["routes"][0]
                        geometry_polyline = route.get("geometry", "")
                        geometry = polyline.decode(geometry_polyline) if geometry_polyline else []
                        
                        # Limit geometry points for performance
                        if len(geometry) > 30:
                            step = len(geometry) // 30
                            geometry = geometry[::step]
                        
                        result = {
                            "success": True,
                            "distance_km": round(route["distance"] / 1000, 1),
                            "duration_min": round(route["duration"] / 60, 0),
                            "geometry": geometry,
                            "is_approximate": False,
                            "server": server.split('/')[2] if '//' in server else server
                        }
                        
                        # Cache the result
                        self.cache[cache_key] = {
                            "data": result,
                            "expires": datetime.now().timestamp() + (CACHE_DURATION_HOURS * 3600)
                        }
                        self._save_cache()
                        
                        return result
                else:
                    self._switch_server()
                    
            except (requests.Timeout, requests.ConnectionError):
                self._switch_server()
                continue
        
        # If all servers fail, return None (caller will use fallback)
        return None
    
    def get_route_between_cities(self, from_city: str, to_city: str, 
                                  city_coords: Dict) -> Optional[Dict]:
        """Get route between two cities with efficient caching"""
        from_coords = city_coords.get(from_city)
        to_coords = city_coords.get(to_city)
        
        if not from_coords or not to_coords:
            return None
        
        # Same city - no route needed
        if from_city == to_city:
            return {
                "success": True,
                "distance_km": 0,
                "duration_min": 0,
                "geometry": [],
                "is_approximate": False
            }
        
        return self.get_route(from_coords, to_coords)
    
    def clear_cache(self):
        """Clear the route cache"""
        self.cache = {}
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)


# Singleton instance
osrm_router = OSRMRouter()