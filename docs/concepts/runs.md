# Runs and exit codes

## Run ids

Every run has an id like `20260924-143012-k3f9x2`: the UTC start time to the second, then six
characters of `[0-9a-z]`.

- It is **fixed width**, so run ids sort by start time, in a log, a label or a file alike.
- It uses only lowercase letters, digits and hyphens, so it is spelled the same way in labels,
  object names and result files, with no escaping anywhere.

`attach` and `cleanup` refuse anything that doesn't match, including a run id in capitals.

## What a run creates

A submission creates three objects, in this order:

| Object | What it is for |
| --- | --- |
| `run-<id>-owner` (ConfigMap) | the run's owner. Everything else the run creates points at it, except its Prometheus |
| `run-<id>-definition` (ConfigMap) | your test definition, mounted into the Job |
| `run-<id>` (Job) | the run itself |

They live in the test type's namespace, `dokimi-iperf2`, which every run of that type shares. A
run never creates it: `deploy/rbac.yaml` does, once, so submitting needs permissions only inside
that namespace.

The definition travels with the run in a ConfigMap instead of being read from your disk. That is
what makes the Job self-contained, and why `attach` needs nothing local.

Then the run adds what it needs, in two steps.

**In phase 4, its own Prometheus:** a ConfigMap, a Deployment and a Service named
`run-<id>-prometheus`.

- It scrapes only this run's exporters, every 5 seconds: pods with this run's id that have a
  container port named `metrics`. A Prometheus kept from an earlier run never records a later
  run's results. Each `iperf2` test pod has its exporter on port 9101, next to the tool.
- It prefers a node other than the two being tested, so it does not compete with the
  measurement. On a two-node cluster it still runs.
- It keeps at most 512 MB of data, in a 1 GiB volume.
- A node-exporter or kube-state-metrics the cluster already runs is found by its Service and
  scraped where it runs. dokimi never deploys kube-state-metrics; if there is none, the run
  records it as absent.
- If the cluster has no node-exporter, the run deploys one as a DaemonSet. It collects CPU,
  memory and network interfaces only, on port 9137, and needs the host's network and nothing
  else. A namespace that enforces the `baseline` Pod Security level refuses its pods; the run
  then says so and continues without node metrics, which explain a result but never decide
  one. The run removes the node-exporter it deployed when it ends, and leaves one it found.

The run checks that its Prometheus answers a query. If it does not answer within three minutes,
the run stops with exit code `4`, before any test pod exists. The log names the Prometheus, says
it is kept, and prints the `kubectl port-forward` command that reaches it from your machine.

**Still in phase 4, the cluster checks.** The run reads the nodes again, then deploys the first
pair once, with its own nodes and image, to see that its pods are scheduled, pull their image,
reach each other and resolve a cluster name. These probe pods run without the exporter, so
nothing scrapes them, and they are removed before the test starts. A failed check stops the run
with exit code `4` and names it: `node_count`, `scheduling`, `image_pull`, `connectivity` or
`dns`. [Using the CLI](../getting-started/using-the-cli.md#preflight) lists what each one means.

**In phase 6, the test pods:** a client pod and a server pod for each pair of nodes, deployed by
the Robot suite. Each runs `iperf2` with its exporter next to it. Once the test has finished, the
run reads both exporters directly (phase 7): the server's view, what arrived, is the result. A
test whose exporters serve no complete result fails as `metrics_missing`, never as a pass. The
run then checks that its Prometheus holds the same values, and warns if it doesn't; the result
stands either way.

**In phase 10, before anything is removed,** the run records where every pod ran, how each one
ended, and which pairs were down. That's `diagnostics.json`, next to Robot's report.

**In phase 11, the run cleans up.** What it leaves depends on how it ended; see
[What a run keeps](#what-a-run-keeps).

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

The run's reports do not stay in the cluster. They come back to your machine through the Job's
log, once: `submit` or `attach` removes the Job when it has extracted them, and the cluster
removes a Job nobody fetched an hour after it finished.
[Using the CLI](../getting-started/using-the-cli.md#attach) says where they land.

The Job also carries:

- **`activeDeadlineSeconds`**, built from named terms: the test duration, startup, warm-up,
  reading the measurement, preflight, diagnostics and cleanup, plus a margin. `--dry-run` prints
  it as `Deadline`. If a run is orphaned, the deadline stops it on its own. Labels make cleanup possible; the deadline makes it
  unnecessary.
- **`backoffLimit: 0` and `restartPolicy: Never`.** The exit code is the verdict, so a controller
  that retried a non-zero exit would re-run the whole test on a plain failure.
- **`ttlSecondsAfterFinished: 3600`**, so that the cluster removes a finished Job whose reports
  nobody fetched within the hour.

## What a run keeps

<span class="dk-status dk-status--works">works today</span>

A run cleans up after itself, in phase 11, and keeps what is worth looking at when it didn't
pass:

| The run | What stays | Until |
| --- | --- | --- |
| exited `0` | its Prometheus; until its reports are fetched, also its owner and definition | you remove the Prometheus; the owner and definition go with the fetch, or with `dokimi cleanup` |
| didn't exit `0` | its Prometheus, its owner and definition, and the pods of each test that was measured or never started | `dokimi cleanup` |
| stopped in its preflight | its Prometheus; until its reports are fetched, also its owner and definition | you remove the Prometheus; the owner and definition go with the fetch, or with `dokimi cleanup` |
| crashed, or its Job was stopped | whatever it had created | `dokimi cleanup`, once its claim has expired |

A kept test pod still has its logs and events. The node-exporter a run deployed always goes,
or the Prometheus would go on scraping every node through it. `submit --retain always` keeps a
passing run's evidence too, and `--retain never` keeps none.

**A test pod that may still be sending never stays,** because the next run would measure next to
it: the client of a test that timed out, or a test that lost a pod or recorded nothing. The run
removes those and waits until they are gone before it frees the cluster. If they can't be
removed, it keeps its claim until the claim expires, and says how to free the cluster earlier.
[Using the CLI](../getting-started/using-the-cli.md#cleaning-up) shows `dokimi cleanup`.

## One run at a time

A cluster runs one dokimi run at a time, whatever its namespace or test type: two runs at once
would compete for the very network they measure.

<span class="dk-status dk-status--works">works today</span>

The Job claims the cluster as the first step of phase 4, by writing a claim onto its own owner.
A second run that starts meanwhile is refused, exits `4`, and says which run holds the cluster:

```text
dokimi: refusing to start run 20260924-201500-p7m2q8 (run_already_active): run 20260924-200229-ca532a already active in this cluster.
  - ConfigMap dokimi-iperf2/run-20260924-200229-ca532a-owner claimed at 2026-09-24T20:02:41Z, claim expires at 2026-09-24T20:25:11Z
Wait for it to finish, or for its claim to expire. If it is stale, because its Job is gone, clear it, which removes what it created with it:
  dokimi cleanup 20260924-200229-ca532a --namespace dokimi-iperf2 --force
```

A run holds the cluster only while its claim is live. It stops counting:

- **when it ends**, however it ends: once no test pod of it can still be sending, it marks
  itself finished, so a failed run whose evidence is kept does not block the next one;
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
| `1` | the run completed, and at least one test failed a criterion |
| `2` | at least one test could not be validly measured, or something went wrong around the run |
| `3` | invalid request: a bad definition, run id or flag, found before anything was created |
| `4` | the cluster was not ready for a run (preflight), including another run already holding it |
| `5` | internal or unexpected error |
| `130` | you pressed ++ctrl+c++ |

**The highest applicable code wins.** A run with both failures and errors exits `2`: an error
means part of the test was not measured, and an incomplete picture matters more than any one
finding.

The code comes from each test's outcome, as Robot's report and its `validation.json` record it.
A test that recorded nothing counts as an error.

A few more rules:

- An anomaly in phase 10's snapshot, such as a test pod that was evicted or a node that is no
  longer Ready, makes the run exit `2` even if its tests passed: their results are not the whole
  picture.
- `dokimi preflight` runs no test, so it answers `0` or `4`.

- A container that exits with a code outside this table, such as `137` after an out-of-memory
  kill, becomes `5`, and the message gives the raw code.
- A run stopped by its deadline exits `5`, with a message saying so.
- A crash in the CLI itself exits `5` with a traceback, not Python's default `1`, which would
  read as a failed test.
- Robot Framework's own exit code is never passed through. It counts failed tests, which
  collides with this table.
