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

The run removes the test pods before it frees the cluster, however it ends, and waits
until they are gone, because a pod that is still sending would disturb the next run. If they
cannot be removed, the run says so, keeps its claim on the cluster until the claim expires, and
prints the two `kubectl` commands that free it earlier.

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
log, as long as the Job's pod exists. [Using the CLI](../getting-started/using-the-cli.md#attach)
says where they land.

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

- **when it ends**, however it ends: on the way out it removes its test pods, waits until they
  are gone, and then marks itself finished, so a failed run does not block the next one, and no
  test is still sending once the cluster is free;
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

    Codes `0` to `2` are verdicts, and a run cannot reach a verdict yet. It runs the test through
    Robot Framework and then exits `5`, because measuring and evaluating the result are not built
    yet. A node that is missing, cordoned or tainted stops it earlier, in planning, with `3`.
    Another run holding the cluster, or a Prometheus that does not answer, stops it with `4`.
