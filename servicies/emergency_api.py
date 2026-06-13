"""
services/emergency_api.py — Real 1122 Emergency Service API Integration
"""

import os
import json
import logging
import requests
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Emergency1122API:
    """
    Integration with Pakistan's Rescue 1122 API
    """
    
    def __init__(self):
        self.api_url = os.environ.get("EMERGENCY_API_URL", "https://api.rescue1122.gov.pk/v1")
        self.api_key = os.environ.get("EMERGENCY_API_KEY", "")
        self.enabled = bool(self.api_url and self.api_key)
        
        if self.enabled:
            logger.info("Emergency 1122 API initialized")
        else:
            logger.warning("Emergency 1122 API not configured")
    
    def is_available(self) -> bool:
        """Check if API is configured"""
        return self.enabled
    
    def _get_headers(self) -> Dict:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SERS-Emergency-System/1.0"
        }
    
    def report_emergency(self, incident_data: Dict) -> Dict:
        """
        Report emergency to actual 1122 system
        
        Args:
            incident_data: Dictionary with incident details
            
        Returns:
            API response
        """
        if not self.is_available():
            logger.warning("Cannot report to 1122: API not configured")
            return {"status": "simulated", "message": "API not configured"}
        
        try:
            response = requests.post(
                f"{self.api_url}/emergencies",
                headers=self._get_headers(),
                json=incident_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to report to 1122 API: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_nearby_units(self, lat: float, lon: float, radius_km: float = 10) -> List[Dict]:
        """
        Get nearby response units from 1122 system
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            
        Returns:
            List of nearby units
        """
        if not self.is_available():
            # Return mock data for development
            return self._get_mock_units(lat, lon)
        
        try:
            response = requests.get(
                f"{self.api_url}/units/nearby",
                headers=self._get_headers(),
                params={"lat": lat, "lon": lon, "radius": radius_km},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("units", [])
        except Exception as e:
            logger.error(f"Failed to get nearby units: {e}")
            return []
    
    def get_unit_status(self, unit_id: str) -> Dict:
        """
        Get real-time status of a response unit
        
        Args:
            unit_id: Unit identifier
            
        Returns:
            Unit status dictionary
        """
        if not self.is_available():
            return {"id": unit_id, "status": "available", "location": None}
        
        try:
            response = requests.get(
                f"{self.api_url}/units/{unit_id}",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get unit status: {e}")
            return {"id": unit_id, "status": "unknown"}
    
    def get_incident_stats(self, days: int = 7) -> Dict:
        """
        Get real incident statistics from 1122
        
        Args:
            days: Number of days to look back
            
        Returns:
            Statistics dictionary
        """
        if not self.is_available():
            return self._get_mock_stats()
        
        try:
            response = requests.get(
                f"{self.api_url}/statistics",
                headers=self._get_headers(),
                params={"days": days},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return self._get_mock_stats()
    
    async def report_emergency_async(self, incident_data: Dict) -> Dict:
        """Asynchronously report emergency"""
        if not self.is_available():
            return {"status": "simulated", "message": "API not configured"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_url}/emergencies",
                    headers=self._get_headers(),
                    json=incident_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return await response.json()
            except Exception as e:
                logger.error(f"Async API call failed: {e}")
                return {"status": "error", "message": str(e)}
    
    def _get_mock_units(self, lat: float, lon: float) -> List[Dict]:
        """Generate mock unit data for development"""
        return [
            {
                "id": "FTK-01",
                "type": "Fire",
                "distance_km": 3.2,
                "eta_minutes": 5,
                "status": "available"
            },
            {
                "id": "AMB-01",
                "type": "Medical",
                "distance_km": 4.5,
                "eta_minutes": 7,
                "status": "available"
            },
            {
                "id": "POL-01",
                "type": "Crime",
                "distance_km": 2.8,
                "eta_minutes": 4,
                "status": "dispatched"
            }
        ]
    
    def _get_mock_stats(self) -> Dict:
        """Generate mock statistics for development"""
        return {
            "total_incidents_today": 147,
            "avg_response_time_min": 8.5,
            "incidents_by_type": {
                "Fire": 23,
                "Medical": 67,
                "Traffic": 34,
                "Crime": 18,
                "Other": 5
            },
            "units_active": 156,
            "units_available": 89
        }


class EmergencyWebhook:
    """Handle incoming webhooks from emergency services"""
    
    def __init__(self):
        self.webhook_url = os.environ.get("EMERGENCY_WEBHOOK_URL", "")
    
    def process_webhook(self, payload: Dict) -> Dict:
        """
        Process incoming webhook from emergency service
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processed response
        """
        event_type = payload.get("type", "unknown")
        
        if event_type == "incident_created":
            return self._handle_incident_created(payload)
        elif event_type == "unit_status_changed":
            return self._handle_unit_status_change(payload)
        elif event_type == "incident_resolved":
            return self._handle_incident_resolved(payload)
        else:
            return {"status": "ignored", "message": f"Unknown event: {event_type}"}
    
    def _handle_incident_created(self, payload: Dict) -> Dict:
        """Handle new incident creation webhook"""
        logger.info(f"New incident reported to 1122: {payload.get('incident_id')}")
        return {"status": "processed", "action": "notify_sers"}
    
    def _handle_unit_status_change(self, payload: Dict) -> Dict:
        """Handle unit status change webhook"""
        logger.info(f"Unit {payload.get('unit_id')} status: {payload.get('status')}")
        return {"status": "processed", "action": "update_router"}
    
    def _handle_incident_resolved(self, payload: Dict) -> Dict:
        """Handle incident resolution webhook"""
        logger.info(f"Incident {payload.get('incident_id')} resolved")
        return {"status": "processed", "action": "close_incident"}


# Singleton instance
emergency_api = Emergency1122API()
emergency_webhook = EmergencyWebhook()