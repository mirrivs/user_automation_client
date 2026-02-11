TODO: Implement new thread safe structure

┌─────────────────────────────────────────────────────┐
│              BaseBehaviour (Thread)                 │
│                                                     │
│  + _cancel_event = threading.Event()                │
│                                                     │
│  stop()  ← CHANGED                                  │
│    └── self._cancel_event.set()                     │
│        (cooperative instead of preemptive)          │
│                                                     │
│  + cpag = CancellablePyAutoGUI(_cancel_event)       │
│    (shared cancel event)                            │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│         CancellablePyAutoGUI                        │
│                                                     │
│  Wraps every pyautogui call with cancel check:      │
│                                                     │
│  def press(key):                                    │
│      if _cancel_event.is_set(): raise Cancelled     │
│      pag.press(key)                                 │
│                                                     │
│  def sleep(seconds):                                │
│      polls _cancel_event every 100ms                │
│      instead of blocking for full duration          │
│                                                     │
│  def write(text):                                   │
│      checks _cancel_event per character             │
│                                                     │
│  def locateOnScreen(image):                         │
│      checks _cancel_event between retry attempts    │
└─────────────────────────────────────────────────────┘

BehaviourManager                Behaviour Thread              CancellablePyAutoGUI
      │                              │                              │
      │ .start()                     │                              │
      ├─────────────────────────────>│                              │
      │                              │ cpag.hotkey("ctrl","n")      │
      │                              ├─────────────────────────────>│
      │                              │                   check flag │
      │                              │                   pag.hotkey │
      │                              │<─────────────────────────────│
      │                              │ cpag.sleep(2)                │
      │                              ├─────────────────────────────>│
      │                              │              check flag x20  │
      │                              │              (100ms chunks)  │
      │ .stop()                      │                              │
      ├──── sets cancel event ──────>│                              │
      │                              │              check flag ✗    │
      │                              │<──── CancellationError ──────│
      │                              │                              │
      │                              │ cleanup()                    │
      │                              │ thread exits                 │
      │<─────────────────────────────│                              │