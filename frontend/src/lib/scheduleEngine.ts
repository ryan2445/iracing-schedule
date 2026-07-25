import scheduleData from './schedule.json'

export interface Track {
  track_id: number
  track_name: string
  config_name: string
  category: string
}

export interface Week {
  week: number
  date: string
  track_obj?: Track
  duration_minutes?: number
  duration_laps?: number
  timeslot_time?: string
}

export interface Rule {
  interval_hours: number
  even_hours: boolean | null
  minutes: number[]
  specific_slots: [number, number, number][] // [weekday, hour, minute]
  is_timeslot: boolean
}

export interface Series {
  series_id: number
  series_name: string
  category: string
  license_group: string
  license_group_id: number
  fixed_setup: boolean
  cars: string[]
  weeks: Week[]
  team_racing?: boolean
  min_drivers?: number | null
  schedule_line?: string
  rule: Rule
}

export interface Session {
  session_id: string
  series_id: number
  series_name: string
  category: string
  license_group: string
  license_group_id: number
  fixed_setup: boolean
  cars: string[]
  track: Track
  start_time: string // ISO string
  duration_minutes: number
  duration_laps?: number | null
  team_racing: boolean
  min_drivers?: number | null
  schedule_line?: string
  rule?: Rule
}

// Convert Date to Python weekday (0=Monday, ..., 6=Sunday)
function getPythonWeekday(date: Date): number {
  const day = date.getUTCDay()
  return day === 0 ? 6 : day - 1
}

export function generateSessionsForRange(
  startTime: Date,
  endTime: Date
): Session[] {
  const sessions: Session[] = []
  const seriesList = scheduleData.series as unknown as Series[]

  // 1. Generate sessions for timeslot-based series first
  generateTimeslotSessions(sessions, seriesList, startTime, endTime)

  // 2. Process non-timeslot based series hour by hour
  generateRegularSessions(sessions, seriesList, startTime, endTime)

  // Sort sessions chronologically by start_time
  sessions.sort((a, b) => a.start_time.localeCompare(b.start_time))
  return sessions
}

function generateTimeslotSessions(
  sessions: Session[],
  seriesList: Series[],
  startTime: Date,
  endTime: Date
): void {
  for (const s of seriesList) {
    const rule = s.rule
    if (!rule.is_timeslot) continue

    for (const w of s.weeks || []) {
      const tsStr = w.timeslot_time
      if (!tsStr) continue

      // Parse UTC timestamp: e.g. "2026-06-23 18:30" -> "2026-06-23T18:30:00Z"
      const sessionTime = new Date(tsStr.replace(' ', 'T') + 'Z')
      if (isNaN(sessionTime.getTime())) continue

      if (sessionTime >= startTime && sessionTime <= endTime) {
        const trackObj = w.track_obj || {
          track_id: 0,
          track_name: 'TBD',
          config_name: 'Full Course',
          category: s.category
        }

        sessions.push(createSessionObject(s, w, sessionTime, trackObj))
      }
    }
  }
}

function generateRegularSessions(
  sessions: Session[],
  seriesList: Series[],
  startTime: Date,
  endTime: Date
): void {
  // Round start time to the beginning of the hour
  let currentHour = new Date(
    Date.UTC(
      startTime.getUTCFullYear(),
      startTime.getUTCMonth(),
      startTime.getUTCDate(),
      startTime.getUTCHours(),
      0,
      0,
      0
    )
  )

  while (currentHour <= endTime) {
    const weekday = getPythonWeekday(currentHour)
    const hour = currentHour.getUTCHours()
    const isEven = hour % 2 === 0

    for (const s of seriesList) {
      const rule = s.rule
      if (rule.is_timeslot) continue

      const matchingMinutes = getMatchingMinutes(rule, weekday, hour, isEven)

      for (const minVal of matchingMinutes) {
        const sessionTime = new Date(currentHour.getTime() + minVal * 60 * 1000)
        if (sessionTime >= startTime && sessionTime <= endTime) {
          addRegularSessionIfActive(sessions, s, sessionTime)
        }
      }
    }

    currentHour = new Date(currentHour.getTime() + 60 * 60 * 1000)
  }
}

function getMatchingMinutes(
  rule: Rule,
  weekday: number,
  hour: number,
  isEven: boolean
): number[] {
  if (rule.specific_slots && rule.specific_slots.length > 0) {
    const matchingMinutes: number[] = []
    for (const [specDay, specHour, specMin] of rule.specific_slots) {
      if (specDay === weekday && specHour === hour) {
        matchingMinutes.push(specMin)
      }
    }
    return matchingMinutes
  }

  let hourCompatible = true
  if (rule.interval_hours === 2) {
    if (rule.even_hours === true && !isEven) {
      hourCompatible = false
    } else if (rule.even_hours === false && isEven) {
      hourCompatible = false
    }
  }

  return hourCompatible ? rule.minutes : []
}

function addRegularSessionIfActive(
  sessions: Session[],
  s: Series,
  sessionTime: Date
): void {
  const sessionDateStr = sessionTime.toISOString().substring(0, 10) // YYYY-MM-DD
  const weeks = s.weeks || []
  let trackObj = null
  let durationMinutes = 30
  let durationLaps: number | null = null

  if (weeks.length > 0) {
    // Find largest week start date <= sessionDateStr
    let selectedWeek = null
    for (const w of weeks) {
      if (w.date <= sessionDateStr) {
        selectedWeek = w
      } else {
        break
      }
    }

    if (!selectedWeek) return

    // Enforce 7-day active window limit for the week
    const weekStartDt = new Date(selectedWeek.date + 'T00:00:00Z')
    const weekEndDt = new Date(weekStartDt.getTime() + 7 * 24 * 60 * 60 * 1000)

    if (sessionTime >= weekStartDt && sessionTime < weekEndDt) {
      trackObj = selectedWeek.track_obj
      durationMinutes = selectedWeek.duration_minutes ?? 30
      durationLaps = selectedWeek.duration_laps ?? null
    } else {
      return
    }
  }

  const finalTrack = trackObj || {
    track_id: 0,
    track_name: 'TBD',
    config_name: 'Full Course',
    category: s.category
  }

  sessions.push({
    session_id: `${s.series_id}_${Math.floor(sessionTime.getTime() / 1000)}`,
    series_id: s.series_id,
    series_name: s.series_name,
    category: s.category,
    license_group: s.license_group,
    license_group_id: s.license_group_id,
    fixed_setup: s.fixed_setup,
    cars: s.cars,
    track: finalTrack,
    start_time: sessionTime.toISOString(),
    duration_minutes: durationMinutes,
    duration_laps: durationLaps,
    team_racing: s.team_racing ?? false,
    min_drivers: s.min_drivers ?? null,
    schedule_line: s.schedule_line,
    rule: s.rule
  })
}

function createSessionObject(
  s: Series,
  w: Week,
  sessionTime: Date,
  track: Track
): Session {
  return {
    session_id: `${s.series_id}_${Math.floor(sessionTime.getTime() / 1000)}`,
    series_id: s.series_id,
    series_name: s.series_name,
    category: s.category,
    license_group: s.license_group,
    license_group_id: s.license_group_id,
    fixed_setup: s.fixed_setup,
    cars: s.cars,
    track: track,
    start_time: sessionTime.toISOString(),
    duration_minutes: w.duration_minutes ?? 30,
    duration_laps: w.duration_laps ?? null,
    team_racing: s.team_racing ?? false,
    min_drivers: s.min_drivers ?? null,
    schedule_line: s.schedule_line,
    rule: s.rule
  }
}

export function getCategories(): string[] {
  return scheduleData.categories
}

export function getLicenses(): { name: string; id: number }[] {
  return scheduleData.licenses
}

export function getTracks(): Track[] {
  return scheduleData.tracks
}
