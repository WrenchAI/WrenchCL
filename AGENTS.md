# Agent Rules -- WrenchAI/WrenchCL

WrenchCL is the shared Wrench.ai Python client library used by every backend service.
Breaking changes here break all consumers. Version pinned at `wrenchcl[aws]~=6.0.3`
across the fleet. Changes require backward-compatible additions or a coordinated upgrade.

## Blocking criteria

**Backward compatibility:**
- Public function signature changed in a backward-incompatible way without a major version bump -> Blocker [judgment]
- Existing import path removed or renamed without a deprecation shim -> Blocker

**Secrets:**
- Hardcoded secret, API key, or credential value -> Blocker

**Testing:**
- New function or method with no test -> Blocker
- `resolve_secret`, `slack_post`, `job_register`, `job_update`, `job_close` behavior changed
  without updating the integration tests that depend on them -> Blocker

**Branch integrity:**
- Direct commit to `release` branch -> Blocker (all changes via PR)

## Non-blocking (Nit only)

- Docstring verbosity
- Internal variable naming

## Merge policy

No Blockers from review. Dan Baird approves judgment findings.
Coordinate fleet-wide version bumps with all consuming services before releasing.
