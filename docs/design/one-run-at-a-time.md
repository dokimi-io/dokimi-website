# One run at a time

**What you notice:** while one run holds a cluster, a second one is refused, whatever its
namespace or test type, and exits `4`:

```text
dokimi: refusing to start run 20260924-201500-p7m2q8 (run_already_active): run 20260924-200229-ca532a already active in this cluster.
```

The message names the run that holds the cluster, when its claim expires, and how to clear it if
it is stale.

## Why

**Two runs would measure each other.** dokimi measures the network between nodes. A second run
sending traffic at the same time would share the links, the nodes' CPUs and the CNI with the
first, and both results would be wrong in ways neither could see. Refusing is the only way both
stay right.

**Only a run that has started counts.** A run claims the cluster as the first step of its Job,
before it deploys anything. A submission that was refused, or whose Job never started, claimed
nothing and blocks nobody, and neither does a Prometheus an earlier run left behind.

**A crashed run can't block the cluster forever.** The claim expires with the Job's own deadline.
By then the cluster has stopped the Job and everything it ran, so nothing of it can still be
sending traffic.

## What it costs

- **Runs queue by hand.** There is no queue yet: a refused run is submitted again once the
  cluster is free.
- **A run holds the cluster until no test pod of it can still be sending.** It marks itself
  finished only after it has removed every test pod that might still send traffic, because such a
  pod would disturb the next run. If those pods cannot be removed, the run says so and keeps its
  claim until it expires. A run that didn't pass may keep the pods of tests that were measured or
  never started, for inspection; those can't send, so they don't hold the cluster.
