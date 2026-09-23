# GLM-5.3 coordinator and real Opus workers

Use the user's working Claude Code setup. No provider installation or API call is performed by this packet. Availability of tokens is not a guarantee of provider credentials, model access, runtime capabilities or unlimited server concurrency.

Official Z.ai documentation supports GLM use through Claude Code and shows Claude model aliases mapping to GLM models. Therefore `model: opus` on a Z.ai endpoint is not sufficient evidence that Anthropic Opus served the request. Official Claude subagent documentation describes per-agent model selection and inheritance. [O01/O02]

## Startup record, once

Record Claude Code version, requested model alias/ID, effective endpoint/provider label (redacted origin only), visible resolved/served model metadata, effort requested/supported, delegation mode and route-verification status. Do not print API keys, tokens, full environment, user settings files or authorization headers. A self-reported model name in generated prose is not provider evidence.

GLM coordinator continues on the selected GLM-5.3 model. Use model inheritance in GLM-specific workers only after verifying that the parent actually uses the requested route. Do not switch to a Flash/other model silently to save money. The user authorized sufficient inference for the task.

For actual Opus use an already authenticated Anthropic/profile-isolated Claude session or an already verified multi-provider gateway. Prefer separate provider-specific processes with inherited Z.ai overrides removed from the Opus child environment under the user's existing profiles. A different settings directory is not by itself complete isolation: environment, managed/project settings and proxy defaults can still override routing. Do not rewrite global config or copy credentials between worktrees. Do not install a gateway as a prerequisite.

If no verified Opus route exists, continue useful implementation/review with GLM in independent sessions and record the exact limitation. High-risk unproved optimization can remain unselected; it must not force a false provider claim. No requests for Astra tokens are needed.

## Agent files

Optional `agents/sw6-*.md` templates use conservative documented frontmatter and intentionally do not request automatic worktree isolation. The coordinator sets up an explicit detached worktree at the intended commit and launches there. Confirm installed client schema before installing; reuse existing agent definitions rather than creating duplicates. `model: opus` templates are used only in a verified Opus-capable route; otherwise invoke the GLM equivalents with honest labels. Keep short descriptions and load dossiers in the task packet rather than preloading every skill into every session.

Keep default permission boundaries. No `bypassPermissions`, automatic credential access or blanket destructive Bash permission is needed. Safe local tests/edits are preauthorized in the task; production/remote/policy changes are not.
