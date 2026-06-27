<script lang="ts">
  import { 
    Search, 
    Filter, 
    X, 
    SlidersHorizontal, 
    ShieldCheck, 
    Settings2 
  } from 'lucide-svelte';

  interface License {
    name: string;
    id: number;
  }

  // Svelte 5 Props using runes
  let { 
    search = $bindable(''), 
    selectedCategories = $bindable([]), 
    selectedLicenses = $bindable([]), 
    fixedOnly = $bindable(false),
    availableCategories = [],
    availableLicenses = []
  } = $props<{
    search: string;
    selectedCategories: string[];
    selectedLicenses: string[];
    fixedOnly: boolean;
    availableCategories: string[];
    availableLicenses: License[];
  }>();

  // Handle category toggle
  function toggleCategory(category: string) {
    if (selectedCategories.includes(category)) {
      selectedCategories = selectedCategories.filter((c: string) => c !== category);
    } else {
      selectedCategories = [...selectedCategories, category];
    }
  }

  // Handle license toggle
  function toggleLicense(licenseName: string) {
    if (selectedLicenses.includes(licenseName)) {
      selectedLicenses = selectedLicenses.filter((l: string) => l !== licenseName);
    } else {
      selectedLicenses = [...selectedLicenses, licenseName];
    }
  }

  function clearAllFilters() {
    search = '';
    selectedCategories = [];
    selectedLicenses = [];
    fixedOnly = false;
  }

  // Derived check to see if any filter is active
  const hasActiveFilters = $derived(
    search !== '' || selectedCategories.length > 0 || selectedLicenses.length > 0 || fixedOnly
  );
</script>

<div class="filters-panel glass-panel">
  <!-- Top header row -->
  <div class="filters-header">
    <div class="header-left">
      <SlidersHorizontal size={18} class="text-primary-color" />
      <h3>Dashboard Filters</h3>
    </div>
    {#if hasActiveFilters}
      <button class="clear-all-btn" onclick={clearAllFilters}>
        <X size={14} />
        <span>Clear All</span>
      </button>
    {/if}
  </div>

  <!-- Main filters layout -->
  <div class="filters-grid">
    <!-- Search Bar -->
    <div class="filter-item search-box-container">
      <label for="search" class="filter-label">Search Series, Track or Car</label>
      <div class="search-input-wrapper">
        <Search class="search-icon" size={16} />
        <input 
          id="search"
          type="text" 
          placeholder="e.g. IMSA, Spa, GT3, Mazda..." 
          bind:value={search}
        />
        {#if search}
          <button class="clear-search-btn" onclick={() => search = ''} aria-label="Clear search">
            <X size={14} />
          </button>
        {/if}
      </div>
    </div>

    <!-- Category Filters -->
    <div class="filter-item">
      <span class="filter-label">Race Categories</span>
      <div class="tags-row">
        {#each availableCategories as category}
          <button 
            class="filter-tag {category.toLowerCase().replace(' ', '-')} {selectedCategories.includes(category) ? 'selected' : ''}"
            onclick={() => toggleCategory(category)}
          >
            {category}
          </button>
        {/each}
      </div>
    </div>

    <!-- License Level Filters -->
    <div class="filter-item">
      <span class="filter-label">License Requirements</span>
      <div class="tags-row">
        {#each availableLicenses as lic (lic.id)}
          <button 
            class="badge badge-license {lic.name.toLowerCase().replace(' ', '-')} filter-license-badge {selectedLicenses.includes(lic.name) ? 'selected' : ''}"
            onclick={() => toggleLicense(lic.name)}
          >
            {lic.name}
          </button>
        {/each}
      </div>
    </div>

    <!-- Setup Toggle Switch -->
    <div class="filter-item setup-toggle-container">
      <div class="toggle-info">
        <span class="filter-label no-margin">Fixed Setup Only</span>
        <span class="filter-desc">Filter by series where car setups cannot be modified</span>
      </div>
      <label class="toggle-switch">
        <input type="checkbox" bind:checked={fixedOnly} />
        <span class="toggle-slider"></span>
      </label>
    </div>
  </div>
</div>

<style>
  .filters-panel {
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 24px;
  }

  .filters-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 14px;
    margin-bottom: 18px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .header-left h3 {
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  .clear-all-btn {
    background: none;
    border: none;
    color: var(--primary);
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    transition: color var(--transition-fast);
  }

  .clear-all-btn:hover {
    color: var(--primary-hover);
  }

  /* Filters layout grid */
  .filters-grid {
    display: grid;
    grid-template-columns: 1.2fr 1fr 1fr auto;
    gap: 24px;
    align-items: end;
  }

  @media (max-width: 1024px) {
    .filters-grid {
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
  }

  @media (max-width: 650px) {
    .filters-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }
  }

  .filter-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
    height: 100%;
    justify-content: flex-end;
  }

  .filter-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
  }

  .filter-label.no-margin {
    margin: 0;
  }

  .filter-desc {
    font-size: 0.75rem;
    color: var(--text-muted);
  }

  /* Search bar input wrapper */
  .search-input-wrapper {
    position: relative;
    width: 100%;
  }

  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
  }

  .search-input-wrapper input {
    width: 100%;
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 10px 36px 10px 36px;
    font-family: var(--sans);
    font-size: 0.9rem;
    border-radius: 8px;
    transition: all var(--transition-normal);
  }

  .search-input-wrapper input:focus {
    outline: none;
    border-color: rgba(243, 18, 58, 0.4);
    box-shadow: 0 0 10px rgba(243, 18, 58, 0.08);
  }

  .clear-search-btn {
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

  .clear-search-btn:hover {
    color: var(--text-primary);
  }

  /* Filter tags and badges row */
  .tags-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .filter-tag {
    background-color: var(--bg-surface-elevated);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .filter-tag:hover {
    color: var(--text-primary);
    border-color: rgba(255,255,255,0.15);
  }

  /* Category specific tags selected states with theme matching borders */
  .filter-tag.selected {
    color: #ffffff;
    font-weight: 600;
  }

  .filter-tag.sports-car.selected { background-color: var(--color-sports-car); border-color: var(--color-sports-car); box-shadow: 0 0 10px rgba(255, 0, 127, 0.25); }
  .filter-tag.formula-car.selected { background-color: var(--color-formula-car); border-color: var(--color-formula-car); color: #000; box-shadow: 0 0 10px rgba(0, 240, 255, 0.25); }
  .filter-tag.oval.selected { background-color: var(--color-oval); border-color: var(--color-oval); color: #000; box-shadow: 0 0 10px rgba(255, 170, 0, 0.25); }
  .filter-tag.dirt-oval.selected { background-color: var(--color-dirt-oval); border-color: var(--color-dirt-oval); box-shadow: 0 0 10px rgba(139, 90, 43, 0.25); }
  .filter-tag.dirt-road.selected { background-color: var(--color-dirt-road); border-color: var(--color-dirt-road); color: #000; box-shadow: 0 0 10px rgba(0, 255, 102, 0.25); }

  /* License badges selector */
  .filter-license-badge {
    cursor: pointer;
    transition: all var(--transition-fast);
    opacity: 0.45;
  }

  .filter-license-badge:hover {
    opacity: 0.8;
  }

  .filter-license-badge.selected {
    opacity: 1;
    transform: scale(1.03);
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }

  /* Setup Switch Row */
  .setup-toggle-container {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 10px 14px;
    background-color: var(--bg-surface-elevated);
    border: 1px dashed var(--border-color);
    border-radius: 8px;
    width: 100%;
  }

  @media (max-width: 1024px) {
    .setup-toggle-container {
      grid-column: span 2;
    }
  }

  @media (max-width: 650px) {
    .setup-toggle-container {
      grid-column: span 1;
    }
  }

  .toggle-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
</style>
