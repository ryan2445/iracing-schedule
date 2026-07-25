<script lang="ts">
  import {
    Activity,
    Info,
    RefreshCw,
    Gauge,
    Clock,
    SlidersHorizontal
  } from 'lucide-svelte'
  import Filters from './lib/Filters.svelte'
  import SessionCard from './lib/SessionCard.svelte'
  import { generateSessionsForRange, getCategories } from './lib/scheduleEngine'
  import type { Session } from './lib/scheduleEngine'

  // Fetch categories directly (synchronous and static)
  const categories = getCategories()

  // Filter bindings
  let searchQuery = $state('')
  let selectedCategories = $state<string[]>([])

  // Sorting bindings
  type SortField =
    | 'start_time'
    | 'series_name'
    | 'category'
    | 'license_group_id'
    | 'duration_minutes'
    | 'track_name'
    | 'fixed_setup'
  let sortBy = $state<SortField>('start_time')
  let sortOrder = $state<'asc' | 'desc'>('asc')

  // Pagination / Limiting for ultra-fast rendering performance
  let limitCount = $state(100)

  // Reset limitCount whenever filters change to keep things responsive
  $effect(() => {
    searchQuery
    selectedCategories
    limitCount = 100
  })

  // Synchronous, reactive derived session generation (7-day window)
  const sessions = $derived.by(() => {
    const now = new Date()
    const end = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
    let allSessions = generateSessionsForRange(now, end)

    // Apply category filter
    if (selectedCategories.length > 0) {
      allSessions = allSessions.filter((s) =>
        selectedCategories.includes(s.category)
      )
    }

    // Apply search query filter (series, track or cars)
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      allSessions = allSessions.filter((s) => {
        const seriesMatch = s.series_name.toLowerCase().includes(query)
        const trackMatch =
          s.track.track_name.toLowerCase().includes(query) ||
          s.track.config_name.toLowerCase().includes(query)
        const carMatch = s.cars.some((car) =>
          car.toLowerCase().includes(query)
        )
        return seriesMatch || trackMatch || carMatch
      })
    }

    return allSessions
  })

  // Filter sessions to only keep the next upcoming timeslot for each series
  const nextUpcomingSessions = $derived.by(() => {
    const minSessionsMap = new Map<number, Session>()
    for (const session of sessions) {
      const existing = minSessionsMap.get(session.series_id)
      if (
        !existing ||
        new Date(session.start_time) < new Date(existing.start_time)
      ) {
        minSessionsMap.set(session.series_id, session)
      }
    }
    return Array.from(minSessionsMap.values())
  })

  // Sorting logic using Svelte 5 derived rune
  const sortedSessions = $derived.by(() => {
    const list = [...nextUpcomingSessions]
    list.sort((a, b) => {
      let valA: any
      let valB: any

      if (sortBy === 'track_name') {
        valA = a.track?.track_name || ''
        valB = b.track?.track_name || ''
      } else {
        valA = a[sortBy]
        valB = b[sortBy]
      }

      if (typeof valA === 'string') {
        valA = valA.toLowerCase()
        valB = (valB || '').toLowerCase()
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
    return list
  })

  const displayedSessions = $derived(sortedSessions.slice(0, limitCount))

  // Dashboard Stats
  const activeSeriesCount = $derived(
    new Set(sessions.map((s) => s.series_id)).size
  )

  const startingSoonCount = $derived(
    sessions.filter((s) => {
      const diff = new Date(s.start_time).getTime() - new Date().getTime()
      return diff > 0 && diff <= 30 * 60 * 1000 // in next 30 minutes
    }).length
  )

  function handleSortChange(fieldId: SortField) {
    if (sortBy === fieldId) {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy = fieldId
      sortOrder = fieldId === 'start_time' ? 'desc' : 'asc'
    }
  }
</script>

<div class="bg-glow-effect"></div>

<header class="app-header">
  <div class="header-logo">
    <div class="logo-glow">
      <Gauge size={28} />
    </div>
    <div class="title-block">
      <h1>iRacing Race Tracker</h1>
    </div>
  </div>
</header>

<main>
  <section class="stats-panel-grid">
    <div class="metric-card glass-panel">
      <div class="metric-icon-wrap sports-car">
        <Activity size={20} />
      </div>
      <div class="metric-content">
        <span class="metric-label">Active Series</span>
        <span class="metric-value">{activeSeriesCount}</span>
      </div>
    </div>

    <div class="metric-card glass-panel">
      <div class="metric-icon-wrap active-green">
        <Clock size={20} />
      </div>
      <div class="metric-content">
        <span class="metric-label">Starting Soon</span>
        <span class="metric-value">{startingSoonCount}</span>
      </div>
    </div>
  </section>

  <!-- Shared Filter Dashboard Component -->
  <Filters
    bind:search={searchQuery}
    bind:selectedCategories
    availableCategories={categories}
  />

  <!-- Timeline Linear View -->
  <div class="linear-schedule-container">
    <div class="view-header">
      <h2>Live Race Grid</h2>
      <span class="badge badge-sessions-count"
        >{nextUpcomingSessions.length} upcoming sessions found</span
      >
    </div>

    <!-- Premium Sort Toolbar -->
    <div class="sort-toolbar-panel glass-panel">
      <div class="sort-label-group">
        <SlidersHorizontal size={14} class="text-primary-color" />
        <span class="sort-title">Sort Grid:</span>
      </div>
      <div class="sort-pills-container">
        {#each [{ id: 'start_time', label: 'Start Time' }, { id: 'series_name', label: 'Series Name' }, { id: 'category', label: 'Category' }, { id: 'license_group_id', label: 'License' }, { id: 'duration_minutes', label: 'Duration' }, { id: 'track_name', label: 'Track' }, { id: 'fixed_setup', label: 'Setup' }] as field}
          <button
            class="sort-pill-btn {sortBy === field.id ? 'active' : ''}"
            onclick={() => handleSortChange(field.id as SortField)}
          >
            <span>{field.label}</span>
            {#if sortBy === field.id}
              <span class="sort-dir-arrow">
                {sortOrder === 'asc' ? '↑' : '↓'}
              </span>
            {/if}
          </button>
        {/each}
      </div>
    </div>

    {#if nextUpcomingSessions.length === 0}
      <div class="empty-state glass-panel">
        <Info size={32} class="text-secondary" />
        <h3>No Match Found</h3>
        <p>
          No active series match your search query or selected criteria. Try
          resetting filters.
        </p>
      </div>
    {:else}
      <div class="sessions-vertical-stack">
        {#each displayedSessions as session (session.session_id)}
          <SessionCard {session} />
        {/each}
      </div>

      {#if nextUpcomingSessions.length > limitCount}
        <div class="load-more-container">
          <button class="btn-load-more" onclick={() => (limitCount += 100)}>
            <RefreshCw size={14} />
            <span
              >Show More ({nextUpcomingSessions.length - limitCount} remaining)</span
            >
          </button>
        </div>
      {/if}
    {/if}
  </div>
</main>

<style>
  /* App Header Styles */
  .app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 32px 0 24px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 24px;
  }

  @media (max-width: 900px) {
    .app-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
      padding: 24px 0 16px;
    }
  }

  .header-logo {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .logo-glow {
    background: linear-gradient(135deg, #a855f7 0%, #7e22ce 100%);
    color: #fff;
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 18px var(--primary-glow);
    animation: pulseGlow 3s ease-in-out infinite alternate;
  }

  @keyframes pulseGlow {
    0% {
      box-shadow: 0 0 10px var(--primary-glow);
    }
    100% {
      box-shadow: 0 0 24px rgba(168, 85, 247, 0.75);
    }
  }

  .title-block {
    display: flex;
    flex-direction: column;
  }

  .title-block h1 {
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.03em;
    background: linear-gradient(to right, #ffffff, #c4b5fd, #a855f7);
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  /* Dashboard Stats Grid (Modified to 2 Columns) */
  .stats-panel-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }

  @media (max-width: 550px) {
    .stats-panel-grid {
      grid-template-columns: 1fr;
    }
  }

  .metric-card {
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    border-radius: 12px;
  }

  .metric-icon-wrap {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .metric-icon-wrap.sports-car {
    background-color: rgba(255, 0, 127, 0.1);
    color: var(--color-sports-car);
  }

  .metric-icon-wrap.active-green {
    background-color: rgba(57, 255, 20, 0.1);
    color: var(--accent-green);
  }

  .metric-content {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.05em;
  }

  .metric-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  /* Sorting Toolbar Panel */
  .sort-toolbar-panel {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 12px 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    background-color: var(--bg-surface);
    border: 1px solid var(--border-color);
  }

  @media (max-width: 900px) {
    .sort-toolbar-panel {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
      padding: 16px;
    }
    .sort-pills-container {
      width: 100%;
    }
  }

  .sort-label-group {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-secondary);
    min-width: 110px;
  }

  .sort-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .sort-pills-container {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    flex-grow: 1;
  }

  .sort-pill-btn {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all var(--transition-fast);
  }

  .sort-pill-btn:hover {
    color: var(--text-primary);
    border-color: rgba(255, 255, 255, 0.15);
    background-color: rgba(255, 255, 255, 0.02);
  }

  .sort-pill-btn.active {
    background-color: var(--primary);
    color: #fff;
    border-color: var(--primary);
    box-shadow: 0 0 10px var(--primary-glow);
  }

  .sort-dir-arrow {
    font-size: 0.8rem;
    font-weight: 700;
  }

  /* Linear View Header */
  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .view-header h2 {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  .badge-sessions-count {
    background-color: var(--bg-surface);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
  }

  /* Loading and Error states */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 14px;
    padding: 60px 20px;
    border-radius: 12px;
  }

  .empty-state h3 {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .empty-state p {
    font-size: 0.9rem;
    color: var(--text-secondary);
    max-width: 450px;
  }

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
    border-color: rgba(168, 85, 247, 0.5);
    background-color: rgba(168, 85, 247, 0.1);
    color: #fff;
    box-shadow: 0 4px 18px rgba(168, 85, 247, 0.25);
  }
</style>
