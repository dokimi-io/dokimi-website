# A run is a one-shot Job

**What you notice:** you install nothing in the cluster before your first run. `dokimi submit`
creates a Kubernetes Job, streams its log, and the Job ends when the run does. Pressing
++ctrl+c++ stops the stream, not the run, and `dokimi attach` picks it up again, from the same
machine or another one.

## Why

**A test should not need a permanent resident.** A controller or an operator would have to be
installed, upgraded and given standing permissions in every cluster you test, before it has
measured anything. A Job exists only while it runs, with only the permissions its service account
grants.

**The run is self-contained.** Your test definition travels with the run in a ConfigMap, and the
images it runs are chosen when you submit and written into the Job. The Job needs nothing from
the machine that submitted it, which is why `attach` works from anywhere and why a laptop going
to sleep never interrupts a test.

**It bounds itself.** Every Job and every test pod carries a deadline derived from the test's own
duration, so a run that is abandoned or crashes stops on its own instead of sending traffic until
someone notices.

**Its exit code is the verdict.** A Job's exit code is something every CI system already reads.
dokimi's codes are a fixed table, and the Job never retries: a failed test that ran again would
replace a finding with a second measurement.

## What it costs

- **What a run leaves behind is deliberate.** When it ends, the run removes the node-exporter it
  deployed. A run that passed removes its test pods too. One that didn't keeps its owner, its
  definition and the pods of tests that were measured or never started, for inspection, until
  `dokimi cleanup`. Its
  Prometheus stays, so its history can be queried later with `dokimi prometheus <run-id>`.
  Removing it is one `kubectl delete` the run prints for you, or
  `dokimi cleanup <run-id> --prometheus`.
- **Reports come back through the log.** A Job has no file server, so the run writes its reports
  into its log at the end, and `submit` and `attach` extract them.
- **One process per run.** There is nothing to share between runs, which is also why a cluster
  runs [one at a time](one-run-at-a-time.md).
