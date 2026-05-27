import json
import os

# ── MOCK MODE FLAG ──
# True  = use fake diagnosis (no API cost, no key needed)
# False = use real Claude API (requires API key + credits)
MOCK_MODE = True

# ── MOCK DIAGNOSES ──
# Realistic responses for each fault code
MOCK_DIAGNOSES = {
    "P0300": {
        "root_cause": "Random cylinder misfire detected. Low battery voltage (below 12V) combined with high coolant temperature is destabilising the ignition system. Most likely cause: failing alternator unable to maintain charge under thermal load, causing ignition coil voltage drops.",
        "immediate_action": "Reduce engine load immediately. Avoid high RPM driving. Schedule workshop inspection within 48 hours. Do not drive on motorway until voltage issue resolved.",
        "long_term_fix": "Test alternator output voltage at operating temperature. Replace alternator if output below 13.5V. Inspect cooling system for thermostat failure. Replace spark plug set as preventive measure.",
        "safety_risk": "High",
        "confidence": "High"
    },
    "P0115": {
        "root_cause": "Engine coolant temperature sensor circuit fault. Sensor reading outside expected range — either sensor has failed or wiring harness has a fault. ECU cannot accurately determine engine temperature, affecting fuel mixture calculations.",
        "immediate_action": "Monitor engine temperature via dashboard gauge. If gauge shows overheating, stop vehicle immediately. Avoid extended highway driving until sensor is replaced.",
        "long_term_fix": "Replace coolant temperature sensor. Inspect wiring harness for chafing or corrosion at connector. Clear fault code and verify sensor reads within normal range after replacement.",
        "safety_risk": "Medium",
        "confidence": "High"
    },
    "P0562": {
        "root_cause": "System voltage below threshold (measured at 11.2V, normal range 13.5-14.8V). Alternator output insufficient or battery degraded. Low voltage affects multiple electronic systems simultaneously and can cause cascading faults.",
        "immediate_action": "Test battery voltage with engine running. If below 13V, alternator is not charging. Avoid using high-drain accessories (AC, heated seats). Get vehicle to workshop same day.",
        "long_term_fix": "Load test battery — replace if capacity below 70%. Test alternator output and diode pack. Inspect drive belt tension. Check for parasitic drain if battery discharges overnight.",
        "safety_risk": "High",
        "confidence": "High"
    },
    "U0100": {
        "root_cause": "Lost CAN bus communication with Engine Control Module (ECM). This is a network fault indicating either ECM has powered down unexpectedly, CAN bus wiring has a fault, or a termination resistor has failed. Critical — multiple vehicle systems will be affected.",
        "immediate_action": "Stop vehicle safely as soon as possible. Do not attempt to restart without diagnosis. Multiple safety systems may be impaired. Call for recovery if vehicle is not driveable.",
        "long_term_fix": "Inspect CAN bus wiring harness for damage, especially at ECM connector. Check CAN bus termination resistors (should be 60 ohms between CAN-H and CAN-L). Verify ECM power supply and ground connections. May require ECM replacement.",
        "safety_risk": "Critical",
        "confidence": "Medium"
    },
    "P0171": {
        "root_cause": "Fuel system running lean on Bank 1 — air-fuel mixture contains too much air relative to fuel. Most common causes: vacuum leak allowing unmetered air into intake, faulty Mass Air Flow (MAF) sensor reading low, or failing fuel injector on Bank 1.",
        "immediate_action": "Check for audible hissing from engine bay indicating vacuum leak. Avoid aggressive acceleration. Monitor fuel consumption — lean condition increases fuel economy temporarily but damages engine long term.",
        "long_term_fix": "Inspect all vacuum hoses and intake manifold gasket for leaks. Clean or replace MAF sensor. Check fuel pressure. Inspect Bank 1 fuel injectors for blockage or failure.",
        "safety_risk": "Medium",
        "confidence": "High"
    }
}

# ── DEFAULT DIAGNOSIS for unknown fault codes ──
DEFAULT_DIAGNOSIS = {
    "root_cause": "Fault code not in local diagnostic database. Requires live Claude API call for detailed analysis. General recommendation: retrieve full freeze frame data and consult OEM service documentation.",
    "immediate_action": "Log fault for workshop investigation. Monitor vehicle behaviour for additional symptoms. If multiple warning lights active, reduce driving until inspected.",
    "long_term_fix": "Connect to OEM diagnostic tool for manufacturer-specific fault analysis. Review Technical Service Bulletins for this fault code.",
    "safety_risk": "Unknown",
    "confidence": "Low"
}

def build_prompt(fault_data):
    """Build the prompt that would be sent to Claude API in live mode."""
    return f"""You are an expert automotive ECU diagnostic engineer with deep knowledge of OBD-II fault codes and vehicle systems.

A connected vehicle has reported the following fault:

Fault Code: {fault_data.get('dtc_code', 'UNKNOWN')}
Description: {fault_data.get('description', 'UNKNOWN')}
Severity: {fault_data.get('severity', 'UNKNOWN')}

Current Sensor Readings:
- Engine RPM: {fault_data.get('sensor_data', {}).get('RPM', 'N/A')}
- Coolant Temperature: {fault_data.get('sensor_data', {}).get('coolant_temp_c', 'N/A')}°C
- Battery Voltage: {fault_data.get('sensor_data', {}).get('battery_voltage', 'N/A')}V

Provide a structured diagnosis with:
1. Root cause (most likely based on fault code + sensor context)
2. Immediate action required
3. Long-term fix
4. Safety risk level (Low/Medium/High/Critical)
5. Confidence level (Low/Medium/High)

Be concise and use automotive technical language."""

def classify_fault_mock(fault_data):
    """Returns a realistic mock diagnosis without calling any API."""
    dtc_code = fault_data.get('dtc_code', 'UNKNOWN')
    diagnosis = MOCK_DIAGNOSES.get(dtc_code, DEFAULT_DIAGNOSIS).copy()
    diagnosis['mode'] = 'MOCK'
    diagnosis['prompt_used'] = build_prompt(fault_data)
    return diagnosis

def classify_fault_live(fault_data):
    """Calls real Claude API — requires API key and credits."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("AI_API_KEY"))
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": build_prompt(fault_data)
            }]
        )
        
        raw_text = response.content[0].text
        
        return {
            "root_cause": raw_text,
            "immediate_action": "See full diagnosis above",
            "long_term_fix": "See full diagnosis above",
            "safety_risk": fault_data.get('severity', 'Unknown'),
            "confidence": "High",
            "mode": "LIVE",
            "model": "claude-sonnet-4-20250514"
        }
    except Exception as e:
        print(f"Claude API call failed: {str(e)} — falling back to mock")
        return classify_fault_mock(fault_data)

def classify_fault(fault_data):
    """Main entry point — routes to mock or live based on MOCK_MODE flag."""
    if MOCK_MODE:
        print(f"[AI Classifier] MOCK MODE — diagnosing {fault_data.get('dtc_code')}")
        return classify_fault_mock(fault_data)
    else:
        print(f"[AI Classifier] LIVE MODE — calling Claude API for {fault_data.get('dtc_code')}")
        return classify_fault_live(fault_data)