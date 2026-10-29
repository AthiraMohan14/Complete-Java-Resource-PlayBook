# Kubernetes Architecture and Objects

Kubernetes is a control system: you declare the state you want, and controllers continuously work to make the cluster match it. Interviewers ask about the architecture to test whether you can explain what happens after `kubectl apply`, and about the core objects to test whether you know when to use a Deployment, a StatefulSet, or a Service.

## Core concepts

### Control plane
The control plane makes global decisions about the cluster.

- **kube-apiserver**: the front door. Every read and write goes through its REST API, including requests from `kubectl` and from other components.
- **etcd**: the consistent key-value store that holds all cluster state. Only the API server talks to it directly.
- **kube-scheduler**: assigns each unscheduled pod to a node that has enough free resources and matches its constraints.
- **kube-controller-manager**: runs controllers, such as the ReplicaSet controller, that compare desired and actual state and act on the difference.

### Worker nodes
Each worker node runs the workloads.

- **kubelet**: an agent that makes sure the containers described in pod specs are running and healthy on its node.
- **kube-proxy**: maintains network rules so Service addresses reach the right pods.
- **Container runtime**: the component that runs containers, such as containerd, through the Container Runtime Interface.

### Clusters, namespaces, and RBAC
A **cluster** is the control plane plus its nodes. A **namespace** is a logical partition inside a cluster. Names must be unique per namespace, and quotas and policies can be applied per namespace, which is the usual basis for multi-tenancy.

**RBAC** (role-based access control) decides who can do what:

| Object | Scope | Purpose |
|---|---|---|
| `Role` | Namespace | Grants permissions on resources inside one namespace |
| `ClusterRole` | Cluster | Grants permissions cluster-wide, or on non-namespaced resources |
| `RoleBinding` | Namespace | Attaches a Role or ClusterRole to subjects in one namespace |
| `ClusterRoleBinding` | Cluster | Attaches a ClusterRole to subjects everywhere |
| `ServiceAccount` | Namespace | Identity used by pods to call the API |

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: orders
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

### Pods
A **pod** is the smallest deployable unit. It groups one or more containers that share a network namespace (one IP address), can share volumes, and are scheduled together. Pods are ephemeral: when one dies, it is replaced by a new pod with a new IP. Application code should never depend on a pod's IP address.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: orders-pod
  labels:
    app: orders
spec:
  containers:
    - name: orders
      image: orders-service:1.4.0
      ports:
        - containerPort: 8080
```

You rarely create bare pods. Higher-level controllers create and replace them.

### Deployments and ReplicaSets
A **ReplicaSet** keeps a specified number of identical pods running. If a pod is removed or fails, the ReplicaSet creates another.

A **Deployment** manages ReplicaSets for stateless applications. Changing the pod template creates a new ReplicaSet, and the Deployment shifts pods from the old one to the new one, which is a **rolling update**. Old ReplicaSets are kept so you can **roll back**.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orders
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: orders
    spec:
      containers:
        - name: orders
          image: orders-service:1.4.0
          ports:
            - containerPort: 8080
```

Useful commands: `kubectl rollout status deployment/orders`, `kubectl rollout undo deployment/orders`.

### StatefulSets
A **StatefulSet** suits workloads that need stable identity and storage: databases, brokers, and clustered systems. Each pod gets an ordered, stable name (`db-0`, `db-1`), a stable network identity, and its own persistent volume claim that follows the pod. Pods start and stop in order by default.

Use a Deployment for stateless services. Use a StatefulSet when each replica is distinct.

### Services
A **Service** gives a stable name and virtual IP to a set of pods selected by labels, so clients do not track pod IPs.

| Type | Behaviour |
|---|---|
| `ClusterIP` (default) | Reachable only inside the cluster |
| `NodePort` | Opens the same port on every node |
| `LoadBalancer` | Asks the cloud provider for an external load balancer |
| `ExternalName` | Returns a DNS CNAME to an external hostname, with no proxying |

```yaml
apiVersion: v1
kind: Service
metadata:
  name: orders
spec:
  type: ClusterIP
  selector:
    app: orders
  ports:
    - port: 80
      targetPort: 8080
```

### Ingress and the Gateway API
An **Ingress** routes external HTTP and HTTPS traffic to Services by host and path. It needs an ingress controller installed in the cluster to take effect. The **Gateway API** is the successor to Ingress for new work. It separates responsibilities more clearly and supports more protocols.

## kubectl quick reference
`kubectl` is the command-line client for the API server. Each command below reads or changes state through that API, so it obeys the same RBAC rules as any other client.

| Command | Purpose |
|---|---|
| `kubectl get pods -n orders` | List objects of one kind in a namespace. Add `-o wide` for node and IP, or `-o yaml` for the full object. |
| `kubectl describe pod orders-pod` | Show the object's spec, status, conditions, and recent events. Start here when a pod is stuck in Pending or CrashLoopBackOff. |
| `kubectl logs orders-pod` | Print the container's stdout and stderr. Use `-f` to follow, `--previous` to read the logs of the last crashed container, and `-c` to pick a container in a multi-container pod. |
| `kubectl exec -it orders-pod -- sh` | Run a command inside a running container. Use `sh` for images without bash. Avoid this for production debugging where possible; prefer logs and metrics. |
| `kubectl port-forward svc/orders 8080:80` | Forward a local port to a Service or pod for testing, without exposing it publicly. |
| `kubectl apply -f orders-deployment.yaml` | Create or update objects from a manifest. The command is repeatable, so the same file can be applied again. |
| `kubectl delete -f orders-deployment.yaml` | Remove the objects described in a manifest. |
| `kubectl rollout status deployment/orders` | Wait and report progress of a rolling update. Useful in CI scripts. |
| `kubectl rollout history deployment/orders` | List the recorded revisions of a Deployment. |
| `kubectl rollout undo deployment/orders` | Return to the previous revision. Add `--to-revision=N` to pick a specific one. |

Typical debugging flow for a failing pod:

```bash
kubectl get pods -n orders -o wide        # Which pods, which nodes, what state
kubectl describe pod orders-7d9f-abcde    # Events: scheduling, image pulls, probe failures
kubectl logs orders-7d9f-abcde --previous # Output from the crashed container
kubectl port-forward pod/orders-7d9f-abcde 8080:8080   # Test the endpoint locally
```

## How it works / Step by step
1. You run `kubectl apply` with a Deployment manifest. The API server validates it and stores it in etcd.
2. The Deployment controller creates a ReplicaSet, which creates pods.
3. The scheduler assigns each pod to a node.
4. The kubelet on that node starts the containers through the container runtime.
5. A Service selects the pods by label, and kube-proxy routes traffic to whichever pods are ready.

## Common pitfalls
- Hard-coding pod IP addresses. Use Service names.
- Using a Deployment for a database that needs stable identity and storage.
- Forgetting that Services select pods by label. A label typo means no traffic arrives, with no error.
- Creating bare pods, which are not recreated when they die.
- Treating a namespace as a security boundary without RBAC and network policies.
- Expecting an Ingress to work without an ingress controller.

!!! tip "Interview tip"
    **Q: What happens when you create a Deployment?**
    The API server stores the object in etcd. The Deployment controller creates a ReplicaSet. The ReplicaSet creates pods. The scheduler binds each pod to a node, and the kubelet starts the containers. The control loops keep running after that, so a failed pod is replaced automatically.

## Quick recap
- The control plane (API server, etcd, scheduler, controller manager) decides; nodes (kubelet, kube-proxy, runtime) run.
- Pods are ephemeral and share a network identity within the pod.
- Deployments manage stateless replicas with rolling updates and rollbacks; StatefulSets keep stable identity and storage.
- Services give stable names to changing pods; Ingress and the Gateway API route external traffic.
- Namespaces partition the cluster; RBAC controls who can change what.

**See also:** [Config, Storage and Health](config-storage-health.md), [Networking, Helm and Operators](networking-helm-operators.md), [Docker Fundamentals](../15-docker/docker-fundamentals.md)
