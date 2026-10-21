# How it works

## A run is a one-shot Job

You run the `dokimi` CLI on your machine or in CI. It validates your test definition, renders
the Kubernetes objects a run needs, and submits them. From then on, the run happens **inside the
cluster**, as a one-shot Kubernetes Job, and the CLI streams its log back to you.

```mermaid
flowchart LR
    DEF["test.yaml or<br/>suite.robot"] --> CLI["dokimi CLI<br/>(laptop or CI)"]
    CLI -->|submit| JOB["One-shot Job<br/>in the cluster"]
    JOB -->|streams its log| CLI
    JOB -->|reads| NODES["Cluster nodes"]
    JOB -->|deploys| PODS["Test pods:<br/>client and server"]
    JOB -->|starts| PROM["The run's<br/>Prometheus"]
```

Three properties follow from this, and they are the point of the design:

- **No controller is installed.** A Job is not a controller, and it ends with the run. What
  stays is the run's own Prometheus, kept on purpose so that the run's history outlives it,
  until you remove it.
- **The run does not depend on your connection.** The Job is a server-side resource. If the CLI
  disconnects, the run carries on, and `dokimi attach <run-id>` resumes streaming, from any
  machine with access to the cluster.
- **`--dry-run` never submits anything.** It renders the plan and the manifests, and stops.

## The phases of a run

A run moves through twelve phases, numbered 0 to 11. dokimi's messages refer to them by number,
so this table is also a key to what you see in the log.

| # | Phase | What happens | Status |
| --- | --- | --- | --- |
| 0 | Authoring | You write a YAML document or a Robot suite | <span class="dk-status dk-status--works">works today</span> |
| 1 | Submission | The CLI validates, renders the manifests, submits the Job, streams its log, and can reattach. `--dry-run` stops here | <span class="dk-status dk-status--works">works today</span> |
| 2 | Ingestion | In the Job, the definition is parsed and checked again | <span class="dk-status dk-status--works">works today</span> |
| 3 | Planning | The two nodes are resolved against the cluster, and the test is planned | <span class="dk-status dk-status--works">works today</span> |
| 4 | Preflight | The run claims the cluster, so only one run at a time measures its network. It starts its own Prometheus and checks that it answers queries. Then the cluster is checked before any test runs: the nodes, scheduling, image pull, pod-to-pod connectivity and DNS, with the test's own two pods. `dokimi preflight` runs this phase on its own | <span class="dk-status dk-status--works">works today</span> |
| 5 | Suite rendering | The definition is rendered to the Robot suite that actually runs | <span class="dk-status dk-status--works">works today</span> |
| 6 | Execution | Robot Framework runs the suite, which deploys the test pods, waits until both are ready, starts the traffic and waits for it to finish | <span class="dk-status dk-status--works">works today</span> |
| 7 | Measurement | An exporter next to each test pod serves its result as Prometheus metrics. The run reads it directly, and the receiver's view is the result; then it checks that Prometheus holds the same values. No data is never a pass | <span class="dk-status dk-status--works">works today</span> |
| 8 | Validation | The pass criteria are evaluated against the measurements. No data is never a pass | <span class="dk-status dk-status--planned">planned</span> |
| 9 | Reporting | Robot's own report, which comes back to your machine, plus a CSV and JSONL result file | <span class="dk-status dk-status--works">Robot's report works today</span> <span class="dk-status dk-status--planned">CSV and JSONL planned</span> |
| 10 | Diagnostics | Where the pods ran, how each ended, and which pairs were down, captured while that evidence still exists, on every run | <span class="dk-status dk-status--works">works today</span> |
| 11 | Cleanup and exit | The run's objects are deleted, or kept if the run failed, and the exit code goes back to you | <span class="dk-status dk-status--works">test pods removed today</span> <span class="dk-status dk-status--planned">the rest planned</span> |

Today a run gets as far as phase 10. It claims the cluster, starts its Prometheus and checks
that it answers, checks the cluster with the test's own pair, runs the test through Robot
Framework, reads the result and records where everything ran. Phase 8 is not there yet, so it
ends without a verdict and says so:

```text
run 20261013-120000-a1b2c3
phase 2 (ingestion): definition parsed
...
phase 3 (planning): 1 test, sequential
  pair-001  worker-01 -> worker-02

phase 4 (preflight): cluster claimed for this run until 2026-10-13T12:20:30Z
phase 4 (preflight): monitoring mode managed (requested)
  Prometheus  http://run-20261013-120000-a1b2c3-prometheus.dokimi-iperf2.svc:9090
  ...
phase 4 (preflight): Prometheus answers queries
  ...
  query it from your machine with: kubectl port-forward -n dokimi-iperf2 service/run-20261013-120000-a1b2c3-prometheus 9090:9090
phase 4 (preflight): nodes worker-01, worker-02 accept test pods
phase 4 (preflight): pair-001 scheduled, pulled its image and connected, as run-20261013-120000-a1b2c3-pair-001-preflight-client, run-20261013-120000-a1b2c3-pair-001-preflight-server
  UDP to the server pod at 10.244.2.7:5001 arrived, and kubernetes.default.svc resolved
phase 4 (preflight): removed 2 test pod(s)
phase 4 (preflight): the cluster is ready

phase 5 (suite rendering): /work/artifacts/20261013-120000-a1b2c3/suite.robot
phase 6 (execution): pair-001  worker-01 -> worker-02, one Robot Framework process
...
phase 7 (measurement): pair-001, read directly from its exporters (inbound): jitter_seconds 1.1e-05, packet_loss_percent 0, test_duration_seconds 30, throughput_bits_per_second 9.49e+08, transferred_bytes 3.56e+09
phase 7 (measurement): Prometheus holds the series of pair-001

phase 9a (reporting): /work/artifacts/20261013-120000-a1b2c3/log.html, .../report.html

the rest of phases 8 to 11 is not implemented in this build: ... The run stops here without a verdict; Robot's report says which steps ran.
phase 10 (diagnostics): 5 pod(s), 1 pair(s), none down
  ...
phase 10 (diagnostics): /work/artifacts/20261013-120000-a1b2c3/diagnostics.json

phase 11 (cleanup): removed 2 test pod(s)
phase 11 (cleanup): removed node-exporter run-20261013-120000-a1b2c3-node-exporter
...
artifacts: results/20261013-120000-a1b2c3
```

It exits with `5`, not `0`: a run without a verdict must never look like a run that passed. A
cluster that can't run the test stops it in phase 4 with `4`, before any test, and names the
check that failed. On the way out it records where every pod ran, removes its test pods and
waits until they are gone, removes the node-exporter it deployed, and then marks itself
finished, so it stops holding the cluster at once.

## Where Robot Framework fits

Robot Framework has two separate roles in dokimi.

- **As a parser**, today. A `.robot` test definition is read with Robot's own parsing API, so
  keywords are matched the way Robot matches them.
- **As the runner and reporter**, today. The Job renders your definition to a Robot suite,
  the same one `dokimi convert` prints, and runs it with one Robot Framework process per pair of
  nodes. The suite's keywords call dokimi's Python library, which deploys the client and server
  pods, waits until both are ready, starts `iperf2` and waits for it to finish. Robot's `rebot`
  merges the reports, and you get Robot's familiar `report.html` and `log.html`.

The report comes back to your machine through the Job's log: `submit` and `attach` extract it
into the definition's results directory, under the run id:

```text
results/20261013-120000-a1b2c3/
  log.html       Robot Framework's log of the run
  report.html    its report
  output.xml     every pair's results, merged
  suite.robot    the suite that ran
  pairs/         one output.xml per pair
```

Until evaluating the pass criteria is built, every criterion keyword in that report **fails**
and says it was not checked. A test must never look as if it passed when nothing was compared.

Robot Framework is **not** needed on your machine. The CLI works without it. It runs inside the
cluster, in the orchestrator image.

## What a run creates

A submission creates three objects in the test type's namespace, `dokimi-iperf2`:

| Object | What it is for |
| --- | --- |
| `run-<id>-owner` (ConfigMap) | The run's owner. Everything else the run creates points at it, except its Prometheus |
| `run-<id>-definition` (ConfigMap) | Your test definition, mounted into the Job, so the run never depends on a file on your disk |
| `run-<id>` (Job) | The run itself |

In phase 4 the run adds its own Prometheus, `run-<id>-prometheus`: a ConfigMap, a Deployment
and a Service. Unlike everything else, it is kept after the run, so the run's history outlives
it. If the cluster runs no node-exporter, the run also deploys one, as a DaemonSet, and removes
it again when the run ends.

In phase 6 each test adds a client pod and a server pod. The run removes them before it frees
the cluster, however the run ends.

Every one of them is labelled `app.kubernetes.io/managed-by: dokimi` and `dokimi.io/run-id: <id>`.
[Runs and exit codes](concepts/runs.md) goes into the details.
