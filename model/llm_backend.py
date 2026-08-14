"""Model access: call the logged-in `claude` CLI as a text completion backend.

Uses the account already authenticated for Claude Code, so no API key is needed. Each
call shells out to `claude -p --output-format json` with all tools disabled, and reads
the reply text plus the CLI's own cost/token envelope.

This module knows nothing about rules or genomes. The proposers in model/llm.py build
the prompts and parse the replies; `ClaudeCliLLM` only provides `_complete`, the call
budget, and usage accounting.
"""
import json
import re
import shutil
import subprocess
import sys
import time

DEFAULT_MODEL = "sonnet"   # passed to `claude --model`


def _extract_json(text: str):
    """Pull the first {...} object out of an LLM reply (tolerates code fences/prose)."""
    text = re.sub(r"```(?:json)?", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group(0)) if m else None


class ClaudeCliLLM:
    """Completion backend with a hard call budget.

    Subclasses build prompts and call `_complete`. `max_calls` caps how many times a
    run may reach the model; a proposer that hits the cap is expected to fall back to
    its parents rather than stall. A failed call (timeout, non-JSON, error envelope)
    returns "" and increments `fails` instead of raising, so one bad reply cannot end
    a campaign - but any run with fails > 0 is not a clean run, which is why `usage()`
    flags it loudly.
    """

    def __init__(self, model: str = DEFAULT_MODEL, max_calls: int = 50,
                 timeout: int = 180, reevo: bool = True,
                 retries: int = 3, backoff: int = 60):
        self.model = model
        self.max_calls = max_calls
        self.timeout = timeout
        self.reevo = reevo      # True: show fitness + ask for reflection (ReEvo)
        self.retries = retries  # attempts after the first, on a failed call
        self.backoff = backoff  # seconds before the first retry, doubling after that
        self.calls = 0
        self.fails = 0
        self.cost = 0.0
        self.in_tok = 0
        self.out_tok = 0

    def _call_once(self, prompt: str):
        """One CLI invocation. Returns the reply text, or None if the call did not
        produce one (timeout, non-JSON, or an error envelope such as a rate limit)."""
        proc = None
        try:
            proc = subprocess.run(
                ["claude", "-p", "--model", self.model, "--output-format", "json",
                 "--tools", "",                       # disable ALL tools -> pure text generation
                 "--dangerously-skip-permissions"],   # (nothing to permit once tools are off)
                input=prompt, capture_output=True, text=True, timeout=self.timeout)
            env = json.loads(proc.stdout)
        except Exception as e:                        # timeout / non-JSON / crash
            rc = proc.returncode if proc is not None else "n/a"
            err = (proc.stderr[:160] if proc is not None and proc.stderr else str(e)[:160])
            sys.stderr.write(f"[ClaudeCliLLM] call {self.calls} attempt failed (rc={rc}): {err}\n")
            return None
        if env.get("is_error") or "result" not in env:
            sys.stderr.write(f"[ClaudeCliLLM] call {self.calls} error envelope: "
                             f"{str(env.get('subtype') or env.get('result'))[:160]}\n")
            return None
        self.cost += env.get("total_cost_usd") or 0.0
        u = env.get("usage") or {}
        self.in_tok += u.get("input_tokens", 0) or 0
        self.out_tok += u.get("output_tokens", 0) or 0
        return env.get("result", "") or ""

    def _complete(self, prompt: str) -> str:
        """Reply text, retrying with backoff before giving up.

        A long run hits transient refusals - a usage limit is the common one, and it
        clears after a wait rather than immediately. Without a retry the loop keeps
        calling, keeps failing, and burns its remaining generations recycling parents,
        which looks like a completed run in the log but evolved nothing.
        """
        self.calls += 1
        for attempt in range(self.retries + 1):
            text = self._call_once(prompt)
            if text:
                return text
            if attempt < self.retries:
                wait = self.backoff * (2 ** attempt)
                sys.stderr.write(f"[ClaudeCliLLM] retrying in {wait}s "
                                 f"({attempt + 1}/{self.retries})\n")
                time.sleep(wait)
        self.fails += 1
        return ""

    def usage(self) -> str:
        warn = f"  WARNING {self.fails}/{self.calls} CALLS FAILED (run invalid)" if self.fails else ""
        return (f"claude-cli ({self.model}) calls={self.calls}  fails={self.fails}  "
                f"in_tok={self.in_tok}  out_tok={self.out_tok}  reported_cost~${self.cost:.4f}{warn}")


def cli_available() -> bool:
    """True if the `claude` CLI is on PATH (so ClaudeCliLLM can be used)."""
    return shutil.which("claude") is not None
