# Roadmap

dokimi is built in milestones. Each one delivers something usable, and nothing is built before
the design it depends on is settled. **Milestone-01 becomes the first release, 0.1.**

## Milestone-01: the first end-to-end run

<span class="dk-status dk-status--works">in progress</span>

A deliberately narrow first slice. One cluster, one `iperf2` UDP test between two nodes you
name, over the pod network, measured through a managed Prometheus, evaluated against throughput
and packet-loss criteria, results written as CSV and JSONL, and everything the run created
cleaned up afterwards.

| Work item | State |
| --- | --- |
| Repository, toolchain and continuous integration | <span class="dk-status dk-status--works">done</span> |
| Orchestrator container image and release wiring | <span class="dk-status dk-status--works">done</span> |
| Test definitions in YAML and Robot | <span class="dk-status dk-status--works">done</span> |
| CLI: validate, dry-run, submit, stream, reattach | <span class="dk-status dk-status--works">done</span> |
| Cluster discovery, node resolution and planning | <span class="dk-status dk-status--works">done</span> |
| A multi-node test environment on one machine | <span class="dk-status dk-status--works">done</span> |
| Rename to dokimi | <span class="dk-status dk-status--works">done</span> |
| Run identity, ownership labels, one run at a time per cluster | <span class="dk-status dk-status--works">done</span> |
| Preflight: check the cluster before running | <span class="dk-status dk-status--planned">planned</span> |
| Managed Prometheus | <span class="dk-status dk-status--planned">planned</span> |
| The `iperf2` test type | <span class="dk-status dk-status--planned">planned</span> |
| The `iperf2` exporter | <span class="dk-status dk-status--planned">planned</span> |
| Running the test through Robot Framework, with Robot's report | <span class="dk-status dk-status--planned">planned</span> |
| Measurement | <span class="dk-status dk-status--planned">planned</span> |
| Evaluating the pass criteria | <span class="dk-status dk-status--planned">planned</span> |
| Result files: CSV and JSONL | <span class="dk-status dk-status--planned">planned</span> |
| Post-run diagnostics | <span class="dk-status dk-status--planned">planned</span> |
| Outcomes, cleanup and the final exit code | <span class="dk-status dk-status--planned">planned</span> |
| An end-to-end acceptance run | <span class="dk-status dk-status--planned">planned</span> |

## After the first release

<span class="dk-status dk-status--planned">planned</span>

These milestones are planned, not scheduled. Their order can change as the first release teaches
us more.

**Milestone-02: whole-cluster test matrices.** From one pair of nodes to tests across a
cluster: all-to-all and one-to-many matrices, selecting nodes by label or topology, running pairs
in parallel where it is safe, and a versioned YAML schema.

**Milestone-03: more test types.** `iperf3` and IRTT next to `iperf2`, including latency, without
test-type-specific code in the core.

**Milestone-04: results that last.** An optional external result database, repeated runs and
aggregation, historical baselines, and regression detection.

**Milestone-05: stable interfaces.** The interfaces move from `v1alpha1` to `v1`, with explicit
compatibility guarantees and migration rules, ahead of a Kubernetes Operator.

**Milestone-06: multi-cluster.** Tests between clusters: discovery, connectivity, security and
correlating results from more than one cluster.
