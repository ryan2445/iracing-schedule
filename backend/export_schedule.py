import json
import os
from app.schedule import schedule_engine

def export():
    # Construct the payload
    # Let's map series to include their pre-compiled rules directly so they are unified
    series_with_rules = []
    for sr in schedule_engine.series_rules:
        series_item = dict(sr["series"])
        series_item["rule"] = sr["rule"]
        series_with_rules.append(series_item)

    payload = {
        "series": series_with_rules,
        "tracks": schedule_engine.tracks_list,
        "categories": schedule_engine.categories_list,
        "licenses": schedule_engine.licenses_list,
    }

    # Determine paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.abspath(os.path.join(current_dir, "..", "frontend", "src", "lib", "schedule.json"))
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully exported schedule data to {output_path}")

if __name__ == "__main__":
    export()
