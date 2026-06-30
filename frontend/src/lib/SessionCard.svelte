<script lang="ts">
  import { onMount } from 'svelte'
  import {
    Clock,
    MapPin,
    Car,
    ChevronDown,
    ChevronUp,
    Award,
    Users,
    Calendar
  } from 'lucide-svelte'
  import type { Session } from './scheduleEngine'

  let { session }: { session: Session } = $props<{ session: Session }>()

  // Svelte 5 State Runes
  let isExpanded = $state(false)
  let countdownText = $state('')
  let statusColor = $state('text-secondary')
  let isNearStart = $state(false)

  // Format specific slots to local timezone, sort, and group them by day
  const formattedLocalSlots = $derived.by(() => {
    if (
      !session.rule ||
      !session.rule.specific_slots ||
      session.rule.specific_slots.length === 0
    ) {
      return null
    }

    const slots = session.rule.specific_slots.map(
      ([utcDay, utcHour, utcMin]: [number, number, number]) => {
        // June 1, 2026 is a Monday (UTC)
        const d = new Date(Date.UTC(2026, 5, 1 + utcDay, utcHour, utcMin))
        const localDayNum = d.getDay() // 0 = Sun, 1 = Mon, ..., 6 = Sat
        const sortDayNum = localDayNum === 0 ? 6 : localDayNum - 1 // Mon = 0, ..., Sun = 6
        const dayName = d.toLocaleDateString([], { weekday: 'long' })
        const timeStr = d.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        })

        return {
          sortDayNum,
          dayName,
          timeStr,
          sortTime: d.getHours() * 60 + d.getMinutes()
        }
      }
    )

    // Sort chronologically (by day, then by time)
    slots.sort((a: any, b: any) => {
      if (a.sortDayNum !== b.sortDayNum) {
        return a.sortDayNum - b.sortDayNum
      }
      return a.sortTime - b.sortTime
    })

    // Group by day name
    const groups: { day: string; times: string[] }[] = []
    for (const slot of slots) {
      let group = groups.find((g) => g.day === slot.dayName)
      if (!group) {
        group = { day: slot.dayName, times: [] }
        groups.push(group)
      }
      if (!group.times.includes(slot.timeStr)) {
        group.times.push(slot.timeStr)
      }
    }

    return groups
  })

  function toggleExpand(e: Event) {
    e.stopPropagation()
    isExpanded = !isExpanded
  }

  // Format date nicely (e.g. "Sat 14:00")
  function formatLocalTime(isoString: string) {
    const d = new Date(isoString)
    return d.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  }

  function formatLocalDate(isoString: string) {
    const d = new Date(isoString)
    return d.toLocaleDateString([], {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    })
  }

  // Live countdown effect
  function updateCountdown() {
    const start = new Date(session.start_time).getTime()
    const now = new Date().getTime()
    const diff = start - now

    if (diff < 0) {
      const activeDiff = now - start
      const durationMs = session.duration_minutes * 60 * 1000
      if (activeDiff < durationMs) {
        countdownText = 'Race in Progress'
        statusColor = 'text-green'
        isNearStart = true
      } else {
        countdownText = 'Finished'
        statusColor = 'text-muted'
        isNearStart = false
      }
      return
    }

    const totalSeconds = Math.floor(diff / 1000)
    const days = Math.floor(totalSeconds / 86400)
    const hours = Math.floor((totalSeconds % 86400) / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)

    if (days > 0) {
      countdownText = `Starts in ${days}d ${hours}h`
      statusColor = 'text-secondary'
      isNearStart = false
    } else if (hours > 0) {
      countdownText = `Starts in ${hours}h ${minutes}m`
      statusColor = 'text-secondary'
      isNearStart = hours === 0
    } else {
      countdownText = `Starts in ${minutes}m`
      statusColor = 'text-primary-color'
      isNearStart = true
    }
  }

  onMount(() => {
    updateCountdown()
    const interval = setInterval(updateCountdown, 30000) // update every 30s
    return () => clearInterval(interval)
  })
</script>

<div
  class="session-card glass-panel {isNearStart ? 'near-start' : ''} {isExpanded
    ? 'expanded'
    : ''}"
  onclick={() => (isExpanded = !isExpanded)}
  role="button"
  tabindex="0"
  onkeydown={(e) => e.key === 'Enter' && (isExpanded = !isExpanded)}
>
  <div class="card-header">
    <div class="time-block">
      <span class="time-main">{formatLocalTime(session.start_time)}</span>
      <span class="date-sub">{formatLocalDate(session.start_time)}</span>
    </div>

    <div class="divider-line"></div>

    <div class="series-block">
      <div class="series-meta">
        <span
          class="tag-category {session.category
            .toLowerCase()
            .replace(' ', '-')}"
        >
          {session.category}
        </span>
        <span
          class="badge badge-license {session.license_group
            .toLowerCase()
            .replace(' ', '-')}"
        >
          {session.license_group}
        </span>
        {#if session.fixed_setup}
          <span class="badge badge-setup fixed">Fixed</span>
        {:else}
          <span class="badge badge-setup open">Open</span>
        {/if}
        {#if session.team_racing}
          <span
            class="badge badge-team"
            title="Team Series (Min {session.min_drivers ||
              1} {session.min_drivers === 1 ? 'driver' : 'drivers'})"
          >
            <Users size={11} />
            <span>Team (Min {session.min_drivers || 1})</span>
          </span>
        {/if}
      </div>
      <h3 class="series-name">{session.series_name}</h3>
      <div class="track-info">
        <MapPin size={14} class="text-muted" />
        <span class="track-name">{session.track.track_name}</span>
        <span class="track-config">• {session.track.config_name}</span>
      </div>
    </div>

    <div class="status-block">
      <div class="countdown-wrapper {statusColor}">
        <Clock size={14} />
        <span class="countdown-text">{countdownText}</span>
      </div>
      <button
        class="expand-btn"
        onclick={toggleExpand}
        aria-label="Toggle details"
      >
        {#if isExpanded}
          <ChevronUp size={20} />
        {:else}
          <ChevronDown size={20} />
        {/if}
      </button>
    </div>
  </div>

  {#if isExpanded}
    <div class="card-details">
      <div class="details-grid">
        <div class="detail-section">
          <h4 class="section-title">
            <Car size={15} />
            <span>Eligible Vehicles ({session.cars.length})</span>
          </h4>
          <ul class="car-list">
            {#each session.cars as car}
              <li>{car}</li>
            {/each}
          </ul>
        </div>

        <div class="detail-section">
          <h4 class="section-title">
            <Award size={15} />
            <span>Session Stats</span>
          </h4>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">Duration</span>
              <span class="stat-value">
                {#if session.duration_laps}
                  {session.duration_laps} Laps
                {:else}
                  {session.duration_minutes} Mins
                {/if}
              </span>
            </div>
            {#if session.team_racing}
              <div class="stat-item">
                <span class="stat-label">Team Event</span>
                <span class="stat-value">
                  Yes ({session.min_drivers || 1}
                  {session.min_drivers === 1 ? 'Driver' : 'Drivers'} Min)
                </span>
              </div>
            {/if}
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">
            <Calendar size={15} />
            <span>Series Schedule</span>
          </h4>
          <div class="schedule-card">
            {#if session.schedule_line}
              <div class="schedule-line">{session.schedule_line}</div>
            {:else}
              <div class="schedule-line text-muted">
                No schedule line available
              </div>
            {/if}

            {#if formattedLocalSlots && formattedLocalSlots.length > 0}
              <div class="local-slots-wrapper">
                <span class="local-slots-title">Your Local Timeslots</span>
                <div class="local-slots-grid">
                  {#each formattedLocalSlots as group}
                    <div class="local-slot-item">
                      <span class="slot-day">{group.day}</span>
                      <span class="slot-times">{group.times.join(', ')}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .session-card {
    margin-bottom: 12px;
    cursor: pointer;
    transition: all var(--transition-normal);
    overflow: hidden;
  }

  .session-card:hover {
    transform: translateX(4px);
  }

  .session-card.near-start {
    border-left: 3px solid var(--primary);
    box-shadow: 0 0 15px rgba(243, 18, 58, 0.15);
  }

  .card-header {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    gap: 20px;
  }

  @media (max-width: 768px) {
    .card-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
    }
    .divider-line {
      display: none;
    }
  }

  .time-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 80px;
    text-align: center;
  }

  @media (max-width: 768px) {
    .time-block {
      flex-direction: row;
      align-items: center;
      gap: 10px;
      min-width: auto;
      text-align: left;
    }
  }

  .time-main {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
  }

  .date-sub {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    color: var(--text-secondary);
  }

  .divider-line {
    width: 1px;
    height: 45px;
    background-color: var(--border-color);
  }

  .series-block {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .series-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 2px;
  }

  .badge-setup {
    font-size: 0.65rem;
    font-weight: 700;
    border-radius: 4px;
    padding: 2px 6px;
    text-transform: uppercase;
  }

  .badge-setup.fixed {
    background-color: rgba(0, 240, 255, 0.1);
    color: var(--accent-cyan);
    border: 1px solid rgba(0, 240, 255, 0.3);
  }

  .badge-setup.open {
    background-color: rgba(255, 255, 255, 0.05);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
  }

  .badge-team {
    font-size: 0.65rem;
    font-weight: 700;
    border-radius: 4px;
    padding: 2px 6px;
    text-transform: uppercase;
    background: linear-gradient(
      135deg,
      rgba(168, 85, 247, 0.15) 0%,
      rgba(236, 72, 153, 0.15) 100%
    );
    color: #f472b6;
    border: 1px solid rgba(236, 72, 153, 0.35);
    text-shadow: 0 0 8px rgba(236, 72, 153, 0.2);
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .series-name {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.01em;
  }

  .track-info {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: var(--text-secondary);
  }

  .track-name {
    font-weight: 500;
    color: var(--text-secondary);
  }

  .track-config {
    color: var(--text-muted);
  }

  .status-block {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  @media (max-width: 768px) {
    .status-block {
      width: 100%;
      justify-content: space-between;
      border-top: 1px solid var(--border-color);
      padding-top: 10px;
    }
  }

  .countdown-wrapper {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-color);
  }

  .text-green {
    color: var(--accent-green);
    border-color: rgba(57, 255, 20, 0.2);
    background-color: rgba(57, 255, 20, 0.05);
    text-shadow: 0 0 10px rgba(57, 255, 20, 0.2);
  }

  .text-primary-color {
    color: var(--primary);
    border-color: rgba(243, 18, 58, 0.2);
    background-color: rgba(243, 18, 58, 0.05);
    text-shadow: 0 0 10px rgba(243, 18, 58, 0.2);
  }

  .text-secondary {
    color: var(--text-secondary);
  }

  .text-muted {
    color: var(--text-muted);
  }

  .expand-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border-radius: 50%;
    transition:
      background-color var(--transition-fast),
      color var(--transition-fast);
  }

  .expand-btn:hover {
    background-color: var(--bg-surface-elevated);
    color: var(--text-primary);
  }

  /* Expanded Detail Section */
  .card-details {
    border-top: 1px solid var(--border-color);
    background-color: rgba(0, 0, 0, 0.15);
    padding: 20px;
    animation: slideDown 0.25s ease-out;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-5px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .details-grid {
    display: grid;
    grid-template-columns: 1.2fr 1fr 1.2fr;
    gap: 24px;
  }

  @media (max-width: 1024px) {
    .details-grid {
      grid-template-columns: 1.2fr 1fr;
    }
  }

  @media (max-width: 768px) {
    .details-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }
  }

  .detail-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--text-primary);
    border-bottom: 1.5px solid var(--border-color);
    padding-bottom: 6px;
  }

  .car-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .car-list li {
    font-size: 0.85rem;
    color: var(--text-secondary);
    padding: 6px 10px;
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    transition: border-color var(--transition-fast);
  }

  .car-list li:hover {
    border-color: rgba(243, 18, 58, 0.2);
    color: var(--text-primary);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 10px;
  }

  .stat-item {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 8px 12px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .stat-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    font-weight: 600;
  }

  .stat-value {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  /* Schedule Styles */
  .schedule-card {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .schedule-line {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.4;
  }

  .local-slots-wrapper {
    display: flex;
    flex-direction: column;
    gap: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    padding-top: 10px;
  }

  .local-slots-title {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.05em;
  }

  .local-slots-grid {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 150px;
    overflow-y: auto;
    padding-right: 4px;
  }

  /* Customize scrollbar for premium feel */
  .local-slots-grid::-webkit-scrollbar {
    width: 4px;
  }
  .local-slots-grid::-webkit-scrollbar-track {
    background: transparent;
  }
  .local-slots-grid::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 2px;
  }

  .local-slot-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    background-color: rgba(255, 255, 255, 0.02);
    padding: 6px 10px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.03);
    transition: border-color var(--transition-fast);
  }

  .local-slot-item:hover {
    border-color: rgba(243, 18, 58, 0.15);
  }

  .slot-day {
    font-weight: 600;
    color: var(--text-secondary);
  }

  .slot-times {
    color: var(--primary);
    font-weight: 700;
    text-shadow: 0 0 8px rgba(243, 18, 58, 0.15);
  }
</style>
