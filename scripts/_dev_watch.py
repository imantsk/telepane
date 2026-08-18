"""Silent dev supervisor. Runs `python -m telepane`, restarting on any change under
src/telepane and healing crashes, resetting the screen before each launch so no
stale frame or watcher log leaks onto the TUI. Pressing `q` (clean exit 0) stops
it; Ctrl-C stops the supervisor."""

import subprocess
import sys
import time
from pathlib import Path

from watchfiles import watch

MIN_CLEAN_RUNTIME = 2.0  # a shorter run that exits is treated as a crash, not a quit

ROOT = Path(__file__).resolve().parent.parent
_venv_py = ROOT / ".venv" / "bin" / "python"
PY = str(_venv_py if _venv_py.exists() else sys.executable)
SRC = ROOT / "src" / "telepane"
RESET = "\033[?1049l\033[3J\033[H\033[2J"


def launch() -> subprocess.Popen:
    sys.stdout.write(RESET)
    sys.stdout.flush()
    return subprocess.Popen([PY, "-m", "telepane"], cwd=ROOT)


def stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> None:
    proc = launch()
    started = time.monotonic()
    try:
        for changes in watch(SRC, rust_timeout=1000, yield_on_timeout=True):
            if changes:
                stop(proc)
                proc = launch()
                started = time.monotonic()
            elif proc.poll() is not None:
                ran = time.monotonic() - started
                if proc.returncode == 0 and ran >= MIN_CLEAN_RUNTIME:
                    break  # clean quit (ran a while, then exited cleanly)
                time.sleep(0.5)  # a fast exit is a startup crash: heal, don't spin
                proc = launch()
                started = time.monotonic()
    except KeyboardInterrupt:
        pass
    finally:
        stop(proc)


if __name__ == "__main__":
    main()
