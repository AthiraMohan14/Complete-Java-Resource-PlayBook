# Continuous Deployment and Infrastructure as Code

Continuous deployment releases every change that passes the pipeline, and continuous delivery keeps it ready to release at the push of a button. Either way, the release itself must be safe: the strategy controls how traffic moves to the new version, infrastructure is described in code so environments are reproducible, and automated checks decide whether to keep or roll back. Interviewers ask about these topics to test risk management, not just tool names.

## Core concepts

### Deployment strategies
Each strategy trades off speed, cost, and risk differently.

- **Blue-green**: two identical environments, blue (live) and green (new). Deploy to green, verify it, then switch traffic at the router or load balancer. Rollback is switching back. It doubles capacity during the switch.
- **Canary**: send a small share of traffic to the new version, watch its metrics, then increase the share gradually. Rollback removes the canary. It limits the blast radius of a bad release.
- **Rolling**: replace instances a few at a time, so some old and some new versions run together. It needs no extra capacity but requires that old and new versions be compatible during the rollout.
- **Shadow**: the new version receives a copy of production traffic, but its responses are discarded. It tests real load and behaviour without user impact, though side effects such as writes must be handled carefully.

In Kubernetes, the rolling strategy is the Deployment default (see the Kubernetes section). Canary and blue-green are usually built on traffic-splitting features of a mesh, an ingress controller, or a progressive-delivery tool.

#### Kubernetes strategies in practice
Rolling update is configured on the Deployment. `maxSurge` allows extra pods during the rollout, and `maxUnavailable: 0` keeps full capacity. A new pod receives traffic only after its readiness probe passes:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: orders
  template:
    metadata:
      labels:
        app: orders
    spec:
      containers:
        - name: orders
          image: registry.example.com/orders:1.4.1
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
```

Kubernetes does not roll back a Deployment automatically. If the new pods never become ready, the rollout stalls and `progressDeadlineSeconds` marks it as failed. Someone, or the pipeline, must run `kubectl rollout undo`.

Blue-green uses two Deployments and a Service whose selector decides which one receives traffic. Each Deployment's pod template carries a `track: blue` or `track: green` label. Both Deployments run during the switch, so capacity doubles briefly:

```bash
kubectl apply -f orders-green.yaml                       # green runs the new version; Service still selects blue
kubectl patch service orders -p '{"spec":{"selector":{"app":"orders","track":"green"}}}'
kubectl patch service orders -p '{"spec":{"selector":{"app":"orders","track":"blue"}}}'   # instant rollback
```

Canary without a mesh is approximate. Run nine stable pods and one canary pod behind the same Service, and the canary gets roughly 10% of connections. Kubernetes balances by connection, not by request, so the split drifts with traffic patterns. A mesh or ingress controller gives exact weights, as shown in the Helm and Istio section of the networking page.

Shadow traffic uses the mesh too. Istio's `mirror` field copies each request to a second subset and discards that subset's response:

```yaml
http:
  - route:
      - destination:
          host: orders
          subset: stable
    mirror:
      host: orders
      subset: canary
    mirrorPercentage:
      value: 100.0
```

Mirrored requests can cause side effects, such as a second charge or a second email. Point the shadow version at sandbox dependencies, or block writes, before you mirror production traffic.

Progressive-delivery tools such as Flagger automate the canary steps. They raise the canary weight in increments, check success rate and latency from Prometheus at each step, and roll back when a threshold is breached.

Rollout commands for day-to-day control:

```bash
kubectl rollout status deployment/orders
kubectl rollout history deployment/orders
kubectl rollout undo deployment/orders                    # previous revision
kubectl rollout undo deployment/orders --to-revision=3    # a specific revision
kubectl rollout pause deployment/orders                   # hold mid-rollout to inspect
kubectl rollout resume deployment/orders
```

### Infrastructure as code (IaC)
IaC describes servers, networks, databases, and permissions in versioned files, so environments can be created, compared, and recreated.

**Terraform** uses HCL (HashiCorp Configuration Language). You declare resources, and Terraform computes a plan of changes against the recorded **state**. Key ideas:

- **State** maps configuration to real resources. Store it remotely with locking so two people cannot apply at once.
- **Modules** package reusable resource groups with input variables and outputs.
- `terraform plan` shows the changes before `terraform apply` makes them.

```hcl
resource "aws_s3_bucket" "orders_exports" {
  bucket = "example-orders-exports"
}

output "bucket_name" {
  value = aws_s3_bucket.orders_exports.bucket
}
```

**CloudFormation** is AWS's native IaC service. It uses JSON or YAML templates and manages resources as stacks. **Ansible** is primarily for configuration management: installing packages, templating files, and configuring machines, usually with idempotent playbooks.

Terraform and CloudFormation provision infrastructure. Ansible configures what runs on it. Some teams use all three, and some use only one.

### Secrets in pipelines
Pipelines need credentials to deploy, but those credentials must not appear in code or logs.

- **GitHub Secrets** and **GitLab CI variables** store values encrypted and expose them to jobs as environment variables. Mark them masked and protected.
- **HashiCorp Vault** or a cloud key vault issues short-lived credentials on demand, which is safer than long-lived keys.
- Prefer OpenID Connect federation from the CI system to the cloud, so the pipeline needs no stored cloud keys at all.

```yaml
# GitHub Actions: deploy using a secret, never a literal value
- name: Deploy
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: ./scripts/deploy.sh
```

### After deployment: verification and rollback
A deployment is not finished when the new version starts. Post-deployment steps include:

- **Smoke tests**: a few quick checks of critical paths, such as login or a payment status call.
- **Health checks**: readiness and liveness signals from the platform, plus application metrics such as error rate and latency.
- **Automatic rollback**: if smoke tests or health thresholds fail, the pipeline reverts to the previous version.
- **Approvals and notifications**: manual approval gates for sensitive environments, and alerts to the team when a deployment starts, succeeds, or fails.

A deployment without automated rollback relies on a person noticing a problem and responding quickly. Build the rollback path before it is needed.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.io.IOException;

public class SmokeTest {
    public static void main(String[] args) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://orders.example.com/actuator/health"))
                .GET()
                .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            System.exit(1); // a non-zero exit fails the pipeline step and triggers rollback logic
        }
        System.out.println("Smoke test passed");
    }
}
```

The URL is a placeholder for illustration. The non-zero exit code is what the pipeline reads.

### Choosing a strategy

| Strategy | Extra capacity needed | Rollback speed | Old and new versions run together | Best when |
|---|---|---|---|---|
| Blue-green | Yes, a full second environment | Very fast (switch back) | No, only one serves users at a time | Changes need an all-or-nothing switch |
| Canary | A small share of extra capacity | Fast (remove the canary) | Yes, by design | Risk must be measured on real traffic |
| Rolling | Little or none | Moderate (roll back instance by instance) | Yes, during the rollout | Old and new versions are compatible |
| Shadow | Yes, to process copied traffic | Not applicable to users | Yes, but only the old version responds | Validating behaviour and load before exposure |

Strategy choice follows the change. A schema migration that breaks old code rules out rolling and canary unless the migration is split into compatible steps.

### Promoting one artifact through environments
Build the artifact once and promote the same version through development, staging, and production. Only configuration changes per environment, and that configuration lives in version control or a secret store. Rebuilding for each environment means production runs code that was never tested. Record which artifact version is in each environment, so audits and rollbacks have a clear answer.

### Approvals, windows, and change control
Sensitive environments often need a manual approval step, and some teams restrict deployments to certain hours or freeze them around peak periods. Automate what you can: approval gates in the pipeline, notifications with a link to the change, and a record of who approved what. Treat frequent manual approvals as a signal to improve the automated checks instead.

### Configuration management with Ansible
Ansible playbooks describe the desired state of machines. A small example that installs a runtime and deploys a JAR:

```yaml
- name: Configure the orders host
  hosts: orders
  become: true
  tasks:
    - name: Ensure the JRE package is installed
      ansible.builtin.package:
        name: openjdk-21-jre-headless
        state: present

    - name: Copy the application JAR
      ansible.builtin.copy:
        src: build/app.jar
        dest: /opt/orders/app.jar
        mode: "0644"
```

Modules such as `package` and `copy` are idempotent: running the playbook again changes nothing when the machine already matches. The package name here is a Debian-family example and differs on other distributions.

### Drift and state
Infrastructure drifts when someone changes a resource by hand. Detect it by running a plan regularly and alerting on differences, and fix it by changing code and applying, not by editing the console. The same principle applies to Kubernetes: a GitOps tool that reconciles the cluster against a repository prevents manual changes from lingering.

### GitOps with Argo CD
GitOps makes a Git repository the single source of truth for what runs in a cluster. A controller inside the cluster compares the desired state in Git with the live state and applies the difference. Nobody runs `kubectl apply` by hand, so every change has a commit, a reviewer, and a history. **Argo CD** is a widely used GitOps controller. Flux works on the same principle.

An Argo CD **Application** connects one Git path to one cluster and namespace:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: orders
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://git.example.com/platform/orders-config.git
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: orders
  syncPolicy:
    automated:
      prune: true       # delete cluster objects that were removed from Git
      selfHeal: true    # revert manual changes that drift from Git
```

A common layout keeps shared manifests in `base/` and one `overlays/<environment>/` folder per environment, with Kustomize or Helm rendering the difference. A deployment then follows this path:

1. CI builds the image once, pushes it to the registry, and runs the tests.
2. CI opens a commit (or pull request) that changes the image tag in `overlays/staging`.
3. After review, the change merges to the branch Argo CD tracks, and Argo CD syncs it (on a poll or a webhook).
4. The same tag is promoted to `overlays/prod` by another commit, so production runs the artifact that staging tested.

Rolling back is a `git revert` of the change, and the sync brings the cluster back. Keep CI and CD separate: CI should not hold cluster credentials when a GitOps controller can pull the change instead. Secrets cannot sit in plain text in Git. Use an encrypted secret format such as Sealed Secrets or SOPS, or reference a vault.

## How it works / Step by step
1. The pipeline builds and publishes a versioned artifact.
2. Terraform plans and applies infrastructure changes, reviewed before apply.
3. The chosen strategy shifts traffic to the new version in stages or all at once.
4. Smoke tests and health checks run against the new version.
5. If checks pass, the release completes; if they fail, the pipeline rolls back to the previous version.

## Common pitfalls
- Running `terraform apply` by hand against shared state, which causes drift and conflicts.
- Storing Terraform state locally, or without locking.
- Choosing a rolling update when old and new versions cannot run together.
- Using blue-green without checking that the database schema works for both versions.
- Long-lived cloud keys in pipeline secrets, rather than short-lived credentials.
- Declaring a deployment successful without any post-deployment checks.

!!! tip "Interview tip"
    **Q: How would you release a risky change to an order service with minimal impact?**
    Use a canary: route a small percentage of traffic to the new version, watch error rate and latency against the current version, then increase the share. Have automatic rollback tied to those metrics, and make sure the database changes are backward compatible so both versions can run during the rollout.

## Quick recap
- Blue-green, canary, rolling, and shadow strategies trade off capacity, speed, and risk.
- Terraform, CloudFormation, and Ansible describe infrastructure or configuration as versioned code.
- Pipelines should use short-lived credentials and secret stores, not literal values.
- Smoke tests, health checks, and automatic rollback decide whether a release stands.
- GitOps tools such as Argo CD sync a cluster to a Git repository; promote the same image tag through environments by commit.
- Make releases reversible before you need to reverse one.

**See also:** [Continuous Integration](continuous-integration.md), [Git Workflows](git-workflows.md), [Networking, Helm and Operators](../16-kubernetes/networking-helm-operators.md), [Cloud Platforms](../18-cloud/index.md)
