## ADDED Requirements

### Requirement: Daily candidate ledger

The system SHALL produce `data/github-project-digest/candidates/YYYY-MM-DD.jsonl` for each completed daily discovery run, with one valid JSON object per non-empty line and one record per canonical repository.

#### Scenario: Successful daily ledger creation

- **WHEN** a daily run completes with discovered repositories
- **THEN** the system writes a date-keyed JSONL ledger
- **AND** every non-empty line parses as one JSON object
- **AND** each canonical repository appears exactly once

### Requirement: Candidate record contract

Each candidate record MUST contain `date`, `repo`, `url`, `lanes`, `sources`, `status`, `verified`, and `reason`. Available GitHub facts such as Stars, Forks, license, archived state, and pushed date SHALL be recorded when verified; unavailable facts MUST be `null` rather than guessed.

#### Scenario: Candidate observed during degraded API access

- **WHEN** a repository is discovered but a GitHub fact cannot be verified because live API access is degraded
- **THEN** the ledger preserves the candidate with the unavailable fact set to `null`
- **AND** `verified` remains false until an allowed GitHub fact source is checked
- **AND** the reason identifies the verification limitation or fallback used

### Requirement: Canonical deduplication

The ledger utility SHALL deduplicate repository identifiers case-insensitively and SHALL preserve the union of discovery lanes and sources for duplicate hits.

#### Scenario: Repository found by multiple searches

- **WHEN** scanner inputs contain `Owner/Repo` and `owner/repo` from different lanes or sources
- **THEN** the output contains one candidate record for that repository
- **AND** the record contains every distinct lane and source in deterministic order

### Requirement: Safe deterministic output

The ledger utility MUST use only the Python standard library, SHALL emit records in deterministic repository order, and MUST NOT replace an existing valid ledger when any input is malformed.

#### Scenario: Malformed scanner input

- **WHEN** any supplied scanner result is not valid JSON or not a JSON array of repository objects
- **THEN** the utility exits with a non-zero status
- **AND** the destination ledger remains unchanged

### Requirement: Candidate disposition

Every candidate SHALL use one of `discovered`, `shortlisted`, `rejected`, `primary`, or `extra` as its status. A rejected, primary, or extra record MUST include a non-empty reason, and published primary and extra projects SHALL also be recorded in `history.jsonl` with a matching `role`.

#### Scenario: Extra discovery is published

- **WHEN** a candidate is included in the daily report as an extra discovery
- **THEN** its candidate record has `status: extra`, `verified: true`, and a non-empty reason
- **AND** `history.jsonl` contains the repository with `role: extra`

#### Scenario: Candidate is rejected

- **WHEN** a reviewed candidate fails the quality or risk threshold
- **THEN** its candidate record has `status: rejected`
- **AND** its reason states the material rejection cause
