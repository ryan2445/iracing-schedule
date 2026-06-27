<script lang="ts">
  import { 
    CheckCircle, 
    RefreshCw, 
    Database 
  } from 'lucide-svelte';

  // Svelte 5 Props using Runes
  let { 
    status 
  } = $props<{
    status: {
      status: string;
      mock_mode: boolean;
      username: string;
      time_utc: string;
    } | null;
    onConfigUpdated: () => void;
  }>();

  // Svelte 5 State Runes
  let isPanelOpen = $state(false);

  // PDF Parser Analytics Interfaces
  interface CacheEndpoint {
    endpoint: string;
    count: number;
    last_fetched: string;
    total_bytes: number;
  }

  interface CacheHistoryEntry {
    id: number;
    endpoint: string;
    fetched_at: string;
    size_bytes: number;
  }

  interface CacheStatus {
    db_path: string;
    db_size_bytes: number;
    total_snapshots: number;
    endpoints: CacheEndpoint[];
    recent_history: CacheHistoryEntry[];
  }

  let cacheStatus = $state<CacheStatus | null>(null);
  let isFetchingCache = $state(false);

  async function fetchCacheStatus() {
    isFetchingCache = true;
    try {
      const response = await fetch('http://localhost:8000/api/cache/status');
      if (response.ok) {
        cacheStatus = await response.json();
      }
    } catch (e) {
      console.error('Failed to load engine diagnostics', e);
    } finally {
      isFetchingCache = false;
    }
  }

  // Reload cache status whenever panel opens or status changes
  $effect(() => {
    if (isPanelOpen) {
      fetchCacheStatus();
    }
  });
</script>

<div class="oauth-panel glass-panel">
  <button 
    class="panel-trigger" 
    onclick={() => isPanelOpen = !isPanelOpen}
  >
    <div class="trigger-left">
      <Database size={18} class="text-green" />
      <span class="trigger-title">Schedule Data Source:</span>
      {#if !status}
        <span class="status-badge connecting">Loading PDF...</span>
      {:else}
        <span class="status-badge live">PDF Parser Engine (Active)</span>
      {/if}
    </div>
    <span class="trigger-action">{isPanelOpen ? 'Hide Panel' : 'View PDF Engine Logs'}</span>
  </button>

  {#if isPanelOpen}
    <div class="panel-content">
      <div class="info-banner">
        <div class="banner-box live-banner">
          <CheckCircle size={18} />
          <div class="banner-text">
            <p class="banner-title">Static PDF Schedule Active</p>
            <p>Schedules are parsed dynamically from <strong>{status?.username || 'iracing_season_3_schedule.pdf'}</strong>. This provides 100% accurate session start times, configurations, and license tiers without calling rate-limited iRacing APIs.</p>
          </div>
        </div>
      </div>

      <!-- PDF Persistent Parser Section -->
      <div class="cache-diagnostic-panel">
        <div class="cache-header">
          <div class="cache-title">
            <Database size={15} class="text-primary-color" />
            <span>PDF Schedule Engine Analytics</span>
          </div>
          <button 
            type="button" 
            class="btn-icon-only {isFetchingCache ? 'spinning' : ''}" 
            onclick={fetchCacheStatus} 
            title="Refresh engine stats"
            disabled={isFetchingCache}
          >
            <RefreshCw size={13} />
          </button>
        </div>

        {#if cacheStatus}
          <div class="cache-meta-grid">
            <div class="cache-meta-card">
              <span class="meta-label">Total Loaded Series</span>
              <span class="meta-value">{cacheStatus.total_snapshots}</span>
            </div>
            <div class="cache-meta-card">
              <span class="meta-label">Source PDF File Size</span>
              <span class="meta-value">{(cacheStatus.db_size_bytes / 1024).toFixed(1)} KB</span>
            </div>
          </div>

          {#if cacheStatus.endpoints.length > 0}
            <div class="cache-endpoints-list">
              <p class="section-subtitle">Data Loading Details</p>
              <div class="cache-table-container">
                <table class="cache-table">
                  <thead>
                    <tr>
                      <th>Engine Module</th>
                      <th class="text-center">Series</th>
                      <th>Last Parsed (UTC)</th>
                      <th class="text-right">Execution Mode</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each cacheStatus.endpoints as ep}
                      <tr>
                        <td class="font-mono text-ellipsis" title={ep.endpoint}>{ep.endpoint}</td>
                        <td class="text-center font-bold">{ep.count}</td>
                        <td>{new Date(ep.last_fetched).toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit', second:'2-digit'})} {new Date(ep.last_fetched).toLocaleDateString()}</td>
                        <td class="text-right" style="color: #10b981; font-weight: 600;">In-Memory Only</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          {/if}

          {#if cacheStatus.recent_history.length > 0}
            <div class="cache-history-list">
              <p class="section-subtitle">Parser Logs</p>
              <div class="history-timeline-container">
                <ul class="history-timeline">
                  {#each cacheStatus.recent_history as item}
                    <li class="history-item">
                      <span class="history-dot"></span>
                      <div class="history-content">
                        <span class="history-time">
                          {new Date(item.fetched_at).toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit', second:'2-digit'})}
                        </span>
                        <span class="history-endpoint font-mono">{item.endpoint}</span>
                        <span class="badge size-badge" style="background-color: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.2); color: #10b981;">Optimal</span>
                      </div>
                    </li>
                  {/each}
                </ul>
              </div>
            </div>
          {/if}
        {:else}
          <p class="cache-loading-text">Loading engine diagnostics...</p>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .oauth-panel {
    border-radius: 12px;
    margin-bottom: 24px;
    overflow: hidden;
    padding: 0;
  }

  .panel-trigger {
    width: 100%;
    background: none;
    border: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    cursor: pointer;
    font-family: var(--sans);
    transition: background-color var(--transition-fast);
  }

  .panel-trigger:hover {
    background-color: rgba(255, 255, 255, 0.03);
  }

  .trigger-left {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .trigger-title {
    color: var(--text-secondary);
  }

  .status-badge {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
  }

  .status-badge.connecting {
    background-color: rgba(255, 255, 255, 0.05);
    color: var(--text-muted);
  }

  .status-badge.live {
    background-color: rgba(57, 255, 20, 0.1);
    color: var(--accent-green);
    border: 1px solid rgba(57, 255, 20, 0.2);
  }

  .trigger-action {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--primary);
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .panel-content {
    border-top: 1px solid var(--border-color);
    padding: 20px;
    background-color: rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    gap: 16px;
    animation: slideDown 0.2s ease-out;
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .info-banner {
    width: 100%;
  }

  .banner-box {
    display: flex;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 0.85rem;
    line-height: 1.45;
  }

  .live-banner {
    background-color: rgba(57, 255, 20, 0.05);
    border: 1px solid rgba(57, 255, 20, 0.15);
    color: #f0fff4;
  }

  .banner-title {
    font-weight: 700;
    margin-bottom: 2px;
    text-transform: uppercase;
    font-size: 0.8rem;
    letter-spacing: 0.02em;
  }

  .banner-text p {
    color: var(--text-secondary);
  }

  .banner-text strong {
    color: var(--text-primary);
  }

  :global(.text-green) {
    color: var(--accent-green);
  }

  .spinning {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    100% { transform: rotate(360deg); }
  }

  /* Cache Diagnostic Panel Styles */
  .cache-diagnostic-panel {
    margin-top: 16px;
    border-top: 1px solid var(--border-color);
    padding-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .cache-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .cache-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-primary);
    letter-spacing: 0.03em;
  }

  .btn-icon-only {
    background: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    width: 26px;
    height: 26px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .btn-icon-only:hover {
    color: #fff;
    border-color: var(--text-muted);
  }

  .cache-meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .cache-meta-card {
    background-color: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .meta-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.03em;
  }

  .meta-value {
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text-primary);
  }

  .section-subtitle {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.04em;
    margin-bottom: 6px;
  }

  .cache-table-container {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    background-color: rgba(0, 0, 0, 0.1);
  }

  .cache-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
    text-align: left;
  }

  .cache-table th, .cache-table td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color);
  }

  .cache-table th {
    background-color: rgba(255, 255, 255, 0.01);
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.65rem;
    letter-spacing: 0.02em;
  }

  .cache-table tr:last-child td {
    border-bottom: none;
  }

  .font-mono {
    font-family: monospace;
    font-size: 0.75rem;
  }

  .font-bold {
    font-weight: 700;
  }

  .text-center {
    text-align: center;
  }

  .text-right {
    text-align: right;
  }

  .cache-loading-text {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-align: center;
    padding: 16px 0;
  }

  /* History Timeline */
  .history-timeline-container {
    max-height: 180px;
    overflow-y: auto;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 10px 14px;
    background-color: rgba(0, 0, 0, 0.1);
  }

  .history-timeline {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .history-item {
    display: flex;
    align-items: center;
    gap: 10px;
    position: relative;
  }

  .history-dot {
    width: 6px;
    height: 6px;
    background-color: var(--primary);
    box-shadow: 0 0 6px var(--primary-glow);
    border-radius: 50%;
    flex-shrink: 0;
  }

  .history-content {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    width: 100%;
    overflow: hidden;
  }

  .history-time {
    color: var(--text-muted);
    font-weight: 600;
    flex-shrink: 0;
  }

  .history-endpoint {
    color: #e2f8ff;
    flex-grow: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .size-badge {
    font-size: 0.65rem;
    padding: 1px 6px;
    border-radius: 4px;
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    flex-shrink: 0;
  }
</style>
