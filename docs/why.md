# Why dokimi

You want to know whether a Kubernetes cluster performs the way you need it to, and today, with
dokimi, that means whether the network between two of its nodes does. You also want to ask again
next week, after an upgrade or on the next cluster, and get an answer you can compare.

Doing that by hand usually means deploying two pods with `iperf`, reading numbers off a terminal,
deciding on the spot whether they are good enough, and deleting the pods afterwards. That works
once. It is hard to repeat the same way, and the bar the numbers had to clear is written down
nowhere.

dokimi turns that into a test you can keep.

## What it is built around

**The test is the specification.** A test definition names the two nodes, the traffic, and the
criteria that decide pass or fail, with units written out:
`Packet Loss Should Be At Most 0 percent`. Whoever reads the file knows what "good enough" means,
because the file says so.

**No controller stays in your cluster.** A run is a one-shot Kubernetes Job. When it ends, no
controller, operator or agent is left behind. What stays is the run's own Prometheus, kept on
purpose so that the run's history outlives it, until you remove it.

**It touches only what it created.** Every object a run creates is labelled with the run's id.
Lookups and deletes are scoped by those labels, never by name alone.

**It does not guess.** Unknown fields and keywords are refused, not ignored. A node that is
missing, cordoned or tainted stops the run before anything is deployed, and the error names the
fix. A run that stops early never exits as if it had passed.

**It fits CI as well as a terminal.** The same command works on a laptop and in a pipeline, and
the exit codes are a stable contract rather than an implementation detail.

## Where dokimi stands

dokimi is young, and the first release is still being built. Today a run goes from submission to
its verdict: it validates the definition, submits the run, resolves the two nodes, claims the
cluster so that no other run can start, starts its own Prometheus, checks that the cluster can
run the test, runs the `iperf2` test through Robot Framework, reads the measurement, evaluates
the pass criteria against it, cleans up, and exits with the verdict. Robot's report comes back
to you, with each test's outcome. It does not yet write CSV and JSONL results. The
[roadmap](roadmap.md) shows what comes next, and in which order.

## Related projects

Other tools cover parts of this ground, and one of them may already fit what you need:

| Project | What it focuses on |
| --- | --- |
| [k8s-netperf](https://github.com/cloud-bulldozer/k8s-netperf) | Kubernetes network benchmarks with several traffic generators |
| [Testkube](https://github.com/kubeshop/testkube) | General test execution and workflow orchestration on Kubernetes |
| [ClusterLoader2](https://github.com/kubernetes/perf-tests/tree/master/clusterloader2) and [kube-burner](https://github.com/kube-burner/kube-burner) | Load and scalability testing of Kubernetes clusters |
| [K-Bench](https://github.com/vmware-tanzu/k-bench) | Control-plane and data-plane benchmarks |

dokimi's focus is narrower: performance tests whose pass criteria are part of the test itself,
each run as one short-lived Job. Today that means network performance between two nodes. Storage,
control-plane and scalability load, and application load testing are not what dokimi measures.
