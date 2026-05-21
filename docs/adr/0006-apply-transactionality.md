# ADR 0006: Repair Apply Transactionality

Status: Accepted

## Context

Repair plans may contain multiple actions with edits across multiple files plus commands. If the adapter applies action 1 successfully but action 2 fails (precondition check fails, file disappeared, command errors), the workspace is left in a partially modified state.

The spec says agents SHOULD apply edits transactionally and the conformance doc mentions atomic or VCS-aware strategies, but neither defines what `result.apply` must report when partial failure occurs, nor what rollback means.

## Decision

ANCP defines explicit partial-failure semantics for `result.apply`:

- `status` is extended with `rolled_back` and `precondition_failed` values.
- A `rollback` object is added to `result.apply` reporting whether rollback was attempted, whether it succeeded, and which strategy was used.
- If any required precondition fails before any mutation begins, the adapter MUST refuse the entire plan and set `status` to `precondition_failed`.
- If mutation starts and a later action fails, the adapter SHOULD attempt rollback. Status MUST be `partial` if rollback was not attempted or failed, or `rolled_back` if rollback succeeded.
- The adapter MUST document its rollback strategy in `manifest.adapter`.

## Consequences

Benefits:

- consumers can distinguish clean refusal from partial damage,
- agents can decide whether to retry, escalate, or report based on structured status,
- adapter authors must think about transactionality early.

Costs:

- adapters must implement at least a basic rollback strategy to claim the `repair-apply` profile,
- VCS-based rollback requires the workspace to have a clean VCS state,
- backup-based rollback requires temporary storage.
