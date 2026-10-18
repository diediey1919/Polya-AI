# SQLite Checkpointer put_writes Contract (LangGraph 3.x)

## Decision table: sync vs async

BaseCheckpointSaver declares `put_writes(...) -> None` and `aput_writes(...) -> None`.
MemorySaver implements `put_writes` (sync); the async default (BaseCheckpointSaver)
delegates to sync under `aloop`. The custom SqliteCheckpointer MUST implement both:
`aput_writes` may delegate to `put_writes`.

## put_writes signature

```
put_writes(self, config, writes, task_id, task_path="") -> None | RunnableConfig
```

- `config`: RunnableConfig with configurable.thread_id, checkpoint_ns (default ""),
  checkpoint_id (may be empty when writing before commit).
- `writes`: Sequence[tuple[str, Any]] — each entry is (channel, value).
- `task_id`: str identifying the task that produced these writes.
- Return: MemorySaver returns None. Some langgraph _loop.py versions assign the
  return to `updated_config`; returning a config carrying `writes_timestamp` is
  safe and matches MemorySaver's documented "updated config" behavior.

## Key mapping (channel -> write_index)

`from langgraph.checkpoint.base import WRITES_IDX_MAP`
Special channels map to negative indices. Regular channels use the sequential
enumerate index:

```
WRITES_IDX_MAP = {
  "__error__": -1,
  "__scheduled__": -2,
  "__interrupt__": -3,
  "__resume__": -4,
}
for idx, (channel, value) in enumerate(writes):
    c_idx = WRITES_IDX_MAP.get(channel, idx)
```

WARNING: WRITES_IDX_MAP.get(channel, idx) raises TypeError when `channel` is an
unhashable ChannelProtocol object. Serialize the channel (`serde.dumps_typed(channel)`)
alongside the value so the value can be deserialized on read.

## Storage row

Key the write by (thread_id, checkpoint_ns, checkpoint_id, task_id, write_index).
Dedup policy: INSERT OR IGNORE (MemorySaver skips reapplying an existing inner key).
Persist: value_type, value_blob (from serde), task_path, AND the serialized channel
(channel_type, channel_blob) so pending_writes can reconstruct (task_id, channel, value).

## Reconstruction (get_tuple / list)

CheckpointTuple.pending_writes must be List[Tuple[task_id, channel, value]] ordered by
(task_id, write_index). Example reconstruction:

```
rows = SELECT task_id, channel_type, channel, value_type, value_data
       FROM writes
       WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id=?
       ORDER BY task_id, write_index ASC
out = []
for task_id, ct, ch, vt, vd in rows:
    channel = serde.loads_typed((ct, ch))
    value = serde.loads_typed((vt, vd))
    out.append((task_id, channel, value))
```

## When checkpoint_id is unknown at put_writes time

langgraph may call put_writes before the checkpoint id is assigned (the write belongs to
the checkpoint about to be committed). Implementations that key writes by checkpoint_id
must resolve the checkpoint_id from the config's checkpoint_id OR, if empty, associate
the writes with the next checkpoint committed for that thread/ns. If in doubt, store
writes keyed by task_id + a sentinel and merge into the just-committed checkpoint in put().
(Avoid this complexity by ensuring the caller sets checkpoint_id in config before
put_writes, which langgraph does on the real loop path.)

## Temp-DB verification recipe

1. Create temp dir + empty sqlite file.
2. cp = SqliteCheckpointer(tmp_path)
3. config = {"configurable": {"thread_id": "t1", "checkpoint_ns": "", "checkpoint_id": "c1"}}
4. cp.put_writes(config, [("claim_input", "test_value")], "task-1")
5. t = cp.get_tuple(config)
6. assert t.pending_writes == [("task-1", "claim_input", "test_value")]
7. Test dedup: call put_writes twice with the SAME writes list (same task_id + same
   channel/idx positions, e.g. [("claim_input","v")] twice); assert no duplicate rows
   via get_tuple. NOTE: two writes for the same channel at DIFFERENT indices (idx 0 vs
   idx 1) have distinct inner keys and are NOT deduped — correct MemorySaver behavior.
8. Test checkpoint commit + resume: put a checkpoint, call get_tuple, assert
   pending_writes surfaced and merged on next put.

## Common failure: closed DB in list() (generator)

`list()` is a generator that MUST keep the SQLite connection open across the `yield`
loop. A `try/finally: conn.close()` placed around only the `fetchall()` closes the
connection BEFORE the `for ... pending_writes` body runs, raising
"cannot operate on a closed database" on the first get_tuple/list iteration after
fetch. Keep the connection open around the entire yield; close in a `finally` that
wraps the FOR loop itself, not just the fetch.

Common failure: NotImplementedError from BaseCheckpointSaver.put_writes -> graph.invoke
blocks at the pregel per-node write step before any node executes. Signature error for
Recovery-007-style "graph invoke crashes before dispatch".

## Agent dispatch timeout — three-tier diagnosis (do NOT raise budget blindly)

A timeout that fails identically at 45s, 120s, and 300s is NOT a budget defect. Run,
in the SAME env/user context as the production dispatch:

1. Direct CLI, minimal prompt (one imperative sentence). Record wall-clock startup,
   exit code, and the FULL stderr.
2. Direct CLI, the real-size prompt. If it ALSO hangs, size/prompt length is exonerated.
3. Adapter probe (AgentRuntime.dispatch) then graph probe
   (build_research_graph + invoke) with the same config.

The environment-layer tell: an identical stderr marker on BOTH the succeeding (minimal)
and failing (real) call, e.g.
`[claude-code:unrecognized_model] {"model":"General","query_source":"sdk"}` — the
CLI fell into a degraded fallback path because the configured model name
(`ANTHROPIC_MODEL`/`ANTHROPIC_DEFAULT_*_MODEL`) is not a real provider model. Fix =
provider/model config, not a timeout raise.

Recovery-008C evidence: minimal prompt exit=0, dur 9.15s (but stderr still carries
`unrecognized_model`); real-size prompt at 120s TIMEOUT. => root cause is the
degraded-mode fallback caused by `model=General`, confirmed end-to-end, not budget.

Configurable budget (secondary): only after the config root cause is resolved,
add a cloud_code-specific budget knob (`POLYA_CLOUD_CODE_TIMEOUT`) so Claude Code's
longer startup is tunable WITHOUT raising the global routing timeout for all agents.

## Provider / protocol contract probe (Recovery-008D / 009)

When Claude Code (or any adapter) times out with an `unrecognized_model` marker, the
defect is the provider/model pair, not the timeout. Determine which provider the CLI
is actually targeting BEFORE sending any paid or real-size prompt.

Read-only contract checks (no config/credential writes):
- Inspect the 9Router config block (`config.yaml` custom_providers): confirm
  `base_url`, `api_mode` (chat_completions = OpenAI-format, NOT Anthropic Messages),
  and the served model aliases.
- Probe the gateway discovery endpoint: `curl -s http://<base>/v1/models`.
  A 200 + model list (e.g. `General`, `polya-research-code`, `qwen-direct/...`)
  proves it is an OpenAI-compatible endpoint. Real capability fields
  (contextWindow, maxOutput, capabilities.reasoning) distinguish a real model
  from a stub alias.
- Compare to the adapter's protocol: Claude Code (`claude -p`) speaks Anthropic
  Messages; a `chat_completions` gateway is incompatible unless an Anthropic-format
  route exists. A mismatch explains `unrecognized_model` + hang-on-real-prompt.

Decision table:

| Adapter | Protocol | 9Router alias in use | Outcome on research prompt |
|---|---|---|---|
| ClaudeCodeAdapter | Anthropic `claude -p` | `ANTHROPIC_MODEL=General` | `unrecognized_model`; full prompt TIMEOUT (wrong protocol + invalid Anthropic name) |
| HermesAdapter | Hermes CLI (reads 9Router General) | `General` (combo, chat_completions) | HANG — subprocess never returns within budget; CLI does not emit final output |
| (none) | OpenAI chat_completions HTTP | `General`/`qwen-direct` | Available on gateway but NO in-repo adapter consumes this format |

Rule: if the discovery probe returns a model list and the gateway `api_mode` is
`chat_completions`, then a real model IS reachable — but only via an OpenAI-format
caller. Claude Code cannot use it as-is; adding a minimal OpenAI-format adapter
(reusing the EXISTING 9Router provider + the EXISTING env API key, no new credential)
is the safe fix path — subject to explicit approval below.

## Paid-provider / live-model approval gate (Recovery-008D.5)

NEVER send a real-size research prompt to a paying/provider route until:
(a) the provider/model pair is verified resolvable (provider probe above), AND
(b) explicit approval to dispatch live prompts is given by the user.

Signals that the route is NOT ready (block, do not retry with a bigger timeout):
- `[claude-code:unrecognized_model]` on stderr for BOTH minimal and real prompts.
- An OpenAI-format gateway with NO in-repo OpenAI-format adapter (and `openai`
  package not installed).
- A provider config with `api_mode` incompatible with the adapter's protocol.

If no adapter consumes the gateway's protocol, the durable fix is:
1. Add the minimal adapter (reuses existing provider config + existing env key;
   stdlib `urllib` only — NO new dependency).
2. Wire it as a non-hardcoded fallback in role mappings (preserve preference order;
   don't force a specific agent globally).
3. Re-run THIS probe recipe + Stage B isolated run.
4. Report live model evidence (output, usage, correlation_id) — never exit-code-0
   as proof of valid generation.

Only (1)-(2) are code changes; they are BLOCKED until (b). A trivial "ok" from the
CLI for a 1-sentence prompt is NOT proof of a valid model call — it is the fallback
ack path. The tell is: trivial succeeds WITH the same stderr marker that fails the
full prompt.
