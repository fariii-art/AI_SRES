"""
services/map_service.py — PyDeck map visualization for emergency incidents
"""

import pydeck as pdk
import pandas as pd
import streamlit as st
from typing import List, Dict, Optional


class MapService:
    """Handle map visualizations using PyDeck"""
    
    def __init__(self):
        # Pakistani city coordinates
        self.city_coords = {
            "Karachi": (24.8607, 67.0011),
            "Lahore": (31.5204, 74.3587),
            "Islamabad": (33.6844, 73.0479),
            "Rawalpindi": (33.5651, 73.0169),
            "Peshawar": (34.0151, 71.5249),
            "Quetta": (30.1798, 66.9750),
            "Multan": (30.1575, 71.5249),
            "Faisalabad": (31.4504, 73.1350),
            "Sialkot": (32.4945, 74.5229),
            "Hyderabad": (25.3960, 68.3578),
            "Sukkur": (27.7244, 68.8428),
            "Mardan": (34.1989, 72.0497),
            "Abbottabad": (34.1688, 73.2215),
        }
        
        # Color mapping for incident types
        self.color_map = {
            "Fire": [255, 0, 0],           # Red
            "Accident": [255, 165, 0],     # Orange
            "Medical": [0, 255, 0],        # Green
            "Crime": [128, 0, 128],        # Purple
            "Flood": [0, 0, 255],          # Blue
            "Earthquake": [255, 255, 0],   # Yellow
            "Infrastructure": [255, 192, 203], # Pink
        }
    
    def create_incident_map(self, incidents: List[Dict], center: Optional[tuple] = None):
        """
        Create a PyDeck map with incident markers
        
        Args:
            incidents: List of incident dictionaries with lat, lon, category
            center: (lat, lon) tuple for map center
            
        Returns:
            pydeck.Deck object
        """
        if not incidents:
            return None
        
        # Prepare data
        data = []
        for inc in incidents:
            lat, lon = self.get_coordinates(inc.get('city', ''))
            if lat and lon:
                data.append({
                    'lat': lat,
                    'lon': lon,
                    'category': inc.get('category', 'Unknown'),
                    'priority': inc.get('priority', 0),
                    'level': inc.get('level', 'Low'),
                    'status': inc.get('status', 'Pending'),
                    'id': inc.get('id', 0),
                    'color': self.color_map.get(inc.get('category', ''), [128, 128, 128])
                })
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        # Create scatterplot layer
        scatter_layer = pdk.Layer(
            'ScatterplotLayer',
            data=df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=500,  # meters
            pickable=True,
            auto_highlight=True,
            radius_scale=1,
            radius_min_pixels=10,
            radius_max_pixels=50,
        )
        
        # Create text layer for labels
        text_layer = pdk.Layer(
            'TextLayer',
            data=df,
            get_position='[lon, lat]',
            get_text='category',
            get_color=[255, 255, 255],
            get_size=12,
            get_alignment_baseline='"bottom"',
        )
        
        # Set view state
        if center:
            view_state = pdk.ViewState(
                latitude=center[0],
                longitude=center[1],
                zoom=10,
                pitch=0,
            )
        elif data:
            center_lat = sum(d['lat'] for d in data) / len(data)
            center_lon = sum(d['lon'] for d in data) / len(data)
            view_state = pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=8,
                pitch=0,
            )
        else:
            view_state = pdk.ViewState(
                latitude=33.6844,
                longitude=73.0479,
                zoom=8,
                pitch=0,
            )
        
        # Create deck
        deck = pdk.Deck(
            layers=[scatter_layer, text_layer],
            initial_view_state=view_state,
            tooltip={
                "html": "<b>Incident #{id}</b><br/>Category: {category}<br/>Priority: {priority} ({level})<br/>Status: {status}",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            },
            map_style='mapbox://styles/mapbox/dark-v10',
        )
        
        return deck
    
    def create_route_map(self, from_city: str, to_city: str, incidents: List[Dict] = None):
        """
        Create a map showing dispatch route between cities
        
        Args:
            from_city: Source city
            to_city: Destination city
            incidents: Additional incidents to display
            
        Returns:
            pydeck.Deck object
        """
        from_coord = self.get_coordinates(from_city)
        to_coord = self.get_coordinates(to_city)
        
        if not from_coord or not to_coord:
            return None
        
        # Create line data
        line_data = pd.DataFrame({
            'lat': [from_coord[0], to_coord[0]],
            'lon': [from_coord[1], to_coord[1]],
        })
        
        # Line layer
        line_layer = pdk.Layer(
            'LineLayer',
            data=line_data,
            get_source_position='[lon, lat]',
            get_target_position='[lon, lat]',
            get_color=[255, 75, 43],
            get_width=5,
            pickable=True,
        )
        
        # Points layer
        points_data = pd.DataFrame([
            {'lat': from_coord[0], 'lon': from_coord[1], 'type': 'Unit', 'city': from_city},
            {'lat': to_coord[0], 'lon': to_coord[1], 'type': 'Incident', 'city': to_city}
        ])
        
        point_layer = pdk.Layer(
            'ScatterplotLayer',
            data=points_data,
            get_position='[lon, lat]',
            get_color=[0, 255, 0] if points_data['type'] == 'Unit' else [255, 0, 0],
            get_radius=500,
            pickable=True,
        )
        
        # Text layer
        text_layer = pdk.Layer(
            'TextLayer',
            data=points_data,
            get_position='[lon, lat]',
            get_text='type',
            get_color=[255, 255, 255],
            get_size=14,
        )
        
        # Center map between the two points
        center_lat = (from_coord[0] + to_coord[0]) / 2
        center_lon = (from_coord[1] + to_coord[1]) / 2
        zoom = self._calculate_zoom(from_coord, to_coord)
        
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=zoom,
            pitch=30,
        )
        
        deck = pdk.Deck(
            layers=[line_layer, point_layer, text_layer],
            initial_view_state=view_state,
            tooltip={"html": "<b>{city}</b><br/>{type}", "style": {"color": "white"}},
            map_style='mapbox://styles/mapbox/light-v10',
        )
        
        return deck
    
    def get_coordinates(self, city: str) -> Optional[tuple]:
        """Get coordinates for a city"""
        return self.city_coords.get(city)
    
    def _calculate_zoom(self, coord1: tuple, coord2: tuple) -> float:
        """Calculate appropriate zoom level based on distance"""
        from geopy.distance import geodesic
        
        distance = geodesic(coord1, coord2).kilometers
        
        if distance < 10:
            return 12
        elif distance < 50:
            return 10
        elif distance < 200:
            return 8
        elif distance < 500:
            return 7
        else:
            return 6
    
    def display_map(self, deck: pdk.Deck):
        """Display the map in Streamlit"""
        if deck:
            st.pydeck_chart(deck)
        else:
            st.info("No map data available")


# Singleton instance
map_service = MapService()