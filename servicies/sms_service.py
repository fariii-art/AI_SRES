"""
services/sms_service.py — SMS and WhatsApp integration using Twilio
"""

import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import Optional

logger = logging.getLogger(__name__)


class SMSService:
    """Handle SMS and WhatsApp notifications"""
    
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "+14155238886")
        self.sms_number = os.environ.get("TWILIO_SMS_NUMBER", "")
        
        self.client = None
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
    
    def is_available(self) -> bool:
        """Check if SMS service is configured"""
        return self.client is not None
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS notification
        
        Args:
            to_number: Recipient phone number (with country code)
            message: Message content
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            logger.warning("SMS service not configured")
            return False
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.sms_number,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number}, SID: {message_obj.sid}")
            return True
        except TwilioRestException as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def send_whatsapp(self, to_number: str, message: str) -> bool:
        """
        Send WhatsApp notification
        
        Args:
            to_number: Recipient phone number (with country code)
            message: Message content
            
        Returns:
            bool: True if sent successfully
        """
        if not self.is_available():
            logger.warning("WhatsApp service not configured")
            return False
        
        # Format WhatsApp number (Twilio expects 'whatsapp:' prefix)
        to_whatsapp = f"whatsapp:{to_number}"
        from_whatsapp = f"whatsapp:{self.whatsapp_number}"
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=from_whatsapp,
                to=to_whatsapp
            )
            logger.info(f"WhatsApp message sent to {to_number}, SID: {message_obj.sid}")
            return True
        except TwilioRestException as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False
    
    def send_emergency_alert(self, to_number: str, incident: dict) -> bool:
        """
        Send formatted emergency alert
        
        Args:
            to_number: Recipient phone number
            incident: Incident dictionary with details
            
        Returns:
            bool: True if sent successfully
        """
        message = f"""
🚨 EMERGENCY ALERT - SERS System

Type: {incident.get('category', 'Unknown')}
Priority: {incident.get('level', 'Unknown')} ({incident.get('priority', 0)}/100)
Location: {incident.get('city', 'Unknown')}
Status: {incident.get('status', 'Pending')}

Unit: {incident.get('unit', 'Assigning...')}
ETA: {int(incident.get('eta', 0))} minutes

Please stay safe. Help is on the way.
        """.strip()
        
        # Try WhatsApp first, fall back to SMS
        if self.send_whatsapp(to_number, message):
            return True
        else:
            return self.send_sms(to_number, message)
    
    def send_unit_dispatched(self, to_number: str, unit_id: str, eta: float, route: str) -> bool:
        """
        Send unit dispatched notification
        
        Args:
            to_number: Recipient phone number
            unit_id: Unit identifier
            eta: Estimated arrival time in minutes
            route: Route description
            
        Returns:
            bool: True if sent successfully
        """
        message = f"""
✅ UNIT DISPATCHED

Unit: {unit_id}
ETA: {int(eta)} minutes
Route: {route}

Track your emergency at: https://sers.pakistan.gov/track
        """.strip()
        
        return self.send_whatsapp(to_number, message) or self.send_sms(to_number, message)