"""
services/map_service.py — Simplified Map Service for SERS
"""

import folium
from folium import plugins
import streamlit as st

# Try to import streamlit-folium with fallback
try:
    from streamlit_folium import st_folium
    ST_FOLIUM_AVAILABLE = True
except ImportError:
    ST_FOLIUM_AVAILABLE = False


class MapService:
    def __init__(self):
        self.pakistan_center = [30.3753, 69.3451]
        self.default_zoom = 6
        
        self.city_coords = {
            "Karachi": (24.8607, 67.0011),
            "Lahore": (31.5204, 74.3587),
            "Islamabad": (33.6844, 73.0479),
            "Rawalpindi": (33.5651, 73.0169),
            "Peshawar": (34.0151, 71.5249),
            "Quetta": (30.1798, 66.9750),
            "Multan": (30.1575, 71.5249),
            "Faisalabad": (31.4504, 73.1350),
        }
    
    def get_city_coordinates(self, city):
        return self.city_coords.get(city, (30.3753, 69.3451))
    
    def create_base_map(self, center=None, zoom=None):
        center = center or self.pakistan_center
        zoom = zoom or self.default_zoom
        
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='CartoDB positron'
        )
        return m
    
    def add_incident_marker(self, map_obj, incident):
        city = incident.get('city', '')
        coords = self.get_city_coordinates(city)
        if not coords:
            return
        
        priority = incident.get('priority', 50)
        if priority >= 80:
            color = 'red'
        elif priority >= 60:
            color = 'orange'
        else:
            color = 'blue'
        
        folium.Marker(
            location=coords,
            popup=f"Incident #{incident.get('id')}: {incident.get('category')}",
            icon=folium.Icon(color=color)
        ).add_to(map_obj)
    
    def add_unit_marker(self, map_obj, unit):
        city = unit.get('city', '')
        coords = self.get_city_coordinates(city)
        if not coords:
            return
        
        is_available = unit.get('available', True)
        color = 'green' if is_available else 'red'
        
        folium.Marker(
            location=coords,
            popup=f"Unit {unit.get('id')}: {unit.get('type')}",
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(map_obj)
    
    def create_full_dashboard_map(self, incidents, units=None, show_heatmap=True, show_clusters=False):
        m = self.create_base_map()
        
        for inc in incidents[:100]:
            self.add_incident_marker(m, inc)
        
        if units:
            for unit in units[:50]:
                self.add_unit_marker(m, unit)
        
        return m
    
    def create_unit_deployment_map(self, unit_id, destination, route_data=None):
        m = self.create_base_map()
        return m
    
    def display_map(self, map_obj, height=500):
        if map_obj and ST_FOLIUM_AVAILABLE:
            st_folium(map_obj, width="100%", height=height, returned_objects=[])
        elif map_obj:
            # Fallback: just show HTML
            map_html = map_obj._repr_html_()
            st.components.v1.html(map_html, height=height)
        else:
            st.info("No map data available")


map_service = MapService()