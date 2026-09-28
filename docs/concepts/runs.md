# Runs and exit codes

## Run ids

Every run has an id like `20260924-143012-k3f9x2`: the UTC start time to the second, then six
characters of `[0-9a-z]`.

- It is **fixed width**, so run ids sort by start time, in a log, a label or a file alike.
- It uses only lowercase letters, digits and hyphens, so it is spelled the same way in labels,
  object names and result files, with no escaping anywhere.

`attach` refuses anything that doesn't match, including a run id in capitals.

## What a run creates

A submission creates three objects, in this order:

| Object | What it is for |
| --- | --- |
| `run-<id>-owner` (ConfigMap) | the run's owner. Everything else the run creates points at it |
| `run-<id>-definition` (ConfigMap) | your test definition, mounted into the Job |
| `run-<id>` (Job) | the run itself |

They live in the test type's namespace, `dokimi-iperf2`, which every run of that type shares. A
run never creates it: `deploy/rbac.yaml` does, once, so submitting needs permissions only inside
that namespace.

The definition travels with the run in a ConfigMap instead of being read from your disk. That is
what makes the Job self-contained, and why `attach` needs nothing local.

In phase 4 the run adds its own Prometheus: a ConfigMap, a Deployment and a Service named
`run-<id>-prometheus`. It scrapes only this run's exporters, every 5 seconds. A node-exporter or
kube-state-metrics the cluster already runs is scraped too, where it runs; dokimi does not
deploy either. If the Prometheus does not answer a query in time, the run stops with exit
code `4` before any test pod exists.

If the submission fails partway, for example because the Job is refused, what it already
created is deleted again, each object by name and uid, after its labels are checked once more.

## Staying inside its own objects

Every object carries two labels:

```yaml
app.kubernetes.io/managed-by: dokimi
dokimi.io/run-id: 20260924-143012-k3f9x2
```

Nothing without those labels is ever modified or deleted, and every lookup and delete is scoped
by a label selector, not by name alone.

**One exception is kept on purpose: the run's Prometheus.** It carries both labels, so it stays
attributable to its run, but it does not point at the run's owner, so deleting the owner leaves
it in place. It never stops a later run from starting. Each run keeps its own, so remove them
when you no longer need their history; [Using the CLI](../getting-started/using-the-cli.md#cleaning-up)
shows how.

The Job also carries:

- **`activeDeadlineSeconds`**, built from named terms: the test duration, startup, warm-up,
  reading the measurement, preflight, diagnostics and cleanup, plus a margin. `--dry-run` prints
  it as `Deadline`. If a run is orphaned, the deadline stops it on its own. Labels make cleanup possible; the deadline makes it
  unnecessary.
- **`backoffLimit: 0` and `restartPolicy: Never`.** The exit code is the verdict, so a controller
  that retried a non-zero exit would re-run the whole test on a plain failure.

## One run at a time

A cluster runs one dokimi run at a time, whatever its namespace or test type: two runs at once
would compete for the very network they measure.

<span class="dk-status dk-status--works">works today</span>

The Job claims the cluster as the first step of phase 4, by writing a claim onto its own owner.
A second run that starts meanwhile is refused, exits `4`, and says which run holds the cluster:

```text
dokimi: refusing to start run 20260924-201500-p7m2q8 (run_already_active): run 20260924-200229-ca532a already active in this cluster.
  - ConfigMap dokimi-iperf2/run-20260924-200229-ca532a-owner claimed at 2026-09-24T20:02:41Z, claim expires at 2026-09-24T20:25:11Z
Wait for it to finish, or for its claim to expire. If it is stale, clear it by deleting its owner, which removes what it created with it:
  kubectl delete configmap -n dokimi-iperf2 run-20260924-200229-ca532a-owner
```

A run holds the cluster only while its claim is live. It stops counting:

- **when it ends**, however it ends: it marks itself finished on the way out, so a failed run
  whose objects are kept as evidence does not block the next one;
- **when its claim expires**, if it crashed: the claim expires at the Job's own deadline, by
  which time the cluster has stopped the Job.

A submission that was refused, or whose Job never started, never claimed anything and blocks
nobody. Two runs that claim at the same moment are serialised by a `Lease` in the `dokimi`
namespace, so exactly one of them starts.

## Exit codes

The exit codes are meant for automation, so they are a fixed contract:

| Code | Meaning |
| --- | --- |
| `0` | the run completed, and it passed |
| `1` | the run completed, and at least one test failed |
| `2` | at least one test errored, or something went wrong after the run |
| `3` | invalid request: a bad definition, run id or flag, found before anything was created |
| `4` | the cluster was not ready for a run (preflight), including another run already holding it |
| `5` | internal or unexpected error |
| `130` | you pressed ++ctrl+c++ |

**The highest applicable code wins.** A run with both failures and errors exits `2`: an error
means part of the test was not measured, and an incomplete picture matters more than any one
finding.

A few more rules:

- A container that exits with a code outside this table, such as `137` after an out-of-memory
  kill, becomes `5`, and the message gives the raw code.
- A run stopped by its deadline exits `5`, with a message saying so.
- A crash in the CLI itself exits `5` with a traceback, not Python's default `1`, which would
  read as a failed test.
- Robot Framework's own exit code is never passed through. It counts failed tests, which
  collides with this table.

!!! note "Today"

    Codes `0` to `2` are verdicts, and a run cannot reach a verdict yet: it stops right after
    claiming the cluster and exits `5`. A node that is missing, cordoned or tainted stops it
    earlier, in planning, with `3`. Another run holding the cluster stops it with `4`.
