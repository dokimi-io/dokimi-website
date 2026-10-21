# No data is never a pass

**What you notice:** whenever dokimi could not check something, the run doesn't pass. A test whose
tool measured nothing fails. A criterion that wasn't evaluated fails and says it wasn't checked.
And a run that stops early exits with an error, never `0`.

## Why

**`0` is a promise.** CI reads `0` as "everything checked, everything fine". If a run could exit
`0` without having measured, a broken cluster, a missing metric or a crashed tool would look like
a healthy network.

**Missing data is an error, kept apart from a failure.** A failure means dokimi measured, and the
network didn't meet the criterion. An error means it couldn't measure validly. The two point at
different things to fix, so they get different exit codes, and an error is never counted as a
pass.

**Today, in practice:**

- a tool that ran without producing a measurement fails its test;
- the pass criteria are not evaluated yet, so each one fails with "was not checked" rather than
  passing or being skipped;
- a run stops after its report with exit code `5`, because it can't reach a verdict yet;
- a run that couldn't start properly, because the cluster is busy or its Prometheus can't be
  queried, exits `4` before any test.

The full table of exit codes is in [Runs and exit codes](../concepts/runs.md).

## What it costs

- **More red than you might expect** while dokimi is young: a run fails visibly whenever it can't
  check something.
- **Every new check has to decide what "no data" means for it,** before it can pass anything. That
  is slower to build than treating absence as fine.
