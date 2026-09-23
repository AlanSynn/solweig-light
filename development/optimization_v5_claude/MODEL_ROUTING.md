# GLM-5.3 and actual Opus: routing, not just labels

## 1. Separate client, model and provider

Claude Code is the client. GLM-5.3 is the requested model for the coordinator/ordinary implementers. Actual Anthropic Opus is the preferred model family for demanding numerical implementation and independent review. The model named `opus` in a subagent definition does not supply another provider URL or authentication.

Official Z.ai setup uses the Anthropic-compatible endpoint `https://api.z.ai/api/anthropic`. Its example maps `ANTHROPIC_DEFAULT_OPUS_MODEL` and `ANTHROPIC_DEFAULT_SONNET_MODEL` to GLM. Thus a GLM-configured session can display/use an Opus role/alias while all requests still go to Z.ai. This packet must never call that an Anthropic Opus review. [C02,C03,C06]

GLM-5.3's published effort values are low/high/max with reasoning enabled. Claude Code has its own version/model-specific effort interface. Request the most useful supported level, but do not assert that a Claude CLI setting became a GLM backend parameter without verifying the route/version behavior. Do not copy an old `thinking.type: disabled` request to this model. [C01,C05]

## 2. Recommended topology: two existing, authorized profiles

```text
GLM Claude Code coordinator (GLM-5.3, Z.ai profile)
  -> normal native subagents inheriting that verified GLM route
  -> isolated Opus Claude Code sessions (actual Anthropic profile)
       numerical implementation / independent proof and code review
  -> single integrator + exclusive measurement owner
```

This is a logical agent team, not a promise of native cross-provider child routing. The separate Opus sessions can use their own native Opus subagents. Exchange one immutable task packet and one terminal result/commit; do not replay the whole parent transcript.

Default to already functioning profiles. `CLAUDE_CONFIG_DIR` can separate settings/history/plugin storage, and `--settings` / `--setting-sources` exist for session configuration, but authentication details vary by installed version and provider. A separate directory by itself is **not proof of separate credentials or an effective route**. Both profile and all applicable environment/project/managed settings must be checked. [C04,C05]

Illustrative invocations, only after both profiles independently work:

```bash
# GLM profile already configured and authenticated outside the repository.
CLAUDE_CONFIG_DIR="$GLM_CONFIG_DIR" claude --model glm-5.3

# Separate shell/environment without inherited Z.ai routing or remapped aliases.
# OPUS_MODEL_ID must be an ID/alias actually served on this authenticated profile.
CLAUDE_CONFIG_DIR="$OPUS_CONFIG_DIR" claude --model "$OPUS_MODEL_ID"
```

The second command is deliberately not an automatic credential switch. Reusing a shell that still exports Z.ai `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, API keys or default aliases can route incorrectly. `--settings` merges unspecified keys with inherited settings; it does not erase all old routing. Never print auth values while checking. Do not copy login files or credential stores into worktrees. [C02,C04,C05]

For a non-interactive worker, a verified profile can use the documented `-p`, `--model`, `--agent` and output options to run an assigned packet from its explicit worktree. Capture process exit/terminal result with the client or OS supervisor. Use the installed version's help. Do not assume a particular event JSON schema or invent `/goal`, `TeamCreate`, `Task` parameters, or provider-routing YAML fields. This packet does not provide an untested generic gateway script.

## 3. Alternative: one existing multi-provider gateway

Only when the user already has an authorized Anthropic-compatible gateway that genuinely routes both model IDs and supports required tool calls:

- Set the coordinator to the verified GLM wire model.
- Set Opus specialists to the verified Opus wire model / alias mapping.
- Verify that each route selects the intended provider, not a renamed GLM model.
- Ensure tools, response formats, reasoning parameters, cancellation, long calls and background results are supported.
- Record routing provenance and any server-side model substitution.

Do not build/install a gateway, purchase a plan, expose an endpoint or transfer provider credentials as part of numerical optimization. If no mixed route exists, use separate sessions. If neither a genuine Opus session nor an existing gateway is available, run independent GLM review with that exact label and record Opus unavailable. Do not block unrelated work or invent an Opus pass.

## 4. Preflight once per route/version change

Run local version/help/config inspection. `tools/preflight_local.py` reads only an allowlist of nonsecret routing metadata from specified settings files and environment. It performs **no API call**, verifies no subscription, and must output `backend_verified: false`. Treat its output as a diagnostic, not proof of effective precedence.

The execution owner then performs one small authorized tool-use smoke per real route: read an assigned harmless local file and report its hash/path. Collect provider request/response metadata if available. An assistant saying "I am Opus" is not verification. A requested wire model plus trusted provider configuration is useful provenance; if response model metadata is hidden, record it as unknown rather than assuming.

Record in `templates/ROUTING_MANIFEST.json`: CLI version, session/worker identifier, requested model, configured route host (no query/userinfo), alias mappings, resolved backend metadata where available, effort requested/accepted, tool support and verification source. Actual token usage is optional telemetry; this project has no artificial token budget. No service is guaranteed unlimited or immune to 429/rate limits.

Do not use OpenAI/Codex/Astra for live planning, review, routing or emergency fallback. Historical source citations do not authorize such calls.

## 5. Native agent definitions

Templates in `agents/` use documented Markdown frontmatter. GLM implementation roles use `model: inherit`; the coordinator must already be GLM-5.3. Opus definitions use `model: opus` **only on a verified Opus-serving route**. Explicit full wire IDs may replace aliases after preflight. Merely installing a definition does not authorize invoking it through an incompatible endpoint. [C06]

No hard `maxTurns`/dollar/token cap is supplied. Tool capabilities and task scope remain bounded. `permissionMode: acceptEdits` does not automatically approve every Bash command; establish a narrow local test/git worktree allowlist through the actual client, not `bypassPermissions`. Existing managed safety policy remains in force.

Do not preload every strategy file into every agent. A short CLAUDE import gives invariant rules; task packets select blueprint sections and one dossier. Importing Markdown with `@` loads it at session start, so only the short `CLAUDE_PROJECT_RULES.md` is automatically imported. [C07]

## 6. Worktree and API version traps

Current Claude docs describe native worktrees starting from a default branch unless `worktree.baseRef` is `head`; that can omit unpushed integration commits. The optional `config/worktree-head.fragment.json` addresses this only on a client that supports it. Prefer explicit `git worktree add -b ... <immutable_SHA>` and verify each worker's actual base before any edit. No packet is considered present in a new worktree merely because it is untracked in the parent; copy or commit nonsecret instructions deliberately. [C08]

Subagent concurrency/depth limits and team APIs are version-sensitive. Current documentation supports configured concurrency and nesting limits, but this user request is not a claim that any installed client supports infinite concurrent sessions. Inspect actual support once. Do not repeatedly retry a client capacity error. Native agent teams are an optional interactive facility and are not required by this plan; ordinary subagents and independent sessions suffice. In particular, do not assume interactive team behavior works in `-p` mode. [C06,C09]
