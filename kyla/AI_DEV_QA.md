# KYLA AI development audit loop

This is the working rule for code produced by KYLA agents: `claude`, `codex`, `copilot`, `cursor`, `docker-agent`, `droid`, and `shell`. It supports [R13 — IRA QA & Security](../README.md#rooms), the room for testing and security.

## Why self-review is not enough

A model that writes code is close to its own assumptions, omissions, and mistaken interpretation of the task. Asking that same model to be the only reviewer is like grading your own homework: it may confirm the intended answer without reliably noticing what was missed. A second model with a different review role creates a separate pass over behavior, edge cases, security, and licensing. This is a practical separation of responsibilities—not a claim that either model is infallible—so a final human/owner decision is still required.

## Exact five-step audit loop

For every agent output, run all five steps in order. **No output is approved until it passes the R13 QA/security review.** Record the result and any fixes in the PR.

1. **Write.** The assigned agent implements the smallest change that meets the request. State the scope, assumptions, affected files, and how to test it.
2. **Run skill check.** Run the repository’s applicable tests, linters, formatters, type checks, and documented dry-run or skill checks. Fix failures; do not treat an unrun check as a pass.
3. **Cross-model review.** Have a different model review the first model’s code and diff. Ask it to look for correctness gaps, unsafe behavior, missing tests, and scope creep. The writing model may respond, but it is not the sole reviewer.
4. **Security/license scan.** Check secrets and unsafe inputs, dependency and permission changes, container/shell boundaries, and applicable license or attribution requirements. Capture tool names/results and resolve findings or explain an accepted exception.
5. **SOPHIA/Mel approval.** SOPHIA/Mel reviews the evidence from steps 1–4, confirms the R13 QA/security gate is satisfied, and approves or sends the work back. Approval is required before merge or release.

Apply the same loop whether the writer is `claude`, `codex`, `copilot`, `cursor`, `docker-agent`, `droid`, or `shell`; choose a different available model for step 3.

## Exact Git/GitHub workflow

1. **Feature branch:** start from the current `main`; create a named branch such as `feature/<short-description>`. Keep the change focused.
2. **PR:** commit the change on the feature branch, push it, and open a pull request targeting `main`. Link the task and include the test/skill, cross-model, security/license, and approval evidence.
3. **Review checklist:** before merge, confirm: scope matches the request; tests/linters/skill checks ran and passed; a different model reviewed the diff; security and license scans are recorded; no secrets or unapproved permissions entered; R13 QA/security review passed; SOPHIA/Mel approved.
4. **Merge:** merge the approved PR into `main` using the repository’s permitted merge method. Verify the merged commit and final file on `main`; if any gate is missing or fails, do not merge—return to the responsible agent for fixes and repeat the loop.
