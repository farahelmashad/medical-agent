import json
import sys
import os

# Make sure Python can find the app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.sheets import generate_slots

with open("data/doctors.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Generating slots for all doctors...")
generate_slots(data["doctors"], days_ahead=14)
print("Done! Check your Google Sheet slots tab.")