<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { 
    Activity, 
    List, 
    Calendar as CalendarIcon, 
    Info, 
    AlertTriangle, 
    RefreshCw, 
    Zap, 
    Gauge, 
    Clock, 
    ArrowUp,
    ArrowDown,
    SlidersHorizontal
  } from 'lucide-svelte';

  import Filters from './lib/Filters.svelte';
  import SessionCard from './lib/SessionCard.svelte';
  import CalendarView from './lib/CalendarView.svelte';
  import OAuthPanel from './lib/OAuthPanel.svelte';

  // Svelte 5 Types
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

  interface APIStatus {
    status: string;
    mock_mode: boolean;
    username: string;
    time_utc: string;
  }

  // Svelte 5 State Runes
  let currentView = $state<'list' | 'calendar'>('list');
  let apiStatus = $state<APIStatus | null>(null);
  
  // Available filter options fetched on mount
  let categories = $state<string[]>([]);
  
  // Filter bindings
  let searchQuery = $state('');
  let selectedCategories = $state<string[]>([]);

  // Sorting bindings
  type SortField = 'start_time' | 'series_name' | 'category' | 'license_group_id' | 'duration_minutes' | 'track_name' | 'fixed_setup';
  let sortBy = $state<SortField>('start_time');
  let sortOrder = $state<'asc' | 'desc'>('asc');

  // Loaded sessions list
  let sessions = $state<Session[]>([]);
  let isLoadingSessions = $state(false);
  let sessionFetchError = $state('');

  // Pagination / Limiting for ultra-fast rendering performance
  let limitCount = $state(100);

  // Filter sessions to only keep the next upcoming timeslot for each series
  const nextUpcomingSessions = $derived.by(() => {
    const minSessionsMap = new Map<number, Session>();
    for (const session of sessions) {
      const existing = minSessionsMap.get(session.series_id);
      if (!existing || new Date(session.start_time) < new Date(existing.start_time)) {
        minSessionsMap.set(session.series_id, session);
      }
    }
    return Array.from(minSessionsMap.values());
  });

  // Sorting logic using Svelte 5 fine-grained derived rune
  const sortedSessions = $derived.by(() => {
    const list = [...nextUpcomingSessions];
    list.sort((a, b) => {
      let valA: any;
      let valB: any;

      if (sortBy === 'track_name') {
        valA = a.track?.track_name || '';
        valB = b.track?.track_name || '';
      } else {
        valA = a[sortBy];
        valB = b[sortBy];
      }

      if (typeof valA === 'string') {
        valA = valA.toLowerCase();
        valB = (valB || '').toLowerCase();
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  });

  const displayedSessions = $derived(sortedSessions.slice(0, limitCount));

  $effect(() => {
    // Reset limitCount whenever sessions array changes (e.g. filters applied)
    sessions;
    limitCount = 100;
  });

  // Dashboard Stats
  const activeSeriesCount = $derived(new Set(sessions.map(s => s.series_id)).size);
  
  const startingSoonCount = $derived(
    sessions.filter(s => {
      const diff = new Date(s.start_time).getTime() - new Date().getTime();
      return diff > 0 && diff <= 30 * 60 * 1000; // in next 30 minutes
    }).length
  );


  // Fetch meta-information from the backend API
  async function fetchMetadata() {
    try {
      const [statusRes, catRes] = await Promise.all([
        fetch('http://localhost:8000/api/status'),
        fetch('http://localhost:8000/api/categories')
      ]);

      if (statusRes.ok) apiStatus = await statusRes.json();
      if (catRes.ok) categories = await catRes.json();
    } catch (e) {
      console.error('Failed to load initial metadata', e);
    }
  }

  // Fetch filtered sessions from the backend API
  async function fetchSessions() {
    isLoadingSessions = true;
    sessionFetchError = '';

    try {
      const url = new URL('http://localhost:8000/api/sessions');
      
      // Append query filters
      if (searchQuery) {
        url.searchParams.append('search', searchQuery);
      }
      
      // Append array filters (multi-value query params)
      selectedCategories.forEach(cat => {
        url.searchParams.append('category', cat);
      });

      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`Failed to load sessions: ${response.statusText}`);
      }

      sessions = await response.json();
    } catch (err: any) {
      sessionFetchError = err.message || 'Error connecting to the API.';
    } finally {
      isLoadingSessions = false;
    }
  }

  // Svelte 5 fine-grained reactive effect to reload sessions when filters change
  $effect(() => {
    // This will trigger automatically when any of these state variables change
    searchQuery;
    selectedCategories;
    
    untrack(() => {
      fetchSessions();
    });
  });

  function handleSortChange(fieldId: SortField) {
    if (sortBy === fieldId) {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = fieldId;
      if (fieldId === 'start_time') {
        sortOrder = 'desc';
      } else {
        sortOrder = 'asc';
      }
    }
  }

  function toggleSortOrder() {
    sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
  }

  onMount(() => {
    fetchMetadata();
  });
</script>

<div class="bg-glow-effect"></div>

<header class="app-header">
  <div class="header-logo">
    <div class="logo-glow">
      <Gauge size={28} />
    </div>
    <div class="title-block">
      <h1>iRacing Race Tracker</h1>
      <p class="title-sub">Ultimate Live Schedule & Series Planner</p>
    </div>
  </div>

  <div class="view-switcher-tabs">
    <button 
      class="tab-btn {currentView === 'list' ? 'active' : ''}" 
      onclick={() => currentView = 'list'}
    >
      <List size={16} />
      <span>Linear Timeline</span>
    </button>
    <button 
      class="tab-btn {currentView === 'calendar' ? 'active' : ''}" 
      onclick={() => currentView = 'calendar'}
    >
      <CalendarIcon size={16} />
      <span>Calendar Planner</span>
    </button>
  </div>
</header>

<main>
  <!-- OAuth Integration and connection configuration panel -->
  <OAuthPanel status={apiStatus} onConfigUpdated={fetchMetadata} />

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

  <!-- Main View Render Block -->
  {#if isLoadingSessions}
    <div class="loading-state">
      <RefreshCw size={32} class="spinner text-primary-color" />
      <p class="text-secondary">Retrieving latest session schedules...</p>
    </div>
  {:else if sessionFetchError}
    <div class="error-state glass-panel">
      <AlertTriangle size={32} class="text-primary-color" />
      <h3>API Connection Failed</h3>
      <p>{sessionFetchError}</p>
      <button class="btn-primary" onclick={fetchSessions}>
        <RefreshCw size={16} />
        <span>Try Reconnecting</span>
      </button>
    </div>
  {:else if currentView === 'list'}
    <!-- Timeline Linear View -->
    <div class="linear-schedule-container">
      <div class="view-header">
        <h2>Live Race Grid</h2>
        <span class="badge badge-sessions-count">{nextUpcomingSessions.length} upcoming sessions found</span>
      </div>

      <!-- Premium Sort Toolbar -->
      <div class="sort-toolbar-panel glass-panel">
        <div class="sort-label-group">
          <SlidersHorizontal size={14} class="text-primary-color" />
          <span class="sort-title">Sort Grid:</span>
        </div>
        <div class="sort-pills-container">
          {#each [
            { id: 'start_time', label: 'Start Time' },
            { id: 'series_name', label: 'Series Name' },
            { id: 'category', label: 'Category' },
            { id: 'license_group_id', label: 'License' },
            { id: 'duration_minutes', label: 'Duration' },
            { id: 'track_name', label: 'Track' },
            { id: 'fixed_setup', label: 'Setup' }
          ] as field}
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
        <button class="sort-order-toggle" onclick={toggleSortOrder} aria-label="Toggle sorting order">
          {#if sortOrder === 'asc'}
            <ArrowUp size={12} />
            <span>Ascending</span>
          {:else}
            <ArrowDown size={12} />
            <span>Descending</span>
          {/if}
        </button>
      </div>

      {#if nextUpcomingSessions.length === 0}
        <div class="empty-state glass-panel">
          <Info size={32} class="text-secondary" />
          <h3>No Match Found</h3>
          <p>No active series match your search query or selected criteria. Try resetting filters.</p>
        </div>
      {:else}
        <div class="sessions-vertical-stack">
          {#each displayedSessions as session (session.session_id)}
            <SessionCard {session} />
          {/each}
        </div>

        {#if nextUpcomingSessions.length > limitCount}
          <div class="load-more-container">
            <button class="btn-load-more" onclick={() => limitCount += 100}>
              <RefreshCw size={14} />
              <span>Show More ({nextUpcomingSessions.length - limitCount} remaining)</span>
            </button>
          </div>
        {/if}
      {/if}
    </div>
  {:else}
    <!-- Calendar Weekly View -->
    <CalendarView {sessions} />
  {/if}
</main>

<footer>
  <p class="footer-text">iRacing Race Tracker is an independent dashboard. Track schedules and metadata are subject to change by iRacing.com.</p>
</footer>

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
    .view-switcher-tabs {
      width: 100%;
    }
  }

  .header-logo {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .logo-glow {
    background-color: var(--primary);
    color: #fff;
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 15px var(--primary-glow);
    animation: pulseGlow 3s ease-in-out infinite alternate;
  }

  @keyframes pulseGlow {
    0% { box-shadow: 0 0 10px var(--primary-glow); }
    100% { box-shadow: 0 0 22px rgba(243, 18, 58, 0.6); }
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
    background: linear-gradient(to right, #fff, var(--text-secondary));
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .title-sub {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 2px;
  }

  /* Segment Tabs view switcher */
  .view-switcher-tabs {
    display: flex;
    background-color: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 4px;
  }

  .tab-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 8px;
    font-family: var(--sans);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  @media (max-width: 900px) {
    .tab-btn {
      flex: 1;
      justify-content: center;
    }
  }

  .tab-btn:hover {
    color: var(--text-primary);
  }

  .tab-btn.active {
    background-color: var(--bg-surface-elevated);
    color: #fff;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
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

  .sort-order-toggle {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all var(--transition-normal);
  }

  .sort-order-toggle:hover {
    border-color: rgba(243, 18, 58, 0.4);
    background-color: rgba(243, 18, 58, 0.05);
    color: #fff;
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
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 80px 20px;
    text-align: center;
  }

  .error-state,
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

  .error-state h3,
  .empty-state h3 {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .error-state p,
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
    border-color: rgba(243, 18, 58, 0.4);
    background-color: rgba(243, 18, 58, 0.05);
    color: #fff;
    box-shadow: 0 4px 15px rgba(243, 18, 58, 0.15);
  }

  /* Footer */
  footer {
    border-top: 1px solid var(--border-color);
    padding: 24px 0 40px;
    margin-top: 60px;
    text-align: center;
  }

  .footer-text {
    font-size: 0.8rem;
    color: var(--text-muted);
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.5;
  }
</style>
