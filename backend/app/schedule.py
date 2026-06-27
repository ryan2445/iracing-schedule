import os
import re
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any
import pypdf

logger = logging.getLogger(__name__)

PDF_PATH = "/Users/ryan/Sites/iracing-race-tracker/iracing_season_3_schedule.pdf"

categories_map: dict[str, str] = {
    "OVAL": "Oval",
    "SPORTS CAR": "Sports Car",
    "FORMULA CAR": "Formula Car",
    "DIRT OVAL": "Dirt Oval",
    "DIRT ROAD": "Dirt Road"
}

license_groups_map: dict[str, dict[str, Any]] = {
    "Rookie": {"name": "Rookie", "id": 1},
    "Class D": {"name": "Class D", "id": 2},
    "Class C": {"name": "Class C", "id": 3},
    "Class B": {"name": "Class B", "id": 4},
    "Class A": {"name": "Class A", "id": 5},
    "Pro": {"name": "Pro", "id": 6}
}

class ScheduleEngine:
    def __init__(self):
        self.series_list: list[dict[str, Any]] = []
        self.tracks_list: list[dict[str, Any]] = []
        self.categories_list: list[str] = []
        self.licenses_list: list[dict[str, Any]] = []
        self.load_schedule()

    def load_schedule(self) -> None:
        """
        Loads schedule directly from the PDF.
        """
        self.parse_pdf_schedule()

    def parse_pdf_schedule(self) -> None:
        """
        Parses the season PDF schedule and saves to JSON cache.
        """
        logger.info(f"Parsing schedule PDF at {PDF_PATH}...")
        if not os.path.exists(PDF_PATH):
            logger.error(f"PDF file not found at {PDF_PATH}!")
            return

        try:
            reader = pypdf.PdfReader(PDF_PATH)
            all_text_lines = []
            
            # Skip first 5 pages of Table of Contents
            for i in range(5, len(reader.pages)):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    all_text_lines.extend(page_text.split("\n"))

            license_indices = []
            for idx, line in enumerate(all_text_lines):
                if "-->" in line:
                    license_indices.append(idx)

            # Map line numbers to categories sequentially
            line_to_category = {}
            current_cat = "Oval"
            for idx, line in enumerate(all_text_lines):
                cleaned = line.strip().upper()
                if cleaned in categories_map:
                    current_cat = categories_map[cleaned]
                line_to_category[idx] = current_cat

            series_temp: list[dict[str, Any]] = []
            
            for index_in_list, idx in enumerate(license_indices):
                # Boundary list going backward
                candidates: list[str] = []
                for back_idx in range(idx - 1, max(0, idx - 15), -1):
                    line = all_text_lines[back_idx].strip()
                    if not line or line.isdigit():
                        break
                    
                    cleaned = line.upper()
                    if cleaned in categories_map or "CLASS SERIES" in line or "CLASS D" in line or "CLASS C" in line or "CLASS B" in line or "CLASS A" in line or "ROOKIE" in line:
                        break
                    if line.startswith("Week ") or line.startswith("Races ") or line.startswith("Min entries ") or line.startswith("Penalty ") or line.startswith("No incident ") or line.startswith("DQ at "):
                        break
                    if line.startswith("("):
                        break
                    if "laps" in line or "mins" in line or "tire sets" in line or "scrutiny" in line or "start" in line or "cautions" in line:
                        break
                    if "°F" in line or "°C" in line or "Rain chance" in line or "Cautions" in line:
                        break
                    
                    candidates.insert(0, line)
                    
                if not candidates:
                    continue
                    
                title = candidates[0]
                cars_str = ", ".join(candidates[1:]) if len(candidates) > 1 else title
                
                # Format clean title
                display_title = re.sub(r'\s*-\s*\d{4}\s+Season\s+\d+\s*(Fixed)?', '', title)
                display_title = re.sub(r'\s*-\s*\d{4}\s+Season\s*(Fixed)?', '', display_title)
                display_title = re.sub(r'\s*-\s+Season\s+\d+\s*(Fixed)?', '', display_title)
                display_title = display_title.strip()
                
                # Determine license group
                lic_line = all_text_lines[idx].strip()
                lic_group_name = "Rookie"
                lic_group_id = 1
                for group_key, group_info in license_groups_map.items():
                    if lic_line.startswith(group_key):
                        lic_group_name = str(group_info["name"])
                        lic_group_id = int(group_info["id"])
                        break
                        
                # Determine fixed setup
                fixed_setup = "fixed" in display_title.lower() or "fixed" in title.lower() or "fixed" in lic_line.lower()
                
                # Find weekly schedule details
                next_idx = license_indices[index_in_list + 1] if index_in_list + 1 < len(license_indices) else len(all_text_lines)
                weeks = []
                week_re = re.compile(r"^Week\s+(\d+)\s+\(([^)]+)\)\s*(.*)$")
                for j in range(idx, next_idx):
                    line = all_text_lines[j].strip()
                    match = week_re.match(line)
                    if match:
                        week_num = int(match.group(1))
                        week_date = match.group(2)
                        track_name = match.group(3).strip()
                        weeks.append({
                            "week": week_num,
                            "date": week_date,
                            "track": track_name
                        })
                        
                series_temp.append({
                    "series_id": 1000 + len(series_temp),
                    "series_name": display_title,
                    "original_title": title,
                    "category": line_to_category[idx],
                    "license_group": lic_group_name,
                    "license_group_id": lic_group_id,
                    "fixed_setup": fixed_setup,
                    "official": True,
                    "cars": [c.strip() for c in cars_str.split(",") if c.strip()],
                    "license_line": lic_line,
                    "schedule_line": all_text_lines[idx+1].strip(),
                    "weeks": weeks
                })
                
            self.series_list = series_temp
            
            logger.info(f"Successfully parsed {len(self.series_list)} series from PDF")
            self._build_derived_data()
            
        except Exception as e:
            logger.error(f"Error parsing PDF schedule: {e}", exc_info=True)

    def _build_derived_data(self) -> None:
        """
        Build tracks list, categories list, and licenses list from loaded series.
        """
        categories_set = set()
        licenses_seen = set()
        licenses_temp = []
        tracks_seen = set()
        tracks_temp = []
        
        for s in self.series_list:
            categories_set.add(s["category"])
            
            # Track licenses
            lic_name = s["license_group"]
            lic_id = s["license_group_id"]
            if lic_name not in licenses_seen:
                licenses_seen.add(lic_name)
                licenses_temp.append({"name": lic_name, "id": lic_id})
                
            # Track tracks (dynamically gathered from week schedules)
            for w in s.get("weeks", []):
                full_track_str = w["track"]
                if not full_track_str or full_track_str in tracks_seen:
                    continue
                    
                tracks_seen.add(full_track_str)
                
                # Split track name & config
                if " - " in full_track_str:
                    parts = full_track_str.split(" - ", 1)
                    t_name = parts[0].strip()
                    config_name = parts[1].strip()
                else:
                    t_name = full_track_str
                    config_name = "Full Course"
                    
                # Consistent track ID based on string hash
                track_id = int(hashlib.md5(full_track_str.encode()).hexdigest(), 16) % 10000
                tracks_temp.append({
                    "track_id": track_id,
                    "track_name": t_name,
                    "config_name": config_name,
                    "category": s["category"]
                })
                
        self.categories_list = sorted(list(categories_set))
        self.licenses_list = sorted(licenses_temp, key=lambda x: x["id"])
        self.tracks_list = tracks_temp

    def parse_schedule_rule(self, schedule_str: str) -> dict:
        """
        Parses a schedule line and returns rules for generating sessions.
        """
        interval_hours = 1
        even_hours = None
        minutes = [0]
        specific_slots = []
        
        s = schedule_str.lower()
        
        if "gmt" in s:
            days_map = {
                "mon": 0, "monday": 0, "tues": 1, "wed": 2, "wednesday": 2, 
                "thur": 3, "thurs": 3, "thursday": 3, "fri": 4, "friday": 4, 
                "sat": 5, "saturday": 5, "saturdays": 5, "sun": 6, "sunday": 6, "sundays": 6
            }
            parts = re.split(r'[,&]|\band\b', s)
            current_day = None
            for part in parts:
                part = part.strip()
                for d_name, d_idx in days_map.items():
                    if d_name in part:
                        current_day = d_idx
                        break
                hours = [int(h) for h in re.findall(r'\b\d+\b', part)]
                if current_day is not None and hours:
                    for h in hours:
                        if h < 24:
                            specific_slots.append((current_day, h, 0))
                            
        if not specific_slots:
            if "30 minutes" in s or "thirty minutes" in s:
                interval_hours = 1
                if "15" in s and "45" in s:
                    minutes = [15, 45]
                else:
                    minutes = [0, 30]
            elif "2 hours" in s or "every other hour" in s:
                interval_hours = 2
                if "even" in s:
                    even_hours = True
                elif "odd" in s:
                    even_hours = False
                else:
                    if "15" in s or "45" in s:
                        even_hours = False
                    else:
                        even_hours = True
                        
                m_matches = [int(m) for m in re.findall(r':(\d+)', s)]
                if m_matches:
                    minutes = m_matches
                elif "15 past" in s or "15 after" in s or "15 at" in s:
                    minutes = [15]
                elif "30 past" in s or "30 at" in s or "half past" in s:
                    minutes = [30]
                elif "45 past" in s or "45 at" in s:
                    minutes = [45]
                else:
                    minutes = [0]
            else:
                interval_hours = 1
                m_matches = [int(m) for m in re.findall(r':(\d+)', s)]
                if m_matches:
                    minutes = m_matches
                elif "15" in s:
                    minutes = [15]
                elif "30" in s:
                    minutes = [30]
                elif "45" in s:
                    minutes = [45]
                else:
                    minutes = [0]
                    
        return {
            "interval_hours": interval_hours,
            "even_hours": even_hours,
            "minutes": minutes,
            "specific_slots": specific_slots
        }

    def generate_sessions_for_range(self, start_time: datetime, end_time: datetime) -> list[dict[str, Any]]:
        """
        Generates races schedule dynamically between start_time and end_time (in UTC).
        """
        sessions: list[dict[str, Any]] = []
        
        # Round start time to beginning of the hour for stepping
        current_hour = start_time.replace(minute=0, second=0, microsecond=0)
        
        # Pre-compile schedule rules for each series to save CPU cycles
        series_rules = []
        for s in self.series_list:
            series_rules.append({
                "series": s,
                "rule": self.parse_schedule_rule(s["schedule_line"])
            })
            
        while current_hour <= end_time:
            weekday = current_hour.weekday()
            hour = current_hour.hour
            is_even = hour % 2 == 0
            
            for sr in series_rules:
                s = sr["series"]
                rule = sr["rule"]
                
                # Check schedule rule
                matching_minutes = []
                if rule["specific_slots"]:
                    for spec_day, spec_hour, spec_min in rule["specific_slots"]:
                        if spec_day == weekday and spec_hour == hour:
                            matching_minutes.append(spec_min)
                else:
                    hour_compatible = True
                    if rule["interval_hours"] == 2:
                        if rule["even_hours"] is True and not is_even:
                            hour_compatible = False
                        elif rule["even_hours"] is False and is_even:
                            hour_compatible = False
                            
                    if hour_compatible:
                        matching_minutes = rule["minutes"]
                        
                for min_val in matching_minutes:
                    session_time = current_hour.replace(minute=min_val)
                    if start_time <= session_time <= end_time:
                        # Find track for this session based on date
                        session_date_str = session_time.strftime("%Y-%m-%d")
                        active_track_name = "Unknown Track"
                        
                        # Find the correct week
                        weeks = s.get("weeks", [])
                        active_track_name = "TBD"
                        if weeks:
                            # Weeks are sorted. Find largest week start date <= session_date_str
                            selected_week = weeks[0]
                            for w in weeks:
                                if w["date"] <= session_date_str:
                                    selected_week = w
                                else:
                                    break
                            active_track_name = selected_week["track"]
                            
                        # Split track name & config
                        if " - " in active_track_name:
                            parts = active_track_name.split(" - ", 1)
                            t_name = parts[0].strip()
                            config_name = parts[1].strip()
                        else:
                            t_name = active_track_name
                            config_name = "Full Course"
                            
                        track_id = int(hashlib.md5(active_track_name.encode()).hexdigest(), 16) % 10000
                        track_obj = {
                            "track_id": track_id,
                            "track_name": t_name,
                            "config_name": config_name,
                            "category": s["category"]
                        }
                        
                        # Set realistic popularity score
                        popularity = 85
                        if "fixed" in s["series_name"].lower():
                            popularity += 5
                        if s["license_group"] == "Rookie":
                            popularity += 5
                            
                        sessions.append({
                            "session_id": f"{s['series_id']}_{int(session_time.timestamp())}",
                            "series_id": s["series_id"],
                            "series_name": s["series_name"],
                            "category": s["category"],
                            "license_group": s["license_group"],
                            "license_group_id": s["license_group_id"],
                            "fixed_setup": s["fixed_setup"],
                            "official": True,
                            "cars": s["cars"],
                            "track": track_obj,
                            "start_time": session_time.isoformat(),
                            "end_time": (session_time + timedelta(minutes=30)).isoformat(), # default 30 min length
                            "duration_minutes": 30,
                            "popularity_score": min(popularity, 99)
                        })
                        
            current_hour += timedelta(hours=1)
            
        sessions.sort(key=lambda x: x["start_time"])
        return sessions

# Global singleton
schedule_engine = ScheduleEngine()
