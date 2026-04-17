import json
import random
from backend.ai.pipeline import generate_ai_response
from backend.database import SessionLocal, ViolationReport

def fetch_aa_sandbox_data(phone_number: str):
    """
    Mocks the Setu Account Aggregator Sandbox API payload.
    In a real environment, this invokes a Consent Flow using JWS signatures
    and returns encrypted JSON strings from the FIPs (Banks/Insurers).
    """
    
    # We simulate fetching a bank statement that contains an unauthorized deduction
    mock_bank_statement = {
        "account_type": "SAVINGS",
        "bank_name": "HDFC Bank",
        "location": "Maharashtra",
        "transactions": [
            {"date": "2026-03-01", "amount": -15000, "narrative": "Rent Payment"},
            {"date": "2026-03-05", "amount": -436, "narrative": "AUTO-DEBIT PMJJBY LIFE INS"},
            {"date": "2026-03-10", "amount": -1200, "narrative": "ULIP BUNDLE DEBIT - STAR HEALTH"}
        ],
        "registered_mandates": []
    }
    return mock_bank_statement

def process_aa_consent(phone_number: str, user_id: int):
    """
    1. Fetches the AA data.
    2. Runs Groq + Pinecone inference to detect violations.
    3. Logs to db if violations exist.
    """
    data = fetch_aa_sandbox_data(phone_number)
    
    # Convert structured data to a descriptive text block for the LLM
    text_payload = f"Bank: {data['bank_name']}\nLocation: {data['location']}\nTransactions: {json.dumps(data['transactions'])}"
    
    query = f"Analyze the following user bank transactions fetched from the Account Aggregator: {text_payload}. Does this show evidence of Forced Bundling or Ghost Insurance deductions (like PMJJBY or ULIPs without explicit mandates)? Reference IRDAI master circulars."
    
    # Use existing AI pipeline to get the reasoning
    ai_response = generate_ai_response(query, "irdai")
    
    # Simple heuristic to determine if a violation was found based on the mock data
    # (Since we explicitly mocked a PMJJBY and ULIP debit)
    if "PMJJBY" in text_payload or "ULIP" in text_payload:
        db = SessionLocal()
        try:
            report = ViolationReport(
                user_id=user_id,
                bank_name=data['bank_name'],
                violation_type="Ghost Insurance / Forced Bundling",
                location_state=data['location'],
                severity="High"
            )
            db.add(report)
            db.commit()
        except Exception as e:
            print(f"Failed to log violation: {e}")
        finally:
            db.close()
            
    return {
        "status": "success",
        "analysis": ai_response,
        "raw_data_fetched": data
    }
