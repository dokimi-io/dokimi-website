# No data is never a pass

**What you notice:** whenever dokimi could not check something, the run doesn't pass. A test whose
tool measured nothing is an error. A criterion with no measurement behind it is an error, not a
pass. And a run that stops early exits with an error, never `0`.

## Why

**`0` is a promise.** CI reads `0` as "everything checked, everything fine". If a run could exit
`0` without having measured, a broken cluster, a missing metric or a crashed tool would look like
a healthy network.

**Missing data is an error, kept apart from a failure.** A failure means dokimi measured, and the
network didn't meet the criterion. An error means it couldn't measure validly. The two point at
different things to fix, so they get different exit codes, and an error is never counted as a
pass.

**Today, in practice:**

- a tool that ran without producing a measurement makes its test an error, `tool_execution`;
- a test whose exporters serve no result, or serve something unreadable, is an error,
  `metrics_missing` or `exporter_parse`, and Robot's report tags it `outcome:error`, never a pass;
- every pass criterion is evaluated, and one that no pair can measure, such as latency today, is
  an error too. An error outranks a failure;
- a definition without a criterion is refused, so a test always has something to pass against;
- the run's exit code is its worst test outcome: `0` only if every test passed, `1` if one failed,
  `2` if one is an error. Something wrong that the run found after its tests, in the pods it
  deployed, makes it `2` as well;
- a cluster that can't run the test exits `4` before any test: another run holds it, its
  Prometheus can't be queried, or one of the cluster checks fails.

The full table of exit codes is in [Runs and exit codes](../concepts/runs.md).

## What it costs

- **More red than you might expect** while dokimi is young: a run fails visibly whenever it can't
  check something.
- **Every new check has to decide what "no data" means for it,** before it can pass anything. That
  is slower to build than treating absence as fine.
