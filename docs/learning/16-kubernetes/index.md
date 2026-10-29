# Kubernetes and Orchestration

Kubernetes runs containers across a cluster of machines. It schedules workloads, restarts failed containers, rolls out new versions, and gives services stable names and addresses. This section covers the control plane and core objects, configuration and storage, health and lifecycle, networking and extension points.

---

## Topics

### [Kubernetes Architecture and Objects](kubernetes-architecture-objects.md)
**control plane - kubelet - namespaces - RBAC - pods - deployments - StatefulSets - services - ingress**
How a cluster is built, and the core objects used to run and expose applications.

### [Config, Storage and Health](config-storage-health.md)
**ConfigMaps - Secrets - PersistentVolumes - probes - graceful shutdown - resource limits**
Injecting configuration, keeping data, running one-off and scheduled work, and telling the platform when a container is healthy.

### [Networking, Helm and Operators](networking-helm-operators.md)
**service discovery - network policies - service mesh - Helm charts - CRDs - operators**
Pod and service networking, restricting traffic, packaging applications, and extending the API with custom controllers.
