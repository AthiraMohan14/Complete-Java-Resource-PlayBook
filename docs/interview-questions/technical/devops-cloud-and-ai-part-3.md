# DevOps, Cloud, Observability, and AI Questions (Part 3 of 3)

Questions on orchestration compared with automation, Linux commands and scripts for deploying and maintaining a Java service, log rotation and backups, and how IAM Roles for Service Accounts (IRSA) gives pods AWS access. Read [Part 1](devops-cloud-and-ai-part-1.md) and [Part 2](devops-cloud-and-ai-part-2.md) first if you have not.

Continued from [Part 2](devops-cloud-and-ai-part-2.md).

---

## 26. What is orchestration in software and DevOps, and how does it differ from automation?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Automation runs one task without a person doing it, such as a script that builds a jar or a pipeline step that runs tests. Orchestration coordinates many automated tasks or services: it decides the order, handles dependencies, tracks state, retries failures, and reacts when something goes wrong. A deployment pipeline that builds, tests, migrates the database, and rolls out to three regions is orchestration. Each step inside it is automation.

### Explanation
Automation answers the question "how do I do this step without typing it?" Orchestration answers "how do I run many steps, possibly on many machines, in the right order and recover when one fails?"

Examples:
- **Automation:** a shell script that copies a jar to a server and restarts a service.
- **Orchestration in DevOps:** a workflow that runs the script on a fleet, waits for health checks, rolls back if the error rate rises, and records the result.
- **Orchestration in containers:** Kubernetes decides which node runs each Pod, restarts failed containers, scales replicas, and rolls out new versions while keeping a minimum number of Pods available.
- **Orchestration in software design:** a saga orchestrator sends commands to several services and tracks which steps succeeded, in contrast with choreography, where each service reacts to events without a central coordinator.

A useful test: if removing the coordinator would leave each step working, you have automation. If the coordinator holds the state and decides what runs next, you have orchestration.

### When to use / pitfalls
- Start with automation. Orchestration adds a component to design, secure, and keep available.
- A central orchestrator is a single point of failure unless it stores its state durably and can resume.
- Idempotent steps make orchestration safe to retry.
- Do not confuse the word with the tool. Kubernetes, Argo Workflows, and cloud state machines are orchestrators; a Jenkins job or a shell script is usually automation.

**See also:** [Kubernetes architecture and objects](../../learning/16-kubernetes/kubernetes-architecture-objects.md), [Event-driven architecture](../../learning/13-messaging/event-driven-architecture.md), [Continuous integration](../../learning/17-cicd/continuous-integration.md)

</details>

---

## 27. Which Linux commands and scripts help deploy and maintain a Java application?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `java -version` to confirm the runtime, `systemctl` and `journalctl` to run and inspect the service, `ss` and `lsof` to check ports, `ps` and `top` to find the process, `df`, `du`, and `free` to check disk and memory, and `curl` against a health endpoint to confirm the app is up. A deployment script copies the new jar into place, swaps it in, restarts the service, and checks health. Run the service under systemd rather than with `nohup`, because systemd restarts it, captures its logs, and starts it on boot.

### Explanation
Commands for everyday checks:

```bash
java -version                          # runtime in use
ps -ef | grep order-service            # is the process running?
ss -tlnp | grep 8080                   # which process listens on the port?
lsof -i :8080                          # same question, different tool
df -h && du -sh /var/log/order-service # disk space and log size
free -m                                # memory
journalctl -u order-service -n 200 --no-pager   # recent service logs
tail -f /var/log/order-service/app.log          # follow an application log
grep -i "error" /var/log/order-service/app.log | tail -50
curl -fsS http://localhost:8080/actuator/health # health endpoint
```

A systemd unit runs the jar and restarts it on failure:

```ini
[Unit]
Description=Order service
After=network-online.target

[Service]
User=app
EnvironmentFile=/etc/order-service/env
ExecStart=/usr/bin/java -Xms512m -Xmx512m -jar /opt/order-service/app.jar
Restart=on-failure
SuccessExitStatus=143

[Install]
WantedBy=multi-user.target
```

Exit status 143 is what the JVM returns after SIGTERM (128 plus 15), so treating it as success avoids false restart alarms when systemd stops the service normally.

A deployment script that replaces the jar and checks health:

```bash
#!/usr/bin/env bash
# Usage: deploy.sh <path-to-new-jar>
set -euo pipefail

NEW_JAR="$1"
APP_DIR=/opt/order-service
SERVICE=order-service

sudo install -o app -g app -m 0644 "$NEW_JAR" "$APP_DIR/app.jar.new"
sudo mv "$APP_DIR/app.jar.new" "$APP_DIR/app.jar"   # rename is atomic on the same filesystem
sudo systemctl restart "$SERVICE"

for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8080/actuator/health > /dev/null; then
    echo "service is healthy"
    exit 0
  fi
  sleep 2
done

echo "health check failed; recent logs:" >&2
journalctl -u "$SERVICE" -n 100 --no-pager >&2
exit 1
```

### When to use / pitfalls
- Keep the previous jar as `app.jar.prev` so rollback is one `mv` and one restart.
- `set -euo pipefail` stops a script at the first error instead of continuing with a broken state.
- Check the health endpoint with a timeout; a hung process can otherwise block the script forever.
- Keep secrets in an environment file with restricted permissions, not on the command line, where `ps` can show them.

**See also:** [Linux and shell basics](../../learning/17-cicd/continuous-integration.md#linux-commands-for-deployment-and-maintenance), [Containers and Compose](../../learning/15-docker/containers-and-compose.md)

</details>

---

## 28. How do you automate log rotation or backups on a Linux server?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
Use `logrotate` for log files: it rotates, compresses, and deletes old logs on a schedule that the system already runs daily. Use a small backup script that writes a timestamped, compressed dump, removes dumps older than the retention period, and copies them off the server. Schedule the script with a systemd timer or cron, log its output, and test a restore, because a backup you have never restored is not a proven backup.

### Explanation
A `logrotate` rule for an application's log directory:

```
/var/log/order-service/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

`copytruncate` copies the file and then truncates the original, which works when the application keeps the file open and cannot reopen it. Logging frameworks that roll files themselves, such as Logback's rolling file appender, need no `copytruncate`; set their retention in the framework instead. Check a rule with `logrotate -d /etc/logrotate.d/order-service` (a dry run) and force a rotation with `logrotate -f` to test it.

A backup script for a PostgreSQL database:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=/var/backups/orders-db
KEEP_DAYS=7
STAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"
# Credentials come from ~/.pgpass, not from the command line
pg_dump -h db-host -U orders -d orders -Fc -f "$BACKUP_DIR/orders-$STAMP.dump"
find "$BACKUP_DIR" -name 'orders-*.dump' -mtime +"$KEEP_DAYS" -delete
```

Schedule it with cron, appending output to a log so failures are visible:

```
0 2 * * * /opt/scripts/backup.sh >> /var/log/orders-backup.log 2>&1
```

A systemd timer is the alternative on modern distributions and gives you `journalctl` logs and missed-run handling.

### When to use / pitfalls
- Copy backups off the machine (object storage or another host). A backup on the same disk fails with the server.
- Alert when a backup job fails or when the newest backup is older than expected. A silent cron job is the usual cause of "we had no backup".
- Encrypt backups that contain personal data and restrict their file permissions.
- Test restores on a schedule and record how long they take; that number is your real recovery time.

**See also:** [Continuous integration](../../learning/17-cicd/continuous-integration.md#linux-commands-for-deployment-and-maintenance), [Data and persistence](data-and-persistence-part-1.md), [Alerting and health checks](../../learning/20-observability/alerting-health-checks.md)

</details>

---

## 29. What is IRSA (IAM Roles for Service Accounts), and how does a pod assume an IAM role without credentials?

<details markdown="1">
<summary>View Answer</summary>

### Direct answer
IRSA lets a Kubernetes pod on Amazon EKS get AWS permissions through an IAM role, using the pod's Kubernetes service account instead of stored access keys. The cluster issues a signed token for the service account, and AWS STS trusts that token through the cluster's OIDC identity provider. The pod's AWS SDK exchanges the token for temporary credentials for the role. No access key is stored in the pod, the image, or a Secret.

### Explanation
The setup has three parts:
1. **An OIDC identity provider** for the EKS cluster is registered in IAM, so AWS trusts tokens the cluster signs.
2. **An IAM role** whose trust policy allows only one service account in one namespace to assume it:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Federated": "arn:aws:iam::111122223333:oidc-provider/oidc.eks.eu-west-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE"
  },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "oidc.eks.eu-west-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE:sub": "system:serviceaccount:orders:order-service",
      "oidc.eks.eu-west-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE:aud": "sts.amazonaws.com"
    }
  }
}
```

3. **A service account annotated with the role ARN**, and a pod that uses it:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-service
  namespace: orders
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::111122223333:role/order-service-role
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: orders
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      serviceAccountName: order-service
      containers:
        - name: app
          image: example/order-service:1.0.0
```

When the pod starts, the EKS pod identity webhook injects environment variables (`AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE`) and mounts a projected service account token. The AWS SDK's default credential chain sees the web identity token, calls `AssumeRoleWithWebIdentity`, and receives temporary credentials that refresh automatically. The Java code needs no keys: create clients with the default provider chain and the SDK finds the credentials.

### When to use / pitfalls
- Scope the trust policy tightly with the `sub` condition. A wildcard lets other service accounts assume the role.
- Give the role only the permissions the service needs, and do not attach administrator access for convenience.
- The pod's node role is a separate identity; IRSA is the per-workload way to get AWS access.
- Newer EKS setups also offer EKS Pod Identity as an alternative. Check which one your cluster uses before answering in an interview.

**See also:** [AWS](../../learning/18-cloud/aws.md), [Kubernetes architecture and objects](../../learning/16-kubernetes/kubernetes-architecture-objects.md), [Spring and security](spring-and-security-part-1.md)

</details>

---

## Quick recap

- Automation runs a task without a person; orchestration coordinates many tasks, their order, their state, and their recovery.
- Run a Java service under systemd, check health with an endpoint, and keep the previous jar for rollback.
- Rotate logs with `logrotate` and back up on a schedule, off the machine, with tested restores.
- IRSA binds an IAM role to a Kubernetes service account through the cluster's OIDC provider, so pods receive temporary credentials and no stored keys.

**See also:** [DevOps, cloud, and AI, part 1](devops-cloud-and-ai-part-1.md), [DevOps, cloud, and AI, part 2](devops-cloud-and-ai-part-2.md), [Architecture and distributed systems](architecture-and-distributed.md), [Technical questions index](index.md)
