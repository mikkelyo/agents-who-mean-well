"""Run candidate code against hidden tests in a throwaway subprocess."""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

TRACE_LIMIT = 2000


@dataclass(frozen=True)
class VerifyResult:
    """Whether the candidate passed, and the trace explaining it if not."""

    passed: bool
    trace: str


def _sandboxed(command: list[str]) -> list[str]:
    """Wrap the command in a network-less namespace where the kernel allows one."""
    if sys.platform == "linux" and shutil.which("unshare"):
        return ["unshare", "--map-root-user", "--net", *command]
    return command


async def verify(*, code: str, tests: str, timeout: float = 10.0) -> VerifyResult:
    """Execute code plus tests in a subprocess and report pass or failure."""
    with tempfile.TemporaryDirectory() as workdir:
        script = Path(workdir) / "candidate.py"
        script.write_text(f"{code}\n\n{tests}\n")
        process = await asyncio.create_subprocess_exec(
            *_sandboxed([sys.executable, str(script)]),
            cwd=workdir,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout)
        except TimeoutError:
            process.kill()
            await process.wait()
            return VerifyResult(passed=False, trace=f"Timed out after {timeout}s.")

    # The tail carries the assertion; the head is import noise.
    return VerifyResult(
        passed=process.returncode == 0,
        trace=stderr.decode(errors="replace")[-TRACE_LIMIT:],
    )
