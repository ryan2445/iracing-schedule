<script lang="ts">
  import SessionCard from './SessionCard.svelte';
  import { Calendar, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-svelte';

  interface Track {
    track_id: number;
    track_name: string;
    config_name: string;
    category: string;
  }

  interface Session {
    session_id: string;
    series_id: number;
    series_name: string;
    category: string;
    license_group: string;
    license_group_id: number;
    fixed_setup: boolean;
    cars: string[];
    track: Track;
    start_time: string;
    duration_minutes: number;
    duration_laps?: number | null;
  }

  // Svelte 5 Props Rune
  let { sessions } = $props<{ sessions: Session[] }>();

  // Svelte 5 State Runes
  let selectedDayIndex = $state(0);

  // Generate the next 7 days in local time
  const days = $derived(
    Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() + i);
      return d;
    })
  );

  // Helper to format days
  function formatDayLabel(d: Date) {
    return d.toLocaleDateString([], { weekday: 'short' });
  }

  function formatDayNum(d: Date) {
    return d.getDate();
  }

  function formatMonthLabel(d: Date) {
    return d.toLocaleDateString([], { month: 'short' });
  }

  // Check if session start_time is on the same calendar day as the given Date object
  function isSameDay(sessionTimeStr: string, date: Date) {
    const sessionDate = new Date(sessionTimeStr);
    return (
      sessionDate.getFullYear() === date.getFullYear() &&
      sessionDate.getMonth() === date.getMonth() &&
      sessionDate.getDate() === date.getDate()
    );
  }

  // Derived filtered sessions for the selected day
  const dailySessions = $derived(
    sessions.filter((s: Session) => isSameDay(s.start_time, days[selectedDayIndex]))
  );

  // Pagination for fast rendering inside the calendar view
  let limitCount = $state(100);
  const displayedDailySessions = $derived(dailySessions.slice(0, limitCount));

  $effect(() => {
    // Reset limit whenever sessions or selected day changes
    sessions;
    selectedDayIndex;
    limitCount = 100;
  });
</script>

<div class="calendar-container glass-panel">
  <div class="calendar-header">
    <div class="header-title">
      <Calendar size={18} class="text-primary-color" />
      <h3>Race Schedule Planner</h3>
    </div>
    <div class="navigation-hints text-muted">
      Select a day to view its complete schedule
    </div>
  </div>

  <!-- Day Selection Track -->
  <div class="day-selector">
    <button 
      class="nav-arrow" 
      disabled={selectedDayIndex === 0} 
      onclick={() => selectedDayIndex--}
      aria-label="Previous day"
    >
      <ChevronLeft size={18} />
    </button>
    
    <div class="days-track">
      {#each days as day, index}
        <button 
          class="day-tab {index === selectedDayIndex ? 'active' : ''}"
          onclick={() => selectedDayIndex = index}
        >
          <span class="day-name">{formatDayLabel(day)}</span>
          <span class="day-number">{formatDayNum(day)}</span>
          <span class="day-month">{formatMonthLabel(day)}</span>
        </button>
      {/each}
    </div>

    <button 
      class="nav-arrow" 
      disabled={selectedDayIndex === days.length - 1} 
      onclick={() => selectedDayIndex++}
      aria-label="Next day"
    >
      <ChevronRight size={18} />
    </button>
  </div>

  <!-- Daily Schedule linear timeline -->
  <div class="schedule-body">
    <div class="day-indicator">
      <h4>{days[selectedDayIndex].toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</h4>
      <span class="badge badge-sessions-count">{dailySessions.length} Races Scheduled</span>
    </div>

    {#if dailySessions.length === 0}
      <div class="empty-schedule">
        <p class="text-secondary">No races scheduled for this day matching your current filters.</p>
        <p class="text-muted text-small">Try clearing some filters or searching for another series.</p>
      </div>
    {:else}
      <div class="timeline-wrapper">
        <div class="timeline-line"></div>
        <div class="sessions-list">
          {#each displayedDailySessions as session (session.session_id)}
            <div class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-card-container">
                <SessionCard {session} />
              </div>
            </div>
          {/each}
        </div>

        {#if dailySessions.length > limitCount}
          <div class="load-more-container">
            <button class="btn-load-more" onclick={() => limitCount += 100}>
              <RefreshCw size={14} />
              <span>Show More ({dailySessions.length - limitCount} remaining)</span>
            </button>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .calendar-container {
    padding: 24px;
    border-radius: 16px;
  }

  .calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
    margin-bottom: 20px;
  }

  @media (max-width: 600px) {
    .calendar-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
    }
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-title h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .navigation-hints {
    font-size: 0.8rem;
  }

  /* Day selector styles */
  .day-selector {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 24px;
  }

  .days-track {
    flex-grow: 1;
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
    overflow-x: auto;
  }

  @media (max-width: 768px) {
    .days-track {
      display: flex;
      scroll-snap-type: x mandatory;
      padding-bottom: 6px;
    }
  }

  .day-tab {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 10px 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    transition: all var(--transition-normal);
    min-width: 60px;
    scroll-snap-align: start;
  }

  .day-tab:hover {
    border-color: rgba(243, 18, 58, 0.3);
    background-color: rgba(243, 18, 58, 0.02);
  }

  .day-tab.active {
    background-color: var(--primary);
    border-color: var(--primary);
    box-shadow: 0 4px 12px rgba(243, 18, 58, 0.25);
  }

  .day-tab.active .day-name,
  .day-tab.active .day-number,
  .day-tab.active .day-month {
    color: #ffffff;
  }

  .day-name {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .day-number {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.1;
    margin: 4px 0 2px;
  }

  .day-month {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
  }

  .nav-arrow {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .nav-arrow:hover:not(:disabled) {
    border-color: var(--text-primary);
    color: var(--text-primary);
  }

  .nav-arrow:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  /* Schedule layout */
  .schedule-body {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .day-indicator {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 1px dashed var(--border-color);
  }

  .day-indicator h4 {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .badge-sessions-count {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    font-size: 0.7rem;
  }

  .empty-schedule {
    padding: 40px 20px;
    text-align: center;
    background-color: rgba(0,0,0,0.1);
    border-radius: 12px;
    border: 1px dashed var(--border-color);
  }

  .text-small {
    font-size: 0.8rem;
    margin-top: 4px;
  }

  /* Timeline */
  .timeline-wrapper {
    position: relative;
    padding-left: 16px;
  }

  .timeline-line {
    position: absolute;
    top: 10px;
    bottom: 10px;
    left: 4.5px;
    width: 2px;
    background: linear-gradient(to bottom, var(--primary), var(--border-color) 40%, var(--border-color));
  }

  .sessions-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .timeline-item {
    position: relative;
    padding-left: 20px;
  }

  .timeline-dot {
    position: absolute;
    left: -14.5px;
    top: 30px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: var(--bg-main);
    border: 2px solid var(--primary);
    box-shadow: 0 0 5px var(--primary);
    z-index: 1;
    transition: transform var(--transition-fast);
  }

  .timeline-item:hover .timeline-dot {
    transform: scale(1.3);
  }

  .timeline-card-container {
    width: 100%;
  }

  /* Load More styling */
  .load-more-container {
    display: flex;
    justify-content: center;
    margin: 24px 0 12px;
  }

  .btn-load-more {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all var(--transition-normal);
  }

  .btn-load-more:hover {
    border-color: rgba(243, 18, 58, 0.4);
    background-color: rgba(243, 18, 58, 0.05);
    color: #fff;
    box-shadow: 0 4px 15px rgba(243, 18, 58, 0.15);
  }
</style>
