#!/usr/bin/env python3
"""
StreamingApp Kubernetes Healing Controller
==========================================
Watches pod events in real time and performs automated remediation.

Healing actions this controller performs:
1. CrashLoopBackOff  → delete pod (Deployment recreates it fresh)
2. Evicted pods      → delete stale pod object (cleans up cluster state)
3. OOMKilled         → delete pod (Deployment recreates with same limits)
4. ImagePullBackOff  → log alert (requires manual ECR investigation)

Design decisions:
- Uses Kubernetes watch API for real-time event detection
- Runs a periodic full scan every 60s as a safety backstop
- Cooldown per pod prevents thrashing (repeated delete loops)
- All actions written to structured JSON log for audit trail
- Runs as non-root user inside container (security best practice)
"""

import time
import logging
import json
import datetime
import os
import threading
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

# ── Logging setup ─────────────────────────────────────────────────────────────
# Format: timestamp [LEVEL] logger_name: message
# This format works well with CloudWatch Logs and Loki log aggregation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger("healing-controller")

# ── Configuration from environment variables ──────────────────────────────────
# Using env vars (not hardcoded values) so we can change behavior
# without rebuilding the Docker image — just update the Deployment env section

# Which namespace to watch — "default" for our StreamingApp
NAMESPACE = os.getenv("WATCH_NAMESPACE", "default")

# How many restarts before we intervene
# 3 means: first 3 restarts we let Kubernetes handle naturally
# On the 4th restart we step in and force a fresh pod
RESTART_THRESHOLD = int(os.getenv("RESTART_THRESHOLD", "3"))

# How long to wait before taking action on the same pod again
# 300 seconds = 5 minutes
# Prevents: delete → pod crashes again → delete → infinite loop
# During cooldown: pod gets time to stabilize or alert humans
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "300"))

# Where to write the healing action log file
HEALING_LOG_FILE = os.getenv("HEALING_LOG", "/var/log/healing/actions.log")

# ── Cooldown tracking ─────────────────────────────────────────────────────────
# Dictionary: pod_name → timestamp of last healing action
# Stored in memory — resets if controller pod restarts (acceptable trade-off)
_cooldowns: dict = {}


def load_k8s_config():
    """
    Load Kubernetes configuration.
    
    Tries in-cluster config first (works when running as a pod inside EKS).
    Falls back to local kubeconfig (works during local development/testing).
    
    In-cluster config uses the ServiceAccount token mounted at:
    /var/run/secrets/kubernetes.io/serviceaccount/token
    This token is automatically rotated by Kubernetes every 24 hours.
    """
    try:
        config.load_incluster_config()
        log.info("Loaded in-cluster config (running inside EKS)")
    except config.ConfigException:
        config.load_kube_config()
        log.info("Loaded local kubeconfig (running in development)")


def log_action(action: str, pod: str, namespace: str, reason: str, result: str):
    """
    Write a structured JSON record of every healing action.
    
    Written to both:
    1. stdout → captured by Kubernetes, visible via kubectl logs
    2. File   → can be shipped to CloudWatch or Loki for dashboards
    
    The structured JSON format allows log aggregation tools to:
    - Filter by action type (show me all CrashLoop restarts today)
    - Count by pod (which pod needed healing most?)
    - Alert on result=error (healing itself is failing)
    """
    record = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "action":    action,
        "pod":       pod,
        "namespace": namespace,
        "reason":    reason,
        "result":    result,
    }
    # HEALING_ACTION prefix makes these easy to grep from mixed logs
    log.info("HEALING_ACTION %s", json.dumps(record))
    
    # Also write to file for persistent storage
    try:
        os.makedirs(os.path.dirname(HEALING_LOG_FILE), exist_ok=True)
        with open(HEALING_LOG_FILE, "a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as e:
        log.warning("Could not write to healing log file: %s", e)


def is_on_cooldown(pod_name: str) -> bool:
    """
    Check if a pod is within the cooldown window.
    
    Why cooldowns matter:
    Without cooldown: heal → pod crashes → heal → pod crashes → infinite loop
    With cooldown:    heal → wait 5 min → if still broken → heal again
                      5 minutes gives time for: image pull retry,
                      MongoDB connection stabilization, human intervention
    """
    last_action_time = _cooldowns.get(pod_name, 0)
    time_since_last_action = time.time() - last_action_time
    return time_since_last_action < COOLDOWN_SECONDS


def set_cooldown(pod_name: str):
    """Record the timestamp of a healing action for this pod."""
    _cooldowns[pod_name] = time.time()


def delete_pod(v1: client.CoreV1Api, pod_name: str, namespace: str, reason: str):
    """
    Delete a pod to trigger fresh recreation by its Deployment.
    
    Why deleting works:
    Every pod in our cluster is managed by a Deployment → ReplicaSet.
    When we delete a pod, the ReplicaSet controller immediately notices
    that actual replicas < desired replicas and creates a new pod.
    The new pod starts completely fresh — new container process,
    cleared memory, fresh connection to MongoDB.
    
    grace_period_seconds=0 means immediate deletion.
    For a crashing pod this is fine — it is already broken.
    For healthy pods we would use a grace period to allow
    in-flight requests to complete first.
    """
    if is_on_cooldown(pod_name):
        log.info("Pod %s is in cooldown window — skipping healing action", pod_name)
        return
    
    try:
        v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace,
            body=client.V1DeleteOptions(grace_period_seconds=0)
        )
        set_cooldown(pod_name)
        log_action("delete_pod", pod_name, namespace, reason, "success")
        log.info("Successfully deleted pod %s — reason: %s", pod_name, reason)
        
    except ApiException as e:
        if e.status == 404:
            # Pod already gone — that's fine, nothing to do
            log.info("Pod %s already deleted (404) — no action needed", pod_name)
        else:
            log.error("Failed to delete pod %s: HTTP %s %s", pod_name, e.status, e.reason)
            log_action("delete_pod", pod_name, namespace, reason, f"error: {e.status}")


def handle_crash_loop(v1: client.CoreV1Api, pod: client.V1Pod):
    """
    Detect and heal CrashLoopBackOff pods.
    
    CrashLoopBackOff means:
    - Container started, ran, crashed (non-zero exit code)
    - Kubernetes tried to restart it
    - This happened enough times that Kubernetes is now
      adding exponential backoff delays between restarts
    - The pod is effectively stuck — not serving traffic
    
    Common causes in StreamingApp:
    - MongoDB connection string wrong → auth/streaming/admin crash
    - Missing environment variable → any service crashes on startup
    - Port already in use → service cannot bind (rare in containers)
    - Code bug in startup sequence → immediate crash
    """
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    
    if not pod.status or not pod.status.container_statuses:
        return
    
    for cs in pod.status.container_statuses:
        if cs.restart_count >= RESTART_THRESHOLD:
            log.warning(
                "CrashLoopBackOff detected: pod=%s container=%s restarts=%d",
                pod_name, cs.name, cs.restart_count
            )
            delete_pod(
                v1, pod_name, namespace,
                f"CrashLoopBackOff: restarts={cs.restart_count}"
            )


def handle_evicted(v1: client.CoreV1Api, pod: client.V1Pod):
    """
    Clean up evicted pod objects.
    
    Eviction happens when a node runs out of memory or disk space.
    Kubernetes evicts pods to free resources and protect the node.
    
    After eviction:
    - The pod object stays in the cluster with phase=Failed, reason=Evicted
    - The Deployment already created a replacement pod on another node
    - The evicted pod object is just dead weight — it confuses kubectl output
      and wastes etcd storage
    
    Our action: delete the stale evicted object to keep cluster state clean.
    The replacement pod is already running — we are not losing anything.
    """
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    
    if (pod.status and
            pod.status.phase == "Failed" and
            pod.status.reason == "Evicted"):
        log.warning("Evicted pod detected: %s — deleting stale object", pod_name)
        delete_pod(v1, pod_name, namespace, "Evicted: cleaning stale pod object")


def handle_oom_killed(v1: client.CoreV1Api, pod: client.V1Pod):
    """
    Detect and recover from OOMKilled containers.
    
    OOMKilled = Out Of Memory Killed
    The Linux kernel killed the container process because it exceeded
    its memory limit defined in the Deployment resources.limits.memory
    
    In StreamingApp, the streaming service is most at risk:
    - It handles video file processing which is memory-intensive
    - A large video upload could spike memory above the 1Gi limit
    
    Our action: delete the pod so it restarts fresh with cleared memory.
    
    Long-term fix (not done here): increase memory limits in values.yaml
    or implement streaming in chunks to reduce peak memory usage.
    The log_action record helps identify which pod needs limit increases.
    """
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    
    if not pod.status or not pod.status.container_statuses:
        return
    
    for cs in pod.status.container_statuses:
        if (cs.last_state and
                cs.last_state.terminated and
                cs.last_state.terminated.reason == "OOMKilled"):
            log.warning("OOMKilled detected: pod=%s container=%s", pod_name, cs.name)
            delete_pod(v1, pod_name, namespace, "OOMKilled: container exceeded memory limit")


def handle_image_pull_error(v1: client.CoreV1Api, pod: client.V1Pod):
    """
    Detect image pull failures and alert (cannot auto-fix).
    
    ImagePullBackOff / ErrImagePull means:
    - Kubernetes tried to pull the Docker image from ECR
    - The pull failed
    
    Common causes:
    - Image tag does not exist in ECR (Jenkins build failed before push)
    - ECR repository does not exist (needs to be created)
    - Node IAM role missing ECR permissions (imageBuilder addon issue)
    - Network issue between node and ECR endpoint
    
    Why we cannot auto-fix this:
    Deleting the pod does not help — the new pod will have the same
    image reference and fail to pull for the same reason.
    A human needs to investigate ECR and fix the root cause.
    
    Our action: log a detailed alert so the issue is visible
    in Grafana/CloudWatch and triggers a Slack notification.
    """
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    
    if not pod.status or not pod.status.container_statuses:
        return
    
    for cs in pod.status.container_statuses:
        if (cs.state and cs.state.waiting and
                cs.state.waiting.reason in ("ImagePullBackOff", "ErrImagePull")):
            log.error(
                "ImagePull failure: pod=%s image=%s reason=%s — manual ECR investigation required",
                pod_name, cs.image, cs.state.waiting.reason
            )
            log_action(
                "image_pull_failure",
                pod_name, namespace,
                cs.state.waiting.reason,
                "alert_only: check ECR repository and image tag"
            )


def evaluate_pod(v1: client.CoreV1Api, pod: client.V1Pod):
    """
    Run all healing checks against a single pod.
    
    Called from two places:
    1. watch_pods() — triggered immediately when any pod changes
    2. periodic_scan() — runs every 60s as a safety backstop
       (catches events the watch stream may have missed during reconnects)
    """
    if not pod.status:
        return
    
    phase = pod.status.phase or ""
    
    # Running and Pending pods can have container-level issues
    if phase in ("Running", "Pending"):
        handle_crash_loop(v1, pod)
        handle_oom_killed(v1, pod)
        handle_image_pull_error(v1, pod)
    
    # Failed pods may be evicted
    if phase == "Failed":
        handle_evicted(v1, pod)


def watch_pods(v1: client.CoreV1Api):
    """
    Stream pod events from the Kubernetes API in real time.
    
    The Kubernetes watch API uses HTTP long-polling:
    - We open a persistent HTTP connection to the API server
    - API server sends us an event every time any pod changes
    - We evaluate the pod immediately
    - Latency: typically < 1 second from event to healing action
    
    Event types:
    - ADDED:    new pod created (check if it starts healthy)
    - MODIFIED: pod state changed (crash, restart, status update)
    - DELETED:  pod removed (we usually ignore these)
    """
    w = watch.Watch()
    log.info(
        "Starting pod watch stream — namespace=%s restart_threshold=%d cooldown=%ds",
        NAMESPACE, RESTART_THRESHOLD, COOLDOWN_SECONDS
    )
    
    # timeout_seconds=0 means watch forever (no timeout)
    for event in w.stream(
        v1.list_namespaced_pod,
        namespace=NAMESPACE,
        timeout_seconds=0
    ):
        event_type = event["type"]
        pod: client.V1Pod = event["object"]
        
        if event_type in ("ADDED", "MODIFIED"):
            evaluate_pod(v1, pod)


def periodic_scan(v1: client.CoreV1Api, interval: int = 60):
    """
    Full namespace scan every 60 seconds as a safety backstop.
    
    Why we need this even though we have a watch stream:
    - Watch streams can disconnect and reconnect, missing events
    - A pod that was already broken before the controller started
      will not generate a new MODIFIED event
    - Gives us a guaranteed catch-all every minute
    
    Runs in a separate thread so it does not block the watch stream.
    """
    log.info("Starting periodic scan thread — interval=%ds", interval)
    while True:
        try:
            log.info("Running periodic full namespace scan")
            pods = v1.list_namespaced_pod(namespace=NAMESPACE)
            for pod in pods.items:
                evaluate_pod(v1, pod)
            log.info("Periodic scan complete — checked %d pods", len(pods.items))
        except ApiException as e:
            log.error("Periodic scan failed: %s", e)
        
        time.sleep(interval)


def main():
    """
    Main entry point.
    
    Architecture:
    - Thread 1 (main):    watch_pods() — real-time event stream
    - Thread 2 (daemon):  periodic_scan() — 60s safety backstop
    
    The watch loop restarts automatically on connection errors.
    The periodic scan thread runs until the process exits.
    """
    load_k8s_config()
    v1 = client.CoreV1Api()
    
    log.info("StreamingApp Healing Controller starting up")
    log.info("Config: namespace=%s threshold=%d cooldown=%ds",
             NAMESPACE, RESTART_THRESHOLD, COOLDOWN_SECONDS)
    
    # Start periodic scan in background thread
    # daemon=True means this thread dies when the main thread dies
    scanner = threading.Thread(
        target=periodic_scan,
        args=(v1, 60),
        daemon=True,
        name="periodic-scanner"
    )
    scanner.start()
    log.info("Periodic scanner thread started")
    
    # Run watch loop in main thread with auto-restart on errors
    while True:
        try:
            watch_pods(v1)
        except Exception as e:
            log.error("Watch stream error: %s — restarting in 10s", e)
            time.sleep(10)


if __name__ == "__main__":
    main()
