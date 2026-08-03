## 1. Failing-first redirect contracts

- [x] 1.1 Add failing Vitest coverage for selecting the newest valid monthly, weekly, daily and radar detail directory, ignoring unrelated directories, and rejecting a type without a valid `index.html`.
- [x] 1.2 Add failing assertions for deterministic `_redirects` output containing exactly eight `302` rules for slash and non-slash entrypoints without matching dated detail routes.
- [x] 1.3 Add failing route contract tests requiring all four `index.astro` files to return `302` redirects from the existing latest-report loaders and to stop rendering report or archive content.

## 2. Cloudflare redirect generation

- [x] 2.1 Implement a dependency-free Node module that validates built detail directories, selects each type's newest slug and renders the eight exact Cloudflare rules.
- [x] 2.2 Add a CLI entrypoint that writes only `dist/_redirects`, emits a useful success summary and fails with the missing report type when generation is incomplete.
- [x] 2.3 Update the production build command and a focused check command so redirect generation and verification run automatically after Astro output is created.

## 3. Undated Astro entrypoints

- [x] 3.1 Replace the monthly index content with a `302` redirect to `loadMonthlyReports()[0]` and a build-time invariant for the required latest report.
- [x] 3.2 Replace the weekly and daily index archive pages with `302` redirects to the first report returned by their existing loaders.
- [x] 3.3 Replace the radar index archive page with a `302` redirect to the first radar report while preserving all dated radar routes.
- [x] 3.4 Update period-navigation regression coverage so an unresolved time-anchor target still links to the undated type entrypoint, whose contract now redirects to the latest dated page.

## 4. Verification

- [x] 4.1 Run the focused redirect generator and route contract tests and confirm the new tests complete a red-green cycle.
- [x] 4.2 Run the full Vitest suite, Astro check, monthly/radar build checks, production build and strict OpenSpec validation.
- [x] 4.3 Inspect `dist/_redirects` and built detail pages to confirm current latest targets, eight exact `302` rules, unchanged dated pages and no generated redirect loops.
- [x] 4.4 Exercise all four undated entrypoints in a browser or HTTP preview and confirm navigation reaches the expected latest dated URL with the address bar updated.
