# Networking, Helm and Operators

Kubernetes gives every pod an IP address and expects pods to reach each other without network address translation, but it leaves the details to a network plugin. On top of that, you control which traffic is allowed, optionally add a service mesh, package applications with Helm, and extend the API with operators. Interviewers ask these topics to see whether you can reason about traffic flow and about how the platform is extended.

## Core concepts

### Pod-to-pod communication
Every pod gets its own IP address. Pods on any node can reach other pods by IP, which the cluster network plugin (the CNI plugin) makes work. Pod IPs change when pods are replaced, so clients should use Services instead.

### Service discovery through DNS
The cluster DNS server gives every Service a name in the form `<service>.<namespace>.svc.cluster.local`. Within the same namespace, the short name `orders` is enough. A pod in another namespace uses `orders.payments`, for example.

```java
import java.net.InetAddress;
import java.net.UnknownHostException;

public class ServiceLookup {
    public static void main(String[] args) throws UnknownHostException {
        // Resolves inside a pod through cluster DNS; fails on a machine outside the cluster
        InetAddress address = InetAddress.getByName("orders.payments.svc.cluster.local");
        System.out.println("Resolved to " + address.getHostAddress());
    }
}
```

In practice, most applications use the Service URL in configuration, such as `http://orders.payments.svc.cluster.local`, and let the HTTP client resolve it.

### Network policies
By default, all pods can talk to all other pods. A **NetworkPolicy** selects pods and restricts their ingress (incoming) and egress (outgoing) traffic. Policies only take effect if the network plugin enforces them. A common baseline is a default-deny policy, followed by explicit allows.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-orders-from-gateway
  namespace: orders
spec:
  podSelector:
    matchLabels:
      app: orders
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: gateway
      ports:
        - protocol: TCP
          port: 8080
```

This policy allows only pods labelled `app: gateway` to reach the orders pods on port 8080. Once a pod is selected for the `Ingress` policy type, traffic not matched by an allow rule is dropped.

### Service meshes
A **service mesh** adds a layer for service-to-service traffic, usually by injecting a proxy next to each pod. Typical features are mutual TLS between services, retries and timeouts, traffic splitting for canary releases, and uniform metrics. Istio and Linkerd are the common choices.

A mesh adds operational complexity and resource overhead. Adopt it when the features are needed, not by default.

### Helm: packaging and templating
**Helm** packages Kubernetes manifests as a **chart**. A chart has a `Chart.yaml` with metadata, a `values.yaml` with default settings, and `templates/` containing manifests with placeholders.

```yaml
# templates/deployment.yaml (excerpt)
spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

```yaml
# values.yaml
replicaCount: 3
image:
  repository: orders-service
  tag: "1.4.0"
```

Common commands:

- `helm install orders ./orders-chart -f values-prod.yaml` creates a **release**.
- `helm upgrade orders ./orders-chart -f values-prod.yaml` applies changes as a new revision.
- `helm rollback orders 1` returns the release to an earlier revision.
- `helm template ./orders-chart` renders the manifests without applying them, which is useful in CI.

Helm tracks releases and their revisions in the cluster, so rollbacks are one command away.

### Custom Resource Definitions (CRDs)
A **CustomResourceDefinition** adds a new resource type to the Kubernetes API, such as `Database` or `Certificate`. Once installed, you create and read those objects with `kubectl` like any built-in object, and they are stored in etcd.

### Operators and controllers
A **controller** runs a reconcile loop: it reads the desired state from an object, observes the actual state, and makes changes to close the gap. An **operator** is a controller for a CRD that encodes operational knowledge, such as how to back up, upgrade, or fail over a database.

The reconcile pattern is the core idea. The following simplified Java model shows the shape of one pass:

```java
import java.util.Optional;

public class ReconcileSketch {

    record DesiredState(int replicas) {}
    record ObservedState(int runningReplicas) {}

    static Optional<String> reconcile(DesiredState desired, ObservedState observed) {
        int diff = desired.replicas() - observed.runningReplicas();
        if (diff > 0) {
            return Optional.of("scale up by " + diff);
        }
        if (diff < 0) {
            return Optional.of("scale down by " + (-diff));
        }
        return Optional.empty(); // already matches the desired state
    }

    public static void main(String[] args) {
        System.out.println(reconcile(new DesiredState(3), new ObservedState(1)).orElse("in sync"));
    }
}
```

Real operators run this loop against the API server, triggered by watch events, and requeue work on failure. Frameworks such as Operator SDK and Kubebuilder help build them.

## How it works / Step by step
1. A Service selects pods by label and gets a DNS name and virtual IP.
2. A NetworkPolicy, if present, filters the traffic to and from the selected pods.
3. A mesh sidecar, if used, handles mTLS and retries for service-to-service calls.
4. Helm renders templates with values and records each install or upgrade as a revision.
5. An operator watches its custom resources and reconciles the cluster toward the declared state.

## Common pitfalls
- Assuming network policies are enforced. The network plugin must support them.
- Forgetting egress rules, so pods can no longer reach DNS or external APIs after a default-deny policy.
- Hard-coding pod IPs or node addresses in configuration.
- Editing Helm-managed resources by hand, which the next `helm upgrade` overwrites.
- Installing a service mesh for a single service with simple traffic needs.
- Writing an operator that does not handle repeated reconciles idempotently.

!!! tip "Interview tip"
    **Q: How do you restrict which services can call the orders service?**
    Use a NetworkPolicy with a default-deny baseline and an explicit allow for the calling pods' labels. For identity-based control between services, a service mesh can add mutual TLS and authorization rules. Explain that the policy only works if the CNI plugin enforces it.

## Quick recap
- Pods reach each other by IP; applications use Service DNS names instead.
- NetworkPolicies restrict traffic, but only where the network plugin enforces them.
- Service meshes add mTLS, retries, and traffic splitting at the cost of complexity.
- Helm packages manifests as charts with values and tracked, rollback-able releases.
- CRDs add API types; operators reconcile them toward the desired state.

**See also:** [Kubernetes Architecture and Objects](kubernetes-architecture-objects.md), [Config, Storage and Health](config-storage-health.md), [Continuous Deployment and IaC](../17-cicd/continuous-deployment-iac.md)
