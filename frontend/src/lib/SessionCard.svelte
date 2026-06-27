<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    Clock, 
    MapPin, 
    Car, 
    CheckCircle, 
    Lock, 
    ChevronDown, 
    ChevronUp,
    Calendar,
    Award
  } from 'lucide-svelte';

  // Svelte 5 Runes for Props
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
    official: boolean;
    cars: string[];
    track: Track;
    start_time: string;
    end_time: string;
    duration_minutes: number;
    popularity_score: number;
  }

  let { session } = $props<{ session: Session }>();

  // Svelte 5 State Runes
  let isExpanded = $state(false);
  let countdownText = $state('');
  let statusColor = $state('text-secondary');
  let isNearStart = $state(false);

  function toggleExpand(e: Event) {
    e.stopPropagation();
    isExpanded = !isExpanded;
  }

  // Format date nicely (e.g. "Sat 14:00")
  function formatLocalTime(isoString: string) {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  }

  function formatLocalDate(isoString: string) {
    const d = new Date(isoString);
    return d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  }

  // Live countdown effect
  function updateCountdown() {
    const start = new Date(session.start_time).getTime();
    const now = new Date().getTime();
    const diff = start - now;

    if (diff < 0) {
      const activeDiff = now - start;
      const durationMs = session.duration_minutes * 60 * 1000;
      if (activeDiff < durationMs) {
        countdownText = 'Race in Progress';
        statusColor = 'text-green';
        isNearStart = true;
      } else {
        countdownText = 'Finished';
        statusColor = 'text-muted';
        isNearStart = false;
      }
      return;
    }

    const totalSeconds = Math.floor(diff / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);

    if (days > 0) {
      countdownText = `Starts in ${days}d ${hours}h`;
      statusColor = 'text-secondary';
      isNearStart = false;
    } else if (hours > 0) {
      countdownText = `Starts in ${hours}h ${minutes}m`;
      statusColor = 'text-secondary';
      isNearStart = hours === 0;
    } else {
      countdownText = `Starts in ${minutes}m`;
      statusColor = 'text-primary-color';
      isNearStart = true;
    }
  }

  onMount(() => {
    updateCountdown();
    const interval = setInterval(updateCountdown, 30000); // update every 30s
    return () => clearInterval(interval);
  });
</script>

<div 
  class="session-card glass-panel {isNearStart ? 'near-start' : ''} {isExpanded ? 'expanded' : ''}"
  onclick={() => isExpanded = !isExpanded}
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
        <span class="tag-category {session.category.toLowerCase().replace(' ', '-')}">
          {session.category}
        </span>
        <span class="badge badge-license {session.license_group.toLowerCase().replace(' ', '-')}">
          {session.license_group}
        </span>
        {#if session.fixed_setup}
          <span class="badge badge-setup fixed">Fixed</span>
        {:else}
          <span class="badge badge-setup open">Open</span>
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
      <button class="expand-btn" onclick={toggleExpand} aria-label="Toggle details">
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
              <span class="stat-value">{session.duration_minutes} Mins</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Official Race</span>
              <span class="stat-value">{session.official ? 'Yes' : 'No'}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Popularity</span>
              <span class="stat-value">{session.popularity_score}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">End Time</span>
              <span class="stat-value">{formatLocalTime(session.end_time)}</span>
            </div>
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
    transition: background-color var(--transition-fast), color var(--transition-fast);
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
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .details-grid {
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 24px;
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
    grid-template-columns: 1fr 1fr;
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
</style>
