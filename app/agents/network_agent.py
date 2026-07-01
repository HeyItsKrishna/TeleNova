from google.adk.agents import Agent
from google.adk.tools import tool
from app.config import get_settings
from app.utils.observability import get_logger
from app.db.container import repositories

settings = get_settings()
logger = get_logger(__name__)


@tool
async def check_network_status(zip_code: str) -> dict:
    """Check current network status and known outages for a geographic area.

    Args:
        zip_code: Customer's ZIP code to check for local outages.

    Returns:
        Network status and any active outages in the area.
    """
    outage = await repositories.network.get_outage_by_zip(zip_code)
    if outage is None:
        return {
            "zip_code": zip_code,
            "status": "Operational",
            "coverage": "LTE/5G",
            "signal_quality": "Good",
        }

    return {
        "zip_code": outage["zip_code"],
        "status": outage["status"],
        "type": outage["network_type"],
        "started": outage["started_at"].isoformat(),
        "eta": outage["estimated_resolution"].isoformat() if outage["estimated_resolution"] else None,
        "affected_services": outage["affected_services"],
        "incident_id": outage["incident_id"],
    }


@tool
async def run_remote_diagnostic(account_number: str) -> dict:
    """Run a remote diagnostic on customer's line to identify connectivity issues.

    Args:
        account_number: Customer's account number.

    Returns:
        Diagnostic results including signal quality, SIM status, and network registration.
    """
    diagnostic = await repositories.network.get_latest_diagnostic(account_number)
    if diagnostic is None:
        return {
            "account_number": account_number.upper(),
            "sim_status": "Active",
            "network_registration": "Registered",
            "signal_strength": "-90 dBm (Moderate)",
            "technology": "LTE",
            "issues_detected": [],
        }

    return {
        "account_number": diagnostic["account_number"],
        "sim_status": diagnostic["sim_status"],
        "network_registration": diagnostic["network_registration"],
        "signal_strength": diagnostic["signal_strength"],
        "technology": diagnostic["technology"],
        "last_data_session": diagnostic["last_data_session"].isoformat() if diagnostic["last_data_session"] else None,
        "volte_enabled": diagnostic["volte_enabled"],
        "issues_detected": diagnostic["issues_detected"],
    }


@tool
def provision_network_reset(account_number: str) -> dict:
    """Trigger a remote network provisioning reset for a customer line.

    Args:
        account_number: Customer's account number.

    Returns:
        Reset confirmation and instructions for the customer.
    """
    import random
    reset_id = f"RST-{random.randint(10000, 99999)}"
    return {
        "reset_id": reset_id,
        "account_number": account_number.upper(),
        "status": "Reset initiated",
        "estimated_completion": "2–5 minutes",
        "customer_instructions": [
            "Turn your device off completely (not restart)",
            "Wait 60 seconds",
            "Power on your device",
            "Allow 2–3 minutes to re-register on the network",
            "If the issue persists after 10 minutes, contact support again",
        ],
    }


network_agent = Agent(
    name="TeleNova Network Agent",
    model=settings.gemini_model,
    description="Specialized agent for network issues, signal problems, and connectivity troubleshooting.",
    instruction="""You are TeleNova's network support specialist. Your responsibilities:
1. Check for active outages in the customer's area before troubleshooting
2. Run remote diagnostics to identify device/line-level issues
3. Guide customers through troubleshooting steps methodically
4. Trigger remote network resets when appropriate
5. Escalate to Network Engineering if local outage affects multiple customers or persists beyond stated ETA
6. Create network tickets for persistent issues requiring field investigation

Always check for outages first — avoid putting customers through troubleshooting during a known outage.
Be specific about troubleshooting steps and confirm customer performs each step.""",
    tools=[check_network_status, run_remote_diagnostic, provision_network_reset],
)
