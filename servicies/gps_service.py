"""
services/gps_service.py — GPS location handling and geocoding
"""

import streamlit as st
import requests
import os
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import distance as geopy_distance


class GPSService:
    """Handle GPS location, geocoding, and distance calculations"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="sers_emergency_system")
        self.google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    
    def get_browser_location(self) -> Optional[Tuple[float, float]]:
        """
        Attempt to get user's location from browser
        
        Returns:
            (latitude, longitude) or None if not available
        """
        # This uses Streamlit's JavaScript integration
        # The actual location is captured via custom component
        if 'user_latitude' in st.session_state and 'user_longitude' in st.session_state:
            return (st.session_state.user_latitude, st.session_state.user_longitude)
        return None
    
    def render_location_picker(self):
        """Render a location picker widget"""
        st.markdown("""
        <div id="location-picker">
            <button id="get-location" style="
                background: linear-gradient(135deg, #ff416c, #ff4b2b);
                color: white;
                border: none;
                border-radius: 40px;
                padding: 0.6rem 1.5rem;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
            ">
                📍 Share My Current Location
            </button>
            <p id="location-status" style="color: #ccc; margin-top: 8px;"></p>
        </div>
        
        <script>
        const button = document.getElementById('get-location');
        const status = document.getElementById('location-status');
        
        button.addEventListener('click', () => {
            if (navigator.geolocation) {
                status.textContent = 'Getting location...';
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        status.textContent = `Location: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
                        
                        // Send to Streamlit
                        const data = {latitude: lat, longitude: lng};
                        const event = new CustomEvent('streamlit:setComponentValue', {
                            detail: {value: JSON.stringify(data)}
                        });
                        window.dispatchEvent(event);
                    },
                    (error) => {
                        status.textContent = 'Error: ' + error.message;
                    }
                );
            } else {
                status.textContent = 'Geolocation not supported';
            }
        });
        </script>
        """, unsafe_allow_html=True)
    
    def geocode_city(self, city: str) -> Optional[Tuple[float, float]]:
        """
        Convert city name to coordinates
        
        Args:
            city: City name
            
        Returns:
            (latitude, longitude) tuple
        """
        try:
            location = self.geolocator.geocode(f"{city}, Pakistan")
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            print(f"Geocoding error: {e}")
        
        # Fallback coordinates for major cities
        city_coords = {
            "Karachi": (24.8607, 67.0011),
            "Lahore": (31.5204, 74.3587),
            "Islamabad": (33.6844, 73.0479),
            "Rawalpindi": (33.5651, 73.0169),
            "Peshawar": (34.0151, 71.5249),
            "Quetta": (30.1798, 66.9750),
        }
        return city_coords.get(city)
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Calculate distance between two coordinates in kilometers
        
        Args:
            coord1: (lat, lon) of first point
            coord2: (lat, lon) of second point
            
        Returns:
            Distance in kilometers
        """
        return geopy_distance(coord1, coord2).kilometers
    
    def get_nearest_unit(self, user_coords: Tuple[float, float], units: list) -> dict:
        """
        Find the nearest response unit to user's location
        
        Args:
            user_coords: (lat, lon) of user
            units: List of units with coordinates
            
        Returns:
            Nearest unit dictionary
        """
        if not units:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for unit in units:
            unit_coords = self.geocode_city(unit.get('city', ''))
            if unit_coords:
                dist = self.calculate_distance(user_coords, unit_coords)
                if dist < min_distance:
                    min_distance = dist
                    nearest = unit.copy()
                    nearest['distance_km'] = round(dist, 2)
        
        return nearest
    
    def get_address_from_coords(self, lat: float, lon: float) -> Optional[str]:
        """
        Reverse geocode coordinates to address
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Address string or None
        """
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}")
            return location.address if location else None
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None
    
    def get_map_iframe(self, lat: float, lon: float, zoom: int = 15) -> str:
        """
        Generate Google Maps iframe HTML
        
        Args:
            lat: Latitude
            lon: Longitude
            zoom: Zoom level
            
        Returns:
            HTML iframe string
        """
        if self.google_maps_api_key:
            return f"""
            <iframe
                width="100%"
                height="300"
                frameborder="0"
                style="border:0; border-radius: 16px;"
                src="https://www.google.com/maps/embed/v1/place?key={self.google_maps_api_key}&q={lat},{lon}&zoom={zoom}"
                allowfullscreen>
            </iframe>
            """
        else:
            # Fallback to OpenStreetMap
            return f"""
            <iframe
                width="100%"
                height="300"
                frameborder="0"
                style="border:0; border-radius: 16px;"
                src="https://www.openstreetmap.org/export/embed.html?bbox={lon-0.05},{lat-0.05},{lon+0.05},{lat+0.05}&layer=mapnik&marker={lat},{lon}"
                allowfullscreen>
            </iframe>
            """


# Singleton instance
gps_service = GPSService()