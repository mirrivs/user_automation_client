# LLM Overview

## Purpose
This file is for code-reading agents and contributors who need a fast mental model of the repository.
It is intentionally practical and repo-specific.

## High-Level Architecture
### Entry and orchestration
- `main.py`
  Starts the app, validates the behaviour registry, creates `UserAutomationManager`, and launches the tray UI.
- `user_automation_manager.py`
  Owns the long-running runtime loops:
  - idle behaviour cycle
  - server authentication and websocket handling
  - config merge/save flow
- `behaviour_manager.py`
  Owns behaviour prototypes, availability computation, queueing, and starting/stopping behaviour threads.

### Behaviour system
- `behaviour/behaviour.py`
  Defines `BaseBehaviour`, which is a `threading.Thread` with:
  - cooperative cancellation
  - shared cancellable executor pool
  - cleanup integration
- `behaviour/registry.py`
  Registry of all behaviour classes. Also provides:
  - `get_registered_behaviour_ids()`
  - `get_default_behaviour_toggles()`
  - `validate_behaviour_registry()`
- `behaviour/ids.py`
  Shared `BehaviourId` literal alias used across the behaviour system.
- `behaviours/`
  Concrete behaviour implementations.

### Config system
- `app_config.py`
  Loads `config.yml` and exposes the in-memory config object.
- `src/config/models/config.py`
  TypedDict-based config model.
- `src/config/config_handler.py`
  YAML load/save plus helpers for automation config and behaviour toggles.

### UI
- `src/gui/system_tray.py`
  System tray integration and popup ownership.
- `src/gui/popup_window.py`
  Main popup window that displays available behaviours and controls.

### Automation helpers
- `lib/selenium/`
  Selenium-specific logic.
  Main files:
  - `selenium_driver.py`: shared Selenium helpers and cancellation-aware actions
  - `cancellable_wait.py`: cancellation-aware `WebDriverWait`
  - `selenium_controller.py`: higher-level browser workflows
  - `email_web_client.py`: email-client-specific browser interactions
- `lib/autogui/`
  Native GUI automation helpers used outside Selenium.
- `lib/cancellable_futures/`
  Cooperative cancellation primitives for sleeps and threaded task execution.
- `lib/email_manager/`
  Email templates and logic for generated conversations.

## Behaviour Execution Model
1. `BehaviourManager` instantiates behaviour prototypes for metadata and availability checks.
2. A behaviour becomes available only if:
   - `behaviour_class.is_available()` is true
   - config toggle is enabled
3. When started, a behaviour runs as its own thread.
4. That thread binds a `CancellableThreadPoolExecutor` to itself so shared helpers can observe cancellation.
5. On stop or completion, cleanup tasks are run in reverse order.

## Cleanup Design
- `cleanup_manager.py` now uses explicit `CleanupTask` objects instead of anonymous dict payloads.
- `CleanupManager.add_cleanup_task(...)` returns a task handle.
- `CleanupManager.run_task(...)` executes one task early.
- `CleanupManager.run_cleanup()` executes remaining tasks in LIFO order.
- `BaseBehaviour.register_cleanup(...)` is a thin wrapper over the cleanup manager.

## Availability Rules
Availability is not only registry-based and not only config-based.
Final availability is:
`runtime_available and config_enabled`

Config toggles live under:
`automation.behaviour_toggles`

Missing toggle keys default to `True`.

## Important Repo Conventions
- The registry is the source of truth for which behaviours exist.
- Behaviour IDs are class attributes and should stay stable.
- New Selenium interactions should prefer shared helpers in `lib/selenium/selenium_driver.py`.
- New cleanup logic should use `CleanupManager` task handles instead of ad-hoc callbacks.
- When changing config structure, update both the TypedDict model and config helper logic.

## Common Edit Targets
### Add a new behaviour
1. Create a class in `behaviours/`.
2. Give it a typed `id: BehaviourId`.
3. Register it in `behaviour/registry.py`.
4. If it needs config, update the config model/helpers if necessary.

### Change availability or enable/disable logic
- `behaviour_manager.py`
- `behaviour/registry.py`
- `src/config/config_handler.py`
- `src/config/models/config.py`

### Change email/browser automation
- `lib/selenium/email_web_client.py`
- `lib/selenium/selenium_controller.py`
- `lib/selenium/selenium_driver.py`

### Change startup/runtime orchestration
- `main.py`
- `user_automation_manager.py`
- `behaviour_manager.py`

## Current Rough Edges
These are useful to know before editing:
- Some Selenium and behaviour code still uses direct `.click()` / raw driver calls instead of shared helper methods.
- Some unfinished behaviours exist, especially Office-related ones.
- README-level architecture used to be stale/garbled; prefer this file plus the current code over old assumptions.
