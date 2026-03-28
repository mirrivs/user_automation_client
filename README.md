# User Automation Client

## Quick Overview
User Automation Client is a desktop automation agent that runs predefined "behaviours" such as work simulation, browsing, email handling, and attack simulation tasks.

At runtime the app:
- loads `config.yml`
- validates the registered behaviours
- starts the tray UI and the automation manager
- keeps an idle behaviour cycle running
- can also receive commands and config updates from the automation server

## Main Runtime Flow
1. `main.py` starts the application.
2. `app_config.py` loads the YAML config.
3. `user_automation_manager.py` manages the background cycle and server connection.
4. `behaviour_manager.py` builds the registered behaviour set and decides which ones are available.
5. A selected behaviour runs as a `BaseBehaviour` thread and uses the shared cleanup/cancellation infrastructure.

## Core Concepts
### Behaviours
Behaviours are the units of automation. Each one has:
- an `id`
- display metadata
- a runtime `is_available()` check
- a `run_behaviour()` implementation

The registry in `behaviour/registry.py` is the source of truth for which behaviours exist.

### Availability
Final behaviour availability is determined by:
- runtime availability from `is_available()`
- config enable/disable state from `automation.behaviour_toggles`

A behaviour is available only if both are true.

### Cancellation
Cancellation is cooperative.
- `BaseBehaviour` owns a shared cancel event.
- `lib/cancellable_futures` makes sleeps and task execution cancellation-aware.
- `lib/selenium/cancellable_wait.py` makes Selenium waits cancellation-aware.
- `lib/selenium/selenium_driver.py` contains shared Selenium helpers with cancellation checks.

### Cleanup
`cleanup_manager.py` owns cleanup tasks registered during behaviour execution.
Tasks are executed in reverse order when a behaviour ends or is cancelled.

## Important Files
- `main.py`: application entry point
- `app_config.py`: config loading/saving access
- `user_automation_manager.py`: top-level runtime orchestration
- `behaviour_manager.py`: behaviour discovery, availability, queueing, and execution
- `cleanup_manager.py`: task-based cleanup handling
- `behaviour/behaviour.py`: base behaviour thread implementation
- `behaviour/registry.py`: registered behaviour classes and registry helpers
- `behaviour/ids.py`: shared behaviour ID type
- `src/config/config_handler.py`: config helpers and toggle merging
- `src/config/models/config.py`: typed config model
- `lib/selenium/`: Selenium helpers and clients
- `lib/autogui/`: non-Selenium UI automation helpers
- `src/gui/`: tray and popup UI

## Config Notes
The main config file is `config.yml`.

Important sections:
- `app`: server endpoints and app-level settings
- `automation.general`: shared behaviour runtime config
- `automation.idle_cycle`: idle scheduling config
- `automation.behaviour_toggles`: enable/disable per behaviour
- `automation.behaviours`: per-behaviour config payloads

Missing behaviour toggles default to enabled.

## Typical Development Areas
- Add a new behaviour: create a class in `behaviours/`, give it a typed `id`, then register it in `behaviour/registry.py`.
- Change availability rules: update `is_available()` or the config toggle logic in `behaviour_manager.py`.
- Change config structure: update `src/config/models/config.py` and `src/config/config_handler.py`.
- Change Selenium interactions: update `lib/selenium/`.
- Change tray or popup UI: update `src/gui/`.
