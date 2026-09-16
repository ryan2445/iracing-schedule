import os
import re
import glob
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any
import pypdf

logger = logging.getLogger(__name__)


def get_pdf_path() -> str:
    """Finds the most recent iRacing schedule PDF available."""
    env_path = os.environ.get("IRACING_SCHEDULE_PDF")
    if env_path and os.path.exists(env_path):
        return env_path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    candidates = glob.glob(os.path.join(base_dir, "iracing_season_*_schedule.pdf"))
    if not candidates:
        candidates = glob.glob("iracing_season_*_schedule.pdf") + glob.glob("../iracing_season_*_schedule.pdf")
    if candidates:
        candidates.sort(key=lambda p: [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", p)], reverse=True)
        return candidates[0]
    return os.path.join(base_dir, "iracing_season_4_schedule.pdf")


PDF_PATH = get_pdf_path()

categories_map: dict[str, str] = {
    "OVAL": "Oval",
    "SPORTS CAR": "Sports Car",
    "FORMULA CAR": "Formula Car",
    "DIRT OVAL": "Dirt Oval",
    "DIRT ROAD": "Dirt Road",
    "UNRANKED": "Unranked",
}

license_groups_map: dict[str, dict[str, Any]] = {
    "Rookie": {"name": "Rookie", "id": 1},
    "Class D": {"name": "Class D", "id": 2},
    "Class C": {"name": "Class C", "id": 3},
    "Class B": {"name": "Class B", "id": 4},
    "Class A": {"name": "Class A", "id": 5},
    "Pro": {"name": "Pro", "id": 6},
}


class ScheduleEngine:
    def __init__(self) -> None:
        self.series_list: list[dict[str, Any]] = []
        self.tracks_list: list[dict[str, Any]] = []
        self.categories_list: list[str] = []
        self.licenses_list: list[dict[str, Any]] = []
        self.series_rules: list[dict[str, Any]] = []
        self.load_schedule()

    def load_schedule(self) -> None:
        """
        Loads schedule directly from the PDF.
        """
        self.parse_pdf_schedule()

        # Pre-compile schedule rules for each series to save CPU cycles
        self.series_rules = []
        for s in self.series_list:
            self.series_rules.append(
                {"series": s, "rule": self.parse_schedule_rule(s["schedule_line"])}
            )

    def parse_pdf_schedule(self) -> None:
        """
        Parses the season PDF schedule.
        """
        logger.info(f"Parsing schedule PDF at {PDF_PATH}...")
        if not os.path.exists(PDF_PATH):
            logger.error(f"PDF file not found at {PDF_PATH}!")
            return

        try:
            reader = pypdf.PdfReader(PDF_PATH)
            all_text_lines: list[str] = []

            # Extract authoritative TOC series ordering & category
            toc_series = self._parse_toc(reader)

            # Skip first 5 pages of Table of Contents
            for i in range(5, len(reader.pages)):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    all_text_lines.extend(page_text.split("\n"))

            license_indices = [idx for idx, line in enumerate(all_text_lines) if "-->" in line]
            line_to_category = self._build_line_to_category_map(all_text_lines)

            series_temp: list[dict[str, Any]] = []

            for index_in_list, idx in enumerate(license_indices):
                candidates = self._extract_series_candidates(all_text_lines, idx)
                if not candidates:
                    continue

                title = candidates[0]
                cars_str = self._join_candidate_lines(candidates[1:]) if len(candidates) > 1 else title
                display_title = self._clean_series_title(title)
                
                lic_line = all_text_lines[idx].strip()
                lic_group_name, lic_group_id = self._parse_license_group(lic_line)
                fixed_setup = self._is_fixed_setup(display_title, title, lic_line)

                next_idx = (
                    license_indices[index_in_list + 1]
                    if index_in_list + 1 < len(license_indices)
                    else len(all_text_lines)
                )
                if index_in_list < len(toc_series):
                    category = toc_series[index_in_list][1]
                else:
                    category = line_to_category.get(idx, "Oval")
                
                weeks = self._parse_weeks(all_text_lines, idx, next_idx, category)
                is_team_racing = "team racing" in lic_line.lower()
                min_drivers = self._parse_min_drivers(all_text_lines, idx, next_idx) if is_team_racing else None

                series_temp.append(
                    {
                        "series_id": 1000 + len(series_temp),
                        "series_name": display_title,
                        "original_title": title,
                        "category": category,
                        "license_group": lic_group_name,
                        "license_group_id": lic_group_id,
                        "fixed_setup": fixed_setup,
                        "cars": [c.strip() for c in cars_str.split(",") if c.strip()],
                        "license_line": lic_line,
                        "schedule_line": all_text_lines[idx + 1].strip(),
                        "weeks": weeks,
                        "team_racing": is_team_racing,
                        "min_drivers": min_drivers,
                    }
                )

            self.series_list = series_temp
            logger.info(f"Successfully parsed {len(self.series_list)} series from PDF")
            self._build_derived_data()

        except Exception as e:
            logger.error(f"Error parsing PDF schedule: {e}", exc_info=True)

    def _parse_toc(self, reader: pypdf.PdfReader) -> list[tuple[str, str]]:
        """Extracts ordered list of (title, category) from Table of Contents."""
        toc_lines: list[str] = []
        for i in range(min(5, len(reader.pages))):
            t = reader.pages[i].extract_text()
            if t:
                toc_lines.extend(t.split("\n"))

        current_cat = "Oval"
        series_info: list[tuple[str, str]] = []
        for line in toc_lines:
            s = line.strip()
            if not s or ". ." not in s:
                continue
            first_part = s.split(". .")[0].strip()
            u = first_part.upper()
            if u in categories_map:
                current_cat = categories_map[u]
                continue
            if re.match(r"^[RDCBA]\s+Class\s+Series", first_part, re.IGNORECASE):
                continue
            series_info.append((first_part, current_cat))
        return series_info

    def _build_line_to_category_map(self, all_text_lines: list[str]) -> dict[int, str]:
        """Maps line numbers to categories sequentially as a fallback."""
        line_to_category = {}
        current_cat = "Oval"
        for idx, line in enumerate(all_text_lines):
            cleaned = line.strip().upper()
            if cleaned in categories_map:
                current_cat = categories_map[cleaned]
            line_to_category[idx] = current_cat
        return line_to_category

    def _is_boundary_line(self, line: str) -> bool:
        """Checks if a line marks the boundary of series details / previous series."""
        s = line.strip()
        if not s or s.isdigit():
            return True
        u = s.upper()
        if u in categories_map or re.match(r"^[RDCBA]\s+Class\s+Series", s, re.IGNORECASE) or "rule set" in s.lower():
            return True
        if any(
            s.startswith(p)
            for p in [
                "Week ", "Races ", "Min entries ", "Penalty ", "No incident ", "DQ at ",
                "(", "Rolling", "Standing", "Forecast", "Single-file", "- Permissive", "- Strict", "Maintain"
            ]
        ):
            return True
        if re.match(r"^[HCF]:\d+L", s) or re.match(r"^[A-Z0-9]{2,4}:\s*\d+\s*tire", s, re.IGNORECASE):
            return True
        if any(k in s.lower() for k in ["laps", "mins", "tire sets", "scrutiny", "cautions", "°f", "°c", "rain chance"]):
            return True
        return False

    def _extract_series_candidates(self, all_text_lines: list[str], idx: int) -> list[str]:
        """Extracts candidate lines for series title and vehicle description by walking backwards."""
        candidates: list[str] = []
        for back_idx in range(idx - 1, max(0, idx - 20), -1):
            line = all_text_lines[back_idx].strip()
            if not line or line.isdigit():
                continue
            if self._is_boundary_line(line):
                break
            candidates.insert(0, line)
        return candidates

    def _join_candidate_lines(self, lines: list[str]) -> str:
        """Helper to join PDF line breaks correctly for wrapped text."""
        if not lines:
            return ""
        joined = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not joined:
                joined = line
            else:
                if joined.endswith("-"):
                    joined = joined + line
                else:
                    joined = joined + " " + line
        return joined

    def _clean_series_title(self, raw_title: str) -> str:
        """Cleans schedule patterns out of the raw series title."""
        s = raw_title
        s = re.sub(r"Season(?:\s+\d+)?\s+Fixed$", "Season - Fixed", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*-\s*20\d{2}\s*-\s*Season(?:\s+\d+)?\s*", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*20\d{2}\s*-\s*Season(?:\s+\d+)?\s*", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*-\s*20\d{2}\s+Season(?:\s+\d+)?\s*-?\s*", " - ", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*20\d{2}\s+Season(?:\s+\d+)?\s*", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"-\s*Fixed(?:\s*-\s*Fixed)+", "- Fixed", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*-\s*-\s*", " - ", s)
        s = re.sub(r"\s*-\s*$", "", s)
        s = re.sub(r"^\s*-\s*", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _parse_license_group(self, lic_line: str) -> tuple[str, int]:
        """Determines license group name and ID from the license description line."""
        for group_key, group_info in license_groups_map.items():
            if lic_line.strip().startswith(group_key):
                return str(group_info["name"]), int(group_info["id"])
        return "Rookie", 1

    def _is_fixed_setup(self, display_title: str, title: str, lic_line: str) -> bool:
        """Determines if the series uses a fixed setup."""
        return (
            "fixed" in display_title.lower()
            or "fixed" in title.lower()
            or "fixed" in lic_line.lower()
        )

    def _parse_weeks(self, all_text_lines: list[str], idx: int, next_idx: int, category: str) -> list[dict[str, Any]]:
        """Parses the weekly schedule details for a series."""
        weeks = []
        week_re = re.compile(r"^Week\s+(\d+)\s+\(([^)]+)\)\s*(.*)$")
        timeslot_re = re.compile(r"^\(20\d{2}-\d{2}-\d{2}")

        skip_until = -1
        for j in range(idx, next_idx):
            if j <= skip_until:
                continue
            line = all_text_lines[j].strip()
            match = week_re.match(line)
            if match:
                week_num = int(match.group(1))
                week_date = match.group(2)
                track_name = match.group(3).strip()

                # Check if next line is a track continuation (wrapped track name or config)
                consumed_next = False
                if j + 1 < next_idx:
                    next_l = all_text_lines[j + 1].strip()
                    if (
                        next_l
                        and not timeslot_re.match(next_l)
                        and not next_l.startswith("Week ")
                        and "-->" not in next_l
                        and not next_l.startswith("Dirt Outlaw Micro Sprint Car")
                        and not any(k in next_l.lower() for k in ["°f", "°c", "rain chance", "cautions", "laps", "mins", "rolling", "standing", "qual scrutiny"])
                    ):
                        if track_name.endswith("-") or (not next_l.isdigit() and any(track_name.endswith(" " + term) for term in ["Open Wheel", "without", "without first", "GT", "Grand", "Infield Road", "Historical", "24 Heures du", "Big", "Legends Road", "Kurzanbindung", "National", "West", "Dirt Road", "Rallycross"])):
                            track_name = (track_name + " " + next_l).replace("  ", " ").strip()
                            skip_until = j + 1
                            consumed_next = True

                # Split track name & config
                if " - " in track_name:
                    parts = track_name.split(" - ", 1)
                    t_name = parts[0].strip()
                    config_name = parts[1].strip()
                else:
                    t_name = track_name
                    config_name = "Full Course"

                # Consistent track ID based on string hash
                track_id = int(hashlib.md5(track_name.encode()).hexdigest(), 16) % 10000
                track_obj = {
                    "track_id": track_id,
                    "track_name": t_name,
                    "config_name": config_name,
                    "category": category,
                }

                # Scan forward to collect detail lines for this week
                detail_lines = []
                start_k = (j + 2) if consumed_next else (j + 1)
                for k in range(start_k, next_idx):
                    nl = all_text_lines[k].strip()
                    if week_re.match(nl) or "-->" in nl:
                        break
                    detail_lines.append(nl)

                duration_minutes, duration_laps = self._parse_duration(detail_lines, category)
                timeslot_time = self._parse_timeslot(detail_lines)

                weeks.append(
                    {
                        "week": week_num,
                        "date": week_date,
                        "track": track_name,
                        "track_obj": track_obj,
                        "duration_minutes": duration_minutes,
                        "duration_laps": duration_laps,
                        "timeslot_time": timeslot_time,
                    }
                )
        return weeks

    def _parse_duration(self, detail_lines: list[str], category: str) -> tuple[int, int | None]:
        """Parses session duration (minutes or laps) from the week's detail lines."""
        joined_details = " ".join(detail_lines)
        dur_mins_re = re.compile(r"(\d+)\s*(?:mins|minutes|min)", re.IGNORECASE)
        dur_laps_re = re.compile(r"(\d+)\s*(?:laps|lap)", re.IGNORECASE)

        m_mins = dur_mins_re.search(joined_details)
        m_laps = dur_laps_re.search(joined_details)

        mins_val = int(m_mins.group(1)) if m_mins else None
        laps_val = int(m_laps.group(1)) if m_laps else None

        duration_minutes = 30  # default
        if mins_val is not None:
            duration_minutes = mins_val
        elif laps_val is not None:
            cat_upper = category.upper()
            if "OVAL" in cat_upper:
                lap_time_seconds = 25  # estimate 25 seconds for Oval
            else:
                lap_time_seconds = 100  # estimate 100 seconds for road/other
            duration_minutes = max(10, int((laps_val * lap_time_seconds) / 60))

        return duration_minutes, laps_val

    def _parse_timeslot(self, detail_lines: list[str]) -> str | None:
        """Parses timeslot timestamp from the week's detail lines."""
        timeslot_re = re.compile(r"\((20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2})(?:\s+[^)]+)?\)")
        for dl in detail_lines:
            t_match = timeslot_re.search(dl)
            if t_match:
                return t_match.group(1)
        return None

    def _parse_min_drivers(self, all_text_lines: list[str], idx: int, next_idx: int) -> int | None:
        """Parses minimum driver count for team racing series."""
        series_lines_to_search = [all_text_lines[k].strip() for k in range(idx, next_idx)]
        joined_series_text = " ".join(series_lines_to_search)
        match_drivers = re.search(r"Min\s+(\d+)\s+driver", joined_series_text, re.IGNORECASE)
        if match_drivers:
            return int(match_drivers.group(1))
        return None

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
                tracks_temp.append(w["track_obj"])

        self.categories_list = sorted(list(categories_set))
        self.licenses_list = sorted(licenses_temp, key=lambda x: x["id"])
        self.tracks_list = tracks_temp

    def parse_schedule_rule(self, schedule_str: str) -> dict[str, Any]:
        """
        Parses a schedule line and returns rules for generating sessions.
        """
        interval_hours = 1
        even_hours = None
        minutes = [0]
        specific_slots: list[tuple[int, int, int]] = []

        s = schedule_str.lower()

        if "gmt" in s or "et" in s or "est" in s or "edt" in s:
            specific_slots = self._parse_gmt_specific_slots(s)

        if not specific_slots:
            interval_hours, even_hours, minutes = self._parse_regular_intervals(s)

        is_timeslot = "timeslot" in s

        return {
            "interval_hours": interval_hours,
            "even_hours": even_hours,
            "minutes": minutes,
            "specific_slots": specific_slots,
            "is_timeslot": is_timeslot,
        }

    def _parse_gmt_specific_slots(self, s: str) -> list[tuple[int, int, int]]:
        """Parses GMT or ET specific timeslots from schedule string."""
        days_map = {
            "mon": 0, "monday": 0,
            "tues": 1, "tue": 1, "tuesday": 1,
            "weds": 2, "wed": 2, "wednesday": 2,
            "thur": 3, "thurs": 3, "thursday": 3,
            "fri": 4, "friday": 4,
            "sat": 5, "saturday": 5, "saturdays": 5,
            "sun": 6, "sunday": 6, "sundays": 6,
        }

        # Check for ET pattern: e.g. "Races on Monday at 8pm ET"
        et_match = re.search(r"\b(mon(?:day)?|tue(?:sday)?|wed(?:nesday)?|thu(?:rsday)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b.*?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:et|est|edt)", s)
        if et_match:
            day_str = et_match.group(1)
            day_idx = days_map.get(day_str, 0)
            hour = int(et_match.group(2))
            minute = int(et_match.group(3)) if et_match.group(3) else 0
            ampm = et_match.group(4)
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            utc_hour = (hour + 4) % 24
            utc_day = (day_idx + ((hour + 4) // 24)) % 7
            return [(utc_day, utc_hour, minute)]

        if "gmt" not in s:
            return []

        slots: list[tuple[int, int, int]] = []
        cleaned = re.sub(r"every other\s+", "", s)
        chunks = cleaned.split("gmt")
        last_days: list[int] = []

        for chunk in chunks:
            chunk = chunk.strip(" ,;&")
            if not chunk:
                continue

            day_matches: list[tuple[int, int]] = []
            for d_name, d_idx in sorted(days_map.items(), key=lambda x: -len(x[0])):
                for m in re.finditer(rf"\b{d_name}\b", chunk):
                    day_matches.append((m.start(), d_idx))

            day_matches.sort(key=lambda x: x[0])
            days: list[int] = []
            for _, d_idx in day_matches:
                if d_idx not in days:
                    days.append(d_idx)

            if not days and last_days:
                days = list(last_days)
            elif days:
                last_days = list(days)

            time_part = chunk
            if day_matches:
                last_day_pos = day_matches[-1][0]
                time_part = chunk[last_day_pos:]

            times = re.findall(r"\b(\d{1,2})(?::(\d{2}))?\b", time_part)
            for d in days:
                for h_str, m_str in times:
                    h = int(h_str)
                    m = int(m_str) if m_str else 0
                    if h < 24 and m < 60:
                        slots.append((d, h, m))

        return sorted(list(set(slots)))

    def _parse_regular_intervals(self, s: str) -> tuple[int, bool | None, list[int]]:
        """Parses regular interval patterns from schedule string."""
        interval_hours = 1
        even_hours = None
        minutes = [0]

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
                even_hours = False if ("15" in s or "45" in s) else True

            m_matches = [int(m) for m in re.findall(r":(\d+)", s)]
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
            m_matches = [int(m) for m in re.findall(r":(\d+)", s)]
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

        return interval_hours, even_hours, minutes

    def generate_sessions_for_range(
        self, start_time: datetime, end_time: datetime
    ) -> list[dict[str, Any]]:
        """
        Generates races schedule dynamically between start_time and end_time (in UTC).
        """
        sessions: list[dict[str, Any]] = []

        # 1. Generate sessions for timeslot-based series first
        self._generate_timeslot_sessions(sessions, start_time, end_time)

        # 2. Generate regular interval sessions hour by hour
        self._generate_regular_sessions(sessions, start_time, end_time)

        sessions.sort(key=lambda x: x["start_time"])
        return sessions

    def _generate_timeslot_sessions(
        self, sessions: list[dict[str, Any]], start_time: datetime, end_time: datetime
    ) -> None:
        """Generates sessions for timeslot-based series."""
        for sr in self.series_rules:
            s = sr["series"]
            rule = sr["rule"]

            if not rule.get("is_timeslot"):
                continue

            for w in s.get("weeks", []):
                ts_str = w.get("timeslot_time")
                if not ts_str:
                    continue

                try:
                    session_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M")
                    if start_time.tzinfo is not None:
                        session_time = session_time.replace(tzinfo=start_time.tzinfo)
                except Exception as e:
                    logger.error(
                        f"Error parsing timeslot time {ts_str} for series {s['series_name']}: {e}"
                    )
                    continue

                if start_time <= session_time <= end_time:
                    track_obj = w.get("track_obj") or {
                        "track_id": 0,
                        "track_name": "TBD",
                        "config_name": "Full Course",
                        "category": s["category"],
                    }
                    sessions.append(self._create_session_dict(s, w, session_time, track_obj))

    def _generate_regular_sessions(
        self, sessions: list[dict[str, Any]], start_time: datetime, end_time: datetime
    ) -> None:
        """Generates sessions for regular interval-based series."""
        # Round start time to beginning of the hour for stepping normal hourly series
        current_hour = start_time.replace(minute=0, second=0, microsecond=0)

        while current_hour <= end_time:
            weekday = current_hour.weekday()
            hour = current_hour.hour
            is_even = hour % 2 == 0

            for sr in self.series_rules:
                s = sr["series"]
                rule = sr["rule"]

                if rule.get("is_timeslot"):
                    continue

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
                        self._add_matching_regular_session(sessions, s, session_time, start_time)

            current_hour += timedelta(hours=1)

    def _add_matching_regular_session(
        self, sessions: list[dict[str, Any]], s: dict[str, Any], session_time: datetime, start_time: datetime
    ) -> None:
        """Checks if session date lies in an active week and adds the session if so."""
        session_date_str = session_time.strftime("%Y-%m-%d")
        weeks = s.get("weeks", [])
        if not weeks:
            track_obj = {
                "track_id": 0,
                "track_name": "TBD",
                "config_name": "Full Course",
                "category": s["category"],
            }
            sessions.append(self._create_session_dict(s, {}, session_time, track_obj))
            return

        selected_week = None
        for w in weeks:
            if w["date"] <= session_date_str:
                selected_week = w
            else:
                break

        if not selected_week:
            return

        # Enforce 7-day active window limit for the week to prevent generation on gap/off-weeks
        week_start_dt = datetime.strptime(selected_week["date"], "%Y-%m-%d")
        if start_time.tzinfo is not None:
            week_start_dt = week_start_dt.replace(tzinfo=start_time.tzinfo)

        week_end_dt = week_start_dt + timedelta(days=7)
        if week_start_dt <= session_time < week_end_dt:
            track_obj = selected_week.get("track_obj") or {
                "track_id": 0,
                "track_name": "TBD",
                "config_name": "Full Course",
                "category": s["category"],
            }
            sessions.append(self._create_session_dict(s, selected_week, session_time, track_obj))

    def _create_session_dict(
        self, s: dict[str, Any], week_info: dict[str, Any], session_time: datetime, track_obj: dict[str, Any]
    ) -> dict[str, Any]:
        """Creates a standardized session dictionary format."""
        return {
            "session_id": f"{s['series_id']}_{int(session_time.timestamp())}",
            "series_id": s["series_id"],
            "series_name": s["series_name"],
            "category": s["category"],
            "license_group": s["license_group"],
            "license_group_id": s["license_group_id"],
            "fixed_setup": s["fixed_setup"],
            "cars": s["cars"],
            "track": track_obj,
            "start_time": session_time.isoformat(),
            "duration_minutes": week_info.get("duration_minutes", 30),
            "duration_laps": week_info.get("duration_laps"),
            "team_racing": s.get("team_racing", False),
            "min_drivers": s.get("min_drivers"),
        }


# Global singleton
schedule_engine = ScheduleEngine()
