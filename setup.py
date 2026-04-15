import json
import sys
import os
#trial file , will remove later 
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.sheets import generate_slots

with open("data/doctors.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    
generate_slots(data["doctors"], days_ahead=14)
