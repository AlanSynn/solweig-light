# Model routing checks

This packet assumes an already working Claude Code GLM-5.3 session. It does not provision paid accounts or authenticate another provider. Verify available models/routes once at start using the actual client configuration without printing secrets. Existing Z.ai setups can bind Claude aliases such as opus to GLM. Do not infer backend identity from a subagent name.

Templates in agents/ use only minimal documented frontmatter and `model: inherit`; they work with the coordinator's provider. For actual Opus work, use a known authenticated Opus session/profile and the same immutable task packet, or a verified multi-provider invocation supported by the installed client. Keep credentials separate. Provider/model cannot be overridden by a prose instruction alone.

Use stronger reasoning for mixed floating-point proof, native ABI/lifetime, concurrency and final review; bounded mechanical code, fixtures and evidence aggregation can use efficient worker effort. Do not invent model IDs or effort options. Record actual attribution, no attribution when unavailable. The project should continue with independent GLM review when Opus is not configured, unless a specific assurance boundary truly requires additional review.

No arbitrary provider setup, global settings edits, `--dangerously-skip-permissions`, secret dumps, or recursive unlimited agent spawning. Useful total concurrency is unconstrained by this packet, bounded by client capability and code/resource ownership.
