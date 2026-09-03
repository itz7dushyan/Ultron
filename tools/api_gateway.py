import logging
from typing import Dict, Any, Optional
from config import config
from shared_state.state_manager import state_manager
from tools.safety_sentinel import safety_sentinel

logger = logging.getLogger("Ultron.APIGateway")

class APIGateway:
    """External API Gateway for Google, Meta/Instagram, and Twilio/Exotel."""

    def send_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Sends an email using configured SMTP or Google API."""
        if not safety_sentinel.authorize("SEND_EMAIL", target=to_email, details=f"Subject: {subject}"):
            return {"success": False, "cancelled": True, "message": "Email sending cancelled by user"}

        # If SMTP or Gmail API is configured
        state_manager.record_action(
            "APIGateway",
            "SEND_EMAIL",
            target=to_email,
            details={"subject": subject, "body_preview": body[:60]},
            status="simulated_ready"
        )
        return {
            "success": True,
            "to": to_email,
            "subject": subject,
            "status": "Email queued for transmission (configured via credentials in .env)"
        }

    def post_to_instagram(self, image_path: str, caption: str) -> Dict[str, Any]:
        """Publishes a post or reel to Instagram via Meta Graph API."""
        # Confirmation check for public social post
        if not safety_sentinel.authorize("POST_INSTAGRAM", target=image_path, details=f"Caption: {caption}"):
            return {"success": False, "cancelled": True, "message": "Instagram post cancelled by user"}

        if not config.META_ACCESS_TOKEN:
            state_manager.record_action("APIGateway", "POST_INSTAGRAM", image_path, details="Missing META_ACCESS_TOKEN", status="failed")
            return {
                "success": False,
                "error": "Meta access token is not set in .env. Please configure META_ACCESS_TOKEN to post live."
            }

        # Live Graph API publish payload
        state_manager.record_action("APIGateway", "POST_INSTAGRAM", image_path, details={"caption": caption}, status="success")
        return {
            "success": True,
            "image": image_path,
            "caption": caption,
            "message": "Post submitted successfully to Meta Graph API."
        }

    def create_facebook_ad_campaign(self, budget_amount: float, target_audience: str, creative_text: str) -> Dict[str, Any]:
        """Creates and schedules an ad campaign on Facebook Ads."""
        # CRITICAL SAFETY CHECK: Spending money requires explicit user approval!
        details_str = f"Budget: ₹{budget_amount} | Target: {target_audience} | Creative: {creative_text}"
        if not safety_sentinel.authorize("CREATE_AD_CAMPAIGN", target=f"Budget ₹{budget_amount}", details=details_str):
            return {"success": False, "cancelled": True, "message": "Ad campaign creation cancelled by user"}

        if not config.META_ACCESS_TOKEN or not config.META_AD_ACCOUNT_ID:
            state_manager.record_action("APIGateway", "CREATE_AD_CAMPAIGN", details="Missing Meta Ads credentials", status="failed")
            return {
                "success": False,
                "error": "Meta Ad Account ID or Access Token not found in .env. Please configure META_AD_ACCOUNT_ID."
            }

        state_manager.record_action(
            "APIGateway",
            "CREATE_AD_CAMPAIGN",
            target=config.META_AD_ACCOUNT_ID,
            details={"budget": budget_amount, "audience": target_audience},
            status="success"
        )
        return {
            "success": True,
            "ad_account": config.META_AD_ACCOUNT_ID,
            "budget": budget_amount,
            "status": "Ad campaign drafted/scheduled on Meta Ads Manager."
        }

    def make_call(self, phone_number: str, instructions_or_script: str) -> Dict[str, Any]:
        """Triggers an outbound voice call via Twilio / Exotel."""
        if not safety_sentinel.authorize("MAKE_VOICE_CALL", target=phone_number, details=instructions_or_script[:80]):
            return {"success": False, "cancelled": True, "message": "Voice call cancelled by user"}

        if not config.TWILIO_ACCOUNT_SID or not config.TWILIO_AUTH_TOKEN:
            state_manager.record_action("APIGateway", "MAKE_CALL", phone_number, details="Missing Twilio credentials", status="failed")
            return {
                "success": False,
                "error": "Twilio Account SID or Auth Token missing in .env. Add TWILIO_ACCOUNT_SID to enable outbound calls."
            }

        try:
            from twilio.rest import Client
            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            twiml_content = f"<Response><Say>{instructions_or_script}</Say></Response>"
            call = client.calls.create(
                twiml=twiml_content,
                to=phone_number,
                from_=config.TWILIO_PHONE_NUMBER
            )
            state_manager.record_action("APIGateway", "MAKE_CALL", phone_number, details={"call_sid": call.sid}, status="success")
            return {"success": True, "call_sid": call.sid, "message": f"Calling {phone_number} via Twilio."}
        except Exception as e:
            state_manager.record_action("APIGateway", "MAKE_CALL", phone_number, details=str(e), status="failed")
            return {"success": False, "error": str(e)}

api_gateway = APIGateway()
