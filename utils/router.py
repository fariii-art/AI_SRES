"""
ai/router.py — Unit dispatch router
"""

import math


class Router:
    """Emergency unit dispatcher"""
    
    def __init__(self):
        # City coordinates
        self.cities = {
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
        
        # Response units
        self.units = [
            # Fire units
            {"id": "FIRE-01", "type": "Fire", "city": "Karachi", "available": True},
            {"id": "FIRE-02", "type": "Fire", "city": "Lahore", "available": True},
            {"id": "FIRE-03", "type": "Fire", "city": "Islamabad", "available": True},
            {"id": "FIRE-04", "type": "Fire", "city": "Peshawar", "available": True},
            {"id": "FIRE-05", "type": "Fire", "city": "Quetta", "available": True},
            {"id": "FIRE-06", "type": "Fire", "city": "Rawalpindi", "available": True},
            {"id": "FIRE-07", "type": "Fire", "city": "Multan", "available": True},
            
            # Medical units
            {"id": "MED-01", "type": "Medical", "city": "Karachi", "available": True},
            {"id": "MED-02", "type": "Medical", "city": "Lahore", "available": True},
            {"id": "MED-03", "type": "Medical", "city": "Islamabad", "available": True},
            {"id": "MED-04", "type": "Medical", "city": "Rawalpindi", "available": True},
            {"id": "MED-05", "type": "Medical", "city": "Peshawar", "available": True},
            {"id": "MED-06", "type": "Medical", "city": "Multan", "available": True},
            {"id": "MED-07", "type": "Medical", "city": "Faisalabad", "available": True},
            
            # Police units
            {"id": "POL-01", "type": "Crime", "city": "Karachi", "available": True},
            {"id": "POL-02", "type": "Crime", "city": "Lahore", "available": True},
            {"id": "POL-03", "type": "Crime", "city": "Islamabad", "available": True},
            {"id": "POL-04", "type": "Crime", "city": "Rawalpindi", "available": True},
            {"id": "POL-05", "type": "Crime", "city": "Peshawar", "available": True},
            
            # Traffic units
            {"id": "TRF-01", "type": "Accident", "city": "Karachi", "available": True},
            {"id": "TRF-02", "type": "Accident", "city": "Lahore", "available": True},
            {"id": "TRF-03", "type": "Accident", "city": "Islamabad", "available": True},
            {"id": "TRF-04", "type": "Accident", "city": "Rawalpindi", "available": True},
            
            # Flood rescue
            {"id": "FLOOD-01", "type": "Flood", "city": "Sukkur", "available": True},
            {"id": "FLOOD-02", "type": "Flood", "city": "Karachi", "available": True},
            {"id": "FLOOD-03", "type": "Flood", "city": "Lahore", "available": True},
            {"id": "FLOOD-04", "type": "Flood", "city": "Multan", "available": True},
            
            # Earthquake rescue
            {"id": "EQ-01", "type": "Earthquake", "city": "Islamabad", "available": True},
            {"id": "EQ-02", "type": "Earthquake", "city": "Peshawar", "available": True},
            {"id": "EQ-03", "type": "Earthquake", "city": "Quetta", "available": True},
        ]
        
        self._unit_index = {u["id"]: u for u in self.units}
        self._precompute_distances()
    
    def _haversine(self, coord1, coord2):
        """Calculate distance between two points"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    def _precompute_distances(self):
        """Precompute all city distances"""
        self.dist_cache = {}
        cities = list(self.cities.keys())
        for c1 in cities:
            for c2 in cities:
                if c1 == c2:
                    self.dist_cache[(c1, c2)] = 0
                elif (c1, c2) not in self.dist_cache:
                    d = self._haversine(self.cities[c1], self.cities[c2])
                    self.dist_cache[(c1, c2)] = d
                    self.dist_cache[(c2, c1)] = d
    
    def get_distance(self, city1: str, city2: str) -> float:
        """Get distance between cities"""
        return self.dist_cache.get((city1, city2), 300.0)
    
    def find_best_unit(self, incident_city: str, incident_type: str):
        """Find nearest available unit"""
        if incident_city not in self.cities:
            return "BACKUP-01", 30, ["Backup"], "N/A"
        
        best = None
        best_dist = float('inf')
        
        # First try exact type match
        for u in self.units:
            if u["type"] == incident_type and u["available"]:
                d = self.get_distance(incident_city, u["city"])
                if d < best_dist:
                    best_dist = d
                    best = u
        
        # Fallback to any available unit
        if best is None:
            for u in self.units:
                if u["available"]:
                    d = self.get_distance(incident_city, u["city"])
                    if d < best_dist:
                        best_dist = d
                        best = u
        
        if best is None:
            return "NO-UNIT", 60, ["N/A"], "N/A"
        
        # ETA in minutes (60 km/h average speed)
        eta = max(round(best_dist / 60.0 * 60, 0), 5.0)
        route = [best["city"], incident_city] if best["city"] != incident_city else [incident_city]
        
        return best["id"], eta, route, best["city"]
    
    def mark_dispatched(self, unit_id: str):
        """Mark unit as dispatched/unavailable"""
        if unit_id in self._unit_index:
            self._unit_index[unit_id]["available"] = False
    
    def mark_available(self, unit_id: str):
        """Mark unit as available"""
        if unit_id in self._unit_index:
            self._unit_index[unit_id]["available"] = True
    
    def get_unit_status(self) -> list:
        """Get all units with status"""
        return [
            {"id": u["id"], "type": u["type"], "city": u["city"], "available": u["available"]}
            for u in self.units
        ]
    
    def get_cities(self) -> list:
        """Get list of all cities"""
        return list(self.cities.keys())