<script lang="ts">
  import { 
    Lock, 
    Unlock, 
    CheckCircle, 
    AlertTriangle, 
    RefreshCw, 
    Eye, 
    EyeOff, 
    Database 
  } from 'lucide-svelte';

  // Svelte 5 Props using Runes
  let { 
    status, 
    onConfigUpdated 
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
  let username = $state('');
  let password = $state('');
  let showPassword = $state(false);
  let isLoading = $state(false);
  let errorMessage = $state('');
  let successMessage = $state('');
  let isPanelOpen = $state(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    isLoading = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          iracing_username: username,
          iracing_password: password,
          mock_mode: false // try to disable mock mode
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to authenticate with iRacing API.');
      }

      successMessage = 'Successfully synced with iRacing! Mock mode disabled.';
      username = '';
      password = '';
      onConfigUpdated();
      
      // Auto close panel after delay
      setTimeout(() => {
        isPanelOpen = false;
        successMessage = '';
      }, 3000);

    } catch (err: any) {
      errorMessage = err.message || 'An error occurred during sync.';
    } finally {
      isLoading = false;
    }
  }

  async function handleEnableMockMode() {
    isLoading = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mock_mode: true
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to enable mock mode.');
      }

      successMessage = 'Switched to Mock Mode successfully.';
      onConfigUpdated();
      
      setTimeout(() => {
        successMessage = '';
      }, 3000);

    } catch (err: any) {
      errorMessage = err.message || 'An error occurred.';
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="oauth-panel glass-panel">
  <button 
    class="panel-trigger" 
    onclick={() => isPanelOpen = !isPanelOpen}
  >
    <div class="trigger-left">
      <Database size={18} class={status?.mock_mode ? 'text-cyan' : 'text-green'} />
      <span class="trigger-title">Data Connection Status:</span>
      {#if !status}
        <span class="status-badge connecting">Connecting...</span>
      {:else if status.mock_mode}
        <span class="status-badge mock">Mock Mode (Simulated Data)</span>
      {:else}
        <span class="status-badge live">Live Sync Active</span>
      {/if}
    </div>
    <span class="trigger-action">{isPanelOpen ? 'Hide Panel' : 'Configure Sync'}</span>
  </button>

  {#if isPanelOpen}
    <div class="panel-content">
      <div class="info-banner">
        {#if status?.mock_mode}
          <div class="banner-box mock-banner">
            <AlertTriangle size={18} />
            <div class="banner-text">
              <p class="banner-title">Mock Mode Active</p>
              <p>We are serving pre-packaged, extremely authentic race schedules. To fetch live up-to-the-minute data from your active iRacing account, enter your credentials below.</p>
            </div>
          </div>
        {:else}
          <div class="banner-box live-banner">
            <CheckCircle size={18} />
            <div class="banner-text">
              <p class="banner-title">Connected to iRacing API</p>
              <p>Live schedules are syncing successfully for account <strong>{status?.username}</strong>. You can switch back to Mock Mode anytime.</p>
            </div>
          </div>
        {/if}
      </div>

      {#if status?.mock_mode}
        <form onsubmit={handleSubmit} class="sync-form">
          <div class="form-group">
            <label for="username">iRacing Email / Username</label>
            <input 
              type="email" 
              id="username" 
              bind:value={username}
              placeholder="your-email@example.com" 
              required
              disabled={isLoading}
            />
          </div>

          <div class="form-group">
            <label for="password">iRacing Password</label>
            <div class="password-input-wrapper">
              <input 
                type={showPassword ? 'text' : 'password'} 
                id="password" 
                bind:value={password}
                placeholder="••••••••" 
                required
                disabled={isLoading}
              />
              <button 
                type="button" 
                class="password-toggle"
                onclick={() => showPassword = !showPassword}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {#if showPassword}
                  <EyeOff size={16} />
                {:else}
                  <Eye size={16} />
                {/if}
              </button>
            </div>
          </div>

          {#if errorMessage}
            <div class="message error-message">
              <AlertTriangle size={16} />
              <span>{errorMessage}</span>
            </div>
          {/if}

          {#if successMessage}
            <div class="message success-message">
              <CheckCircle size={16} />
              <span>{successMessage}</span>
            </div>
          {/if}

          <div class="button-row">
            <button 
              type="submit" 
              class="btn-primary" 
              disabled={isLoading}
            >
              {#if isLoading}
                <RefreshCw size={16} class="spinner" />
                <span>Authenticating...</span>
              {:else}
                <Lock size={16} />
                <span>Connect & Sync Live API</span>
              {/if}
            </button>
          </div>
        </form>
      {:else}
        <div class="live-controls">
          {#if successMessage}
            <div class="message success-message">
              <CheckCircle size={16} />
              <span>{successMessage}</span>
            </div>
          {/if}
          
          <button 
            type="button" 
            class="btn-secondary" 
            onclick={handleEnableMockMode}
            disabled={isLoading}
          >
            {#if isLoading}
              <RefreshCw size={16} class="spinner" />
              <span>Disconnecting...</span>
            {:else}
              <Unlock size={16} />
              <span>Disconnect & Re-enable Mock Mode</span>
            {/if}
          </button>
        </div>
      {/if}
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

  .status-badge.mock {
    background-color: rgba(0, 240, 255, 0.1);
    color: var(--accent-cyan);
    border: 1px solid rgba(0, 240, 255, 0.2);
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

  .mock-banner {
    background-color: rgba(0, 240, 255, 0.05);
    border: 1px solid rgba(0, 240, 255, 0.15);
    color: #e2f8ff;
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

  /* Form layouts */
  .sync-form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    align-items: end;
  }

  @media (max-width: 768px) {
    .sync-form {
      grid-template-columns: 1fr;
    }
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-group label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
    letter-spacing: 0.03em;
  }

  .form-group input {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 10px 14px;
    border-radius: 8px;
    font-family: var(--sans);
    font-size: 0.9rem;
    transition: all var(--transition-normal);
  }

  .form-group input:focus {
    outline: none;
    border-color: rgba(243, 18, 58, 0.4);
    box-shadow: 0 0 10px rgba(243, 18, 58, 0.08);
  }

  .password-input-wrapper {
    position: relative;
    width: 100%;
  }

  .password-input-wrapper input {
    width: 100%;
    padding-right: 40px;
  }

  .password-toggle {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .password-toggle:hover {
    color: var(--text-primary);
  }

  .button-row {
    grid-column: span 2;
    display: flex;
    justify-content: flex-end;
    margin-top: 8px;
  }

  @media (max-width: 768px) {
    .button-row {
      grid-column: span 1;
    }
  }

  /* Feedback messages */
  .message {
    grid-column: span 2;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    font-weight: 500;
    padding: 10px 14px;
    border-radius: 6px;
  }

  @media (max-width: 768px) {
    .message {
      grid-column: span 1;
    }
  }

  .error-message {
    background-color: rgba(243, 18, 58, 0.08);
    border: 1px solid rgba(243, 18, 58, 0.25);
    color: #ffb3bf;
  }

  .success-message {
    background-color: rgba(57, 255, 20, 0.08);
    border: 1px solid rgba(57, 255, 20, 0.25);
    color: #b3ffb3;
  }

  .text-cyan {
    color: var(--accent-cyan);
  }

  .text-green {
    color: var(--accent-green);
  }

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    100% { transform: rotate(360deg); }
  }

  .live-controls {
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
</style>
