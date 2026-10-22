import faulthandler, signal, sys, os, time, functools, runpy
from pathlib import Path

LOG = open("/tmp/aura_diag.log", "w", buffering=1)
faulthandler.enable(file=LOG, all_threads=True)
faulthandler.register(signal.SIGUSR1, file=LOG, all_threads=True)
faulthandler.dump_traceback_later(20, repeat=True, file=LOG, exit=False)
print("[diag] start pid=" + str(os.getpid()), file=LOG, flush=True)

sys.path.insert(0, str(Path.home() / "aura_project"))

def wrap(cls, name):
    orig = getattr(cls, name, None)
    if orig is None or getattr(orig, "_diag", False):
        return
    @functools.wraps(orig)
    def w(self, *a, **kw):
        print("-> " + cls.__name__ + "." + name, file=LOG, flush=True)
        t = time.monotonic()
        try:
            r = orig(self, *a, **kw)
            print("<- " + cls.__name__ + "." + name + " dt=" + str(round(time.monotonic()-t, 2)) + "s", file=LOG, flush=True)
            return r
        except BaseException as e:
            print("XX " + cls.__name__ + "." + name + " " + type(e).__name__ + ": " + str(e), file=LOG, flush=True)
            raise
    w._diag = True
    setattr(cls, name, w)

try:
    from aura.agents.listener import Listener
    for n in ("listen", "_listen_impl", "pause", "resume", "set_last_response"):
        wrap(Listener, n)
except Exception as e:
    print("import Listener failed: " + str(e), file=LOG, flush=True)

try:
    from aura.agents.speaker import Speaker
    for n in ("say", "stop", "speak"):
        wrap(Speaker, n)
except Exception as e:
    print("import Speaker failed: " + str(e), file=LOG, flush=True)

import subprocess
_orig_run = subprocess.run
def _run(args, *a, **kw):
    print("subprocess.run -> " + repr(args), file=LOG, flush=True)
    t = time.monotonic()
    r = _orig_run(args, *a, **kw)
    print("subprocess.run <- rc=" + str(getattr(r, "returncode", "?")) + " dt=" + str(round(time.monotonic()-t, 2)) + "s", file=LOG, flush=True)
    return r
subprocess.run = _run

print("[diag] launching aura_main", file=LOG, flush=True)
runpy.run_path(str(Path.home() / "aura_project" / "aura_main.py"), run_name="__main__")
