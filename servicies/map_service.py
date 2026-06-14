"""
services/map_service.py — Map Service for SERS
"""

import folium
from folium import plugins
from streamlit_folium import st_folium
import streamlit as st
from typing import List, Dict, Optional, Tuple


class MapService:
    """Map service for visualizing incidents and units"""
    
    def __init__(self):
        self.pakistan_center = [30.3753, 69.3451]
        self.default_zoom = 6
        
        # City coordinates for major locations
        self.city_coords = {
            "Karachi": (24.8607, 67.0011),
            "Lahore": (31.5204, 74.3587),
            "Islamabad": (33.6844, 73.0479),
            "Rawalpindi": (33.5651, 73.0169),
            "Peshawar": (34.0151, 71.5249),
            "Quetta": (30.1798, 66.9750),
            "Multan": (30.1575, 71.5249),
            "Faisalabad": (31.4504, 73.1350),
            "Gujranwala": (32.1877, 74.1945),
            "Sialkot": (32.4945, 74.5229),
            "Hyderabad": (25.3960, 68.3578),
            "Sukkur": (27.7244, 68.8428),
        }
    
    def get_city_coordinates(self, city: str) -> Optional[Tuple]:
        """Get coordinates for a city"""
        return self.city_coords.get(city, (30.3753, 69.3451))
    
    def create_base_map(self, center: Optional[Tuple] = None, zoom: int = None):
        """Create a base map"""
        center = center or self.pakistan_center
        zoom = zoom or self.default_zoom
        
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='CartoDB positron',
            control_scale=True
        )
        
        # Add fullscreen button
        plugins.Fullscreen().add_to(m)
        
        return m
    
    def add_incident_marker(self, map_obj, incident: Dict):
        """Add an incident marker to the map"""
        city = incident.get('city', '')
        coords = self.get_city_coordinates(city)
        
        if not coords:
            return
        
        # Color based on priority
        priority = incident.get('priority', 50)
        if priority >= 80:
            color = 'red'
        elif priority >= 60:
            color = 'orange'
        elif priority >= 40:
            color = 'yellow'
        else:
            color = 'green'
        
        popup_text = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <b>🚨 Incident #{incident.get('id', 'N/A')}</b><br>
            <b>Category:</b> {incident.get('category', 'Unknown')}<br>
            <b>Priority:</b> {priority} ({incident.get('level', 'N/A')})<br>
            <b>Location:</b> {city}<br>
            <b>Status:</b> {incident.get('status', 'Pending')}<br>
            <b>Unit:</b> {incident.get('unit', 'Not assigned')}<br>
            <b>ETA:</b> {int(incident.get('eta', 0))} min
        </div>
        """
        
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"#{incident.get('id')}: {incident.get('category')}",
            icon=folium.Icon(color=color, icon='info-sign', prefix='glyphicon')
        ).add_to(map_obj)
    
    def add_unit_marker(self, map_obj, unit: Dict):
        """Add a unit marker to the map"""
        city = unit.get('city', '')
        coords = self.get_city_coordinates(city)
        
        if not coords:
            return
        
        is_available = unit.get('available', True)
        color = 'green' if is_available else 'red'
        status = 'Available' if is_available else 'Deployed'
        
        popup_text = f"""
        <div style="font-family: Arial; min-width: 150px;">
            <b>🚒 {unit.get('id', 'N/A')}</b><br>
            <b>Type:</b> {unit.get('type', 'Unknown')}<br>
            <b>Location:</b> {city}<br>
            <b>Status:</b> {status}
        </div>
        """
        
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"{unit.get('id')}: {unit.get('type')} ({status})",
            icon=folium.Icon(color=color, icon='home', prefix='glyphicon')
        ).add_to(map_obj)
    
    def create_full_dashboard_map(self, incidents: List[Dict], units: List[Dict] = None,
                                   show_heatmap: bool = True, show_clusters: bool = False):
        """Create a complete dashboard map"""
        m = self.create_base_map()
        
        # Add incident markers
        for inc in incidents[:100]:
            self.add_incident_marker(m, inc)
        
        # Add unit markers
        if units:
            for unit in units[:50]:
                self.add_unit_marker(m, unit)
        
        return m
    
    def create_unit_deployment_map(self, unit_id: str, destination: str, route_data: Dict = None):
        """Create a map showing unit deployment route"""
        try:
            from ai.router import Router
            router = Router()
            
            unit = next((u for u in router.units if u['id'] == unit_id), None)
            if not unit or not destination:
                return None
            
            m = self.create_base_map()
            
            # Add unit marker
            self.add_unit_marker(m, unit)
            
            # Add destination marker
            dest_incident = {
                'city': destination, 
                'category': 'Emergency', 
                'priority': 85, 
                'level': 'High', 
                'status': 'Pending', 
                'id': 'DEST',
                'unit': unit_id,
                'eta': 0
            }
            self.add_incident_marker(m, dest_incident)
            
            return m
        except:
            return None
    
    def display_map(self, map_obj, height: int = 500):
        """Display the map in Streamlit"""
        if map_obj:
            st_folium(map_obj, width="100%", height=height, returned_objects=[])
        else:
            st.info("No map data available")


# Singleton instance
map_service = MapService()
