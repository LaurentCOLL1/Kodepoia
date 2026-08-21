from __future__ import annotations

import threading
from typing import Protocol


class KillableProcess(Protocol):
    def poll(self) -> int | None: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...


class KillSwitch:
    """Process-wide emergency stop shared by protected execution services.

    The switch is deterministic and model-independent. Once triggered it rejects
    new registrations and terminates every process currently registered with it.
    A human-controlled reset is required before new work can start.
    """

    def __init__(self) -> None:
        self._triggered = threading.Event()
        self._lock = threading.RLock()
        self._processes: set[KillableProcess] = set()

    @property
    def triggered(self) -> bool:
        return self._triggered.is_set()

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._processes)

    def register(self, process: KillableProcess) -> None:
        with self._lock:
            if self.triggered:
                self._stop_process(process)
                raise RuntimeError("Kodepoia kill switch is active")
            self._processes.add(process)

    def unregister(self, process: KillableProcess) -> None:
        with self._lock:
            self._processes.discard(process)

    def trigger(self) -> int:
        """Activate the stop and terminate all known processes.

        Returns the number of processes that were active when the switch fired.
        """
        self._triggered.set()
        with self._lock:
            processes = tuple(self._processes)
        for process in processes:
            self._stop_process(process)
        return len(processes)

    def reset(self) -> None:
        with self._lock:
            if self._processes:
                raise RuntimeError("Cannot reset kill switch while processes remain registered")
            self._triggered.clear()

    @staticmethod
    def _stop_process(process: KillableProcess) -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
        except OSError:
            return
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
