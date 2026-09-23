# Existing Claude Code model routing

Use the user's already authenticated GLM-5.3 Claude Code session as coordinator. Verify the actual model id, provider family and effective effort once, without printing keys, full endpoint query strings, or full environment/config files. Do not silently downgrade to a similarly named Flash model. If the configured model differs, record it and use only an explicitly allowed existing route.

Z.ai's Claude Code guide maps Claude model aliases, including `opus`, to GLM-family ids [C02]. Therefore `model: opus` is not proof of Anthropic Opus. For genuine Opus assistance prefer an already working authenticated Anthropic session or an existing verified multi-provider gateway. A separate process/config directory alone does not prove the inherited environment and project settings point to the right provider.

The optional role files in `agents/` use `inherit` for implementation roles and `opus` for Opus review. Install the latter only where its route is verified, or change that one local role to inherit and label the review independent GLM. The coordinator may invoke genuine Opus for implementation as well as review. Do not modify global provider setup, copy auth tokens between sessions, or use broad permission-bypass flags.

Claude Code's model precedence and subagent capabilities vary by installed version [C01]. Check the installed client and available controls; rely on actual completion APIs, not invented TaskOutput calls or unsupported settings. Omitting/setting a model field can still be affected by provider mappings or forced model environment variables. Write a sanitized record with requested model, observed backend/model if available, observation method, effort, client version and unknown fields. Unknown is not verified.

No recurring model status polling. A one-time route check and a terminal attribution record are sufficient unless a route actually changes. Existing v5 records said real Opus was unavailable; do not assume this has since changed, and do not block useful GLM work solely because it remains unavailable.
