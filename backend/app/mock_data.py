from datetime import datetime, timedelta, timezone
from typing import Any

# Define mock tracks
MOCK_TRACKS: list[dict[str, Any]] = [
    {"track_id": 1, "track_name": "Okayama International Circuit", "config_name": "Full", "category": "Sports Car"},
    {"track_id": 2, "track_name": "Lime Rock Park", "config_name": "Classic", "category": "Sports Car"},
    {"track_id": 3, "track_name": "Red Bull Ring", "config_name": "Grand Prix", "category": "Sports Car"},
    {"track_id": 4, "track_name": "Brands Hatch", "config_name": "Grand Prix", "category": "Sports Car"},
    {"track_id": 5, "track_name": "Circuit de Spa-Francorchamps", "config_name": "Classic GP", "category": "Sports Car"},
    {"track_id": 6, "track_name": "Hockenheimring Baden-Württemberg", "config_name": "Grand Prix", "category": "Sports Car"},
    {"track_id": 7, "track_name": "Daytona International Speedway", "config_name": "Tri-Oval", "category": "Oval"},
    {"track_id": 8, "track_name": "Bristol Motor Speedway", "config_name": "Oval", "category": "Oval"},
    {"track_id": 9, "track_name": "Mount Panorama Motor Racing Circuit", "config_name": "Bathurst", "category": "Sports Car"},
    {"track_id": 10, "track_name": "Eldora Speedway", "config_name": "Dirt Oval", "category": "Dirt Oval"},
    {"track_id": 11, "track_name": "Daytona International Speedway", "config_name": "Rallycross Long", "category": "Dirt Road"},
    {"track_id": 12, "track_name": "Road America", "config_name": "Full Course", "category": "Sports Car"},
    {"track_id": 13, "track_name": "Suzuka International Racing Course", "config_name": "Grand Prix", "category": "Formula Car"},
    {"track_id": 14, "track_name": "Autodromo Nazionale Monza", "config_name": "GP", "category": "Sports Car"},
]

# Define mock series
MOCK_SERIES: list[dict[str, Any]] = [
    {
        "series_id": 101,
        "series_name": "Global Mazda MX-5 Cup",
        "category": "Sports Car",
        "license_group": "Rookie",
        "license_group_id": 1,
        "fixed_setup": True,
        "official": True,
        "cars": ["Global Mazda MX-5 Cup"],
        "track": MOCK_TRACKS[0],  # Okayama
        "duration_minutes": 25,
        "frequency_hours": 1,
        "run_on_even_hours": True,  # runs every hour actually
        "run_on_odd_hours": True,
        "offset_minutes": 0,
        "popularity_score": 95,
    },
    {
        "series_id": 102,
        "series_name": "Formula 1600 Trophy",
        "category": "Formula Car",
        "license_group": "Rookie",
        "license_group_id": 1,
        "fixed_setup": True,
        "official": True,
        "cars": ["Ray FF1600"],
        "track": MOCK_TRACKS[1],  # Lime Rock
        "duration_minutes": 20,
        "frequency_hours": 1,
        "run_on_even_hours": True,
        "run_on_odd_hours": True,
        "offset_minutes": 30,
        "popularity_score": 88,
    },
    {
        "series_id": 103,
        "series_name": "Ferrari GT3 Challenge",
        "category": "Sports Car",
        "license_group": "Class D",
        "license_group_id": 2,
        "fixed_setup": True,
        "official": True,
        "cars": ["Ferrari 296 GT3"],
        "track": MOCK_TRACKS[2],  # Red Bull Ring
        "duration_minutes": 15,
        "frequency_hours": 2,
        "run_on_even_hours": False,
        "run_on_odd_hours": True,  # Odd hours (1, 3, 5...)
        "offset_minutes": 15,
        "popularity_score": 92,
    },
    {
        "series_id": 104,
        "series_name": "FIA Formula 4 Championship",
        "category": "Formula Car",
        "license_group": "Class D",
        "license_group_id": 2,
        "fixed_setup": True,
        "official": True,
        "cars": ["FIA F4"],
        "track": MOCK_TRACKS[3],  # Brands Hatch
        "duration_minutes": 20,
        "frequency_hours": 2,
        "run_on_even_hours": True,  # Even hours (0, 2, 4...)
        "run_on_odd_hours": False,
        "offset_minutes": 45,
        "popularity_score": 90,
    },
    {
        "series_id": 105,
        "series_name": "IMSA iRacing Series",
        "category": "Sports Car",
        "license_group": "Class B",
        "license_group_id": 4,
        "fixed_setup": False,
        "official": True,
        "cars": [
            "Acura ARX-06 GTP",
            "BMW M Hybrid V8 GTP",
            "Cadillac V-Series.R GTP",
            "Dallara P217 LMP2",
            "Porsche 911 GT3 R (992)",
            "Corvette Z06 GT3.R",
            "Ferrari 296 GT3",
            "BMW M4 GT3"
        ],
        "track": MOCK_TRACKS[4],  # Spa
        "duration_minutes": 45,
        "frequency_hours": 2,
        "run_on_even_hours": False,
        "run_on_odd_hours": True,
        "offset_minutes": 0,
        "popularity_score": 98,
    },
    {
        "series_id": 106,
        "series_name": "Porsche iRacing Cup",
        "category": "Sports Car",
        "license_group": "Class C",
        "license_group_id": 3,
        "fixed_setup": True,
        "official": True,
        "cars": ["Porsche 911 GT3 Cup (992)"],
        "track": MOCK_TRACKS[5],  # Hockenheim
        "duration_minutes": 30,
        "frequency_hours": 2,
        "run_on_even_hours": True,
        "run_on_odd_hours": False,
        "offset_minutes": 30,
        "popularity_score": 85,
    },
    {
        "series_id": 107,
        "series_name": "NASCAR Cup Series",
        "category": "Oval",
        "license_group": "Class A",
        "license_group_id": 5,
        "fixed_setup": False,
        "official": True,
        "cars": [
            "Next Gen Chevrolet Camaro ZL1",
            "Next Gen Ford Mustang Dark Horse",
            "Next Gen Toyota Camry XSE"
        ],
        "track": MOCK_TRACKS[6],  # Daytona Oval
        "duration_minutes": 60,
        "frequency_hours": 2,
        "run_on_even_hours": False,
        "run_on_odd_hours": True,
        "offset_minutes": 0,
        "popularity_score": 87,
    },
    {
        "series_id": 108,
        "series_name": "ARCA Menards Series",
        "category": "Oval",
        "license_group": "Class D",
        "license_group_id": 2,
        "fixed_setup": True,
        "official": True,
        "cars": ["ARCA Menards Chevrolet Impala"],
        "track": MOCK_TRACKS[7],  # Bristol
        "duration_minutes": 40,
        "frequency_hours": 1,
        "run_on_even_hours": True,
        "run_on_odd_hours": True,
        "offset_minutes": 0,
        "popularity_score": 82,
    },
    {
        "series_id": 109,
        "series_name": "Supercars Series",
        "category": "Sports Car",
        "license_group": "Class C",
        "license_group_id": 3,
        "fixed_setup": False,
        "official": True,
        "cars": ["Ford Mustang GT Supercar", "Holden ZB Commodore Supercar"],
        "track": MOCK_TRACKS[8],  # Bathurst
        "duration_minutes": 25,
        "frequency_hours": 2,
        "run_on_even_hours": True,
        "run_on_odd_hours": False,
        "offset_minutes": 0,
        "popularity_score": 75,
    },
    {
        "series_id": 110,
        "series_name": "Dirt Late Model Championship",
        "category": "Dirt Oval",
        "license_group": "Class C",
        "license_group_id": 3,
        "fixed_setup": True,
        "official": True,
        "cars": ["Dirt Late Model"],
        "track": MOCK_TRACKS[9],  # Eldora
        "duration_minutes": 20,
        "frequency_hours": 2,
        "run_on_even_hours": False,
        "run_on_odd_hours": True,
        "offset_minutes": 30,
        "popularity_score": 70,
    },
    {
        "series_id": 111,
        "series_name": "iRacing Rallycross Championship",
        "category": "Dirt Road",
        "license_group": "Class D",
        "license_group_id": 2,
        "fixed_setup": True,
        "official": True,
        "cars": ["Subaru WRX STI RX", "Ford Fiesta RS WRC"],
        "track": MOCK_TRACKS[10],  # Daytona RX
        "duration_minutes": 15,
        "frequency_hours": 2,
        "run_on_even_hours": True,
        "run_on_odd_hours": False,
        "offset_minutes": 15,
        "popularity_score": 68,
    },
    {
        "series_id": 112,
        "series_name": "Super Formula Championship",
        "category": "Formula Car",
        "license_group": "Class B",
        "license_group_id": 4,
        "fixed_setup": False,
        "official": True,
        "cars": ["Dallara SF23 - Toyota", "Dallara SF23 - Honda"],
        "track": MOCK_TRACKS[12],  # Suzuka
        "duration_minutes": 35,
        "frequency_hours": 2,
        "run_on_even_hours": True,
        "run_on_odd_hours": False,
        "offset_minutes": 15,
        "popularity_score": 89,
    }
]

def generate_sessions_for_range(start_time: datetime, end_time: datetime) -> list[dict[str, Any]]:
    """
    Generates realistic race sessions between start_time and end_time.
    We align them to their schedule parameters.
    """
    sessions: list[dict[str, Any]] = []
    
    # Let's align start_time to the beginning of the hour
    current = start_time.replace(minute=0, second=0, microsecond=0)
    
    while current <= end_time:
        hour = current.hour
        is_even = hour % 2 == 0
        is_odd = not is_even
        
        for series in MOCK_SERIES:
            match_hour = False
            if series["frequency_hours"] == 1:
                match_hour = True
            elif series["frequency_hours"] == 2:
                if is_even and series["run_on_even_hours"]:
                    match_hour = True
                elif is_odd and series["run_on_odd_hours"]:
                    match_hour = True
                    
            if match_hour:
                session_time = current + timedelta(minutes=series["offset_minutes"])
                if start_time <= session_time <= end_time:
                    sessions.append({
                        "session_id": f"{series['series_id']}_{int(session_time.timestamp())}",
                        "series_id": series["series_id"],
                        "series_name": series["series_name"],
                        "category": series["category"],
                        "license_group": series["license_group"],
                        "license_group_id": series["license_group_id"],
                        "fixed_setup": series["fixed_setup"],
                        "official": series["official"],
                        "cars": series["cars"],
                        "track": series["track"],
                        "start_time": session_time.isoformat(),
                        "end_time": (session_time + timedelta(minutes=series["duration_minutes"])).isoformat(),
                        "duration_minutes": series["duration_minutes"],
                        "popularity_score": series["popularity_score"],
                    })
                    
        current += timedelta(hours=1)
        
    # Sort by start_time
    sessions.sort(key=lambda s: s["start_time"])
    return sessions

def get_upcoming_sessions(days: int = 7) -> list[dict[str, Any]]:
    """
    Generates sessions starting from 'now' in UTC up to 'days' into the future.
    """
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    return generate_sessions_for_range(now, end)
