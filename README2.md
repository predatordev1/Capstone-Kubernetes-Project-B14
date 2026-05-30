# StreamingApp — Kubernetes Cluster Health Checker & Auto-Healing System

> A production-grade MERN stack video streaming platform deployed on AWS EKS with automated health monitoring, self-healing mechanisms, CI/CD automation, real-time alerting, and a full observability stack.

**Author:** Priyank Pandey &nbsp;|&nbsp; **AWS Region:** us-west-1 &nbsp;|&nbsp; **Kubernetes:** v1.32 &nbsp;|&nbsp; **Stack:** MERN + EKS + Helm + Jenkins

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Summary of Deliverables](#2-summary-of-deliverables)
3. [Architecture](#3-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Application Components](#5-application-components)
6. [Infrastructure Setup](#6-infrastructure-setup)
7. [Docker Containerization](#7-docker-containerization)
8. [CI/CD Pipeline — Jenkins](#8-cicd-pipeline--jenkins)
9. [EKS Cluster Configuration](#9-eks-cluster-configuration)
10. [Helm Chart Structure](#10-helm-chart-structure)
11. [Self-Healing System](#11-self-healing-system)
12. [Auto-Scaling — HPA & Cluster Autoscaler](#12-auto-scaling--hpa--cluster-autoscaler)
13. [Ingress & Load Balancing](#13-ingress--load-balancing)
14. [Monitoring — Prometheus & Grafana](#14-monitoring--prometheus--grafana)
15. [Alerting — Alertmanager & Slack](#15-alerting--alertmanager--slack)
16. [Security Implementation](#16-security-implementation)
17. [Kubernetes Secrets Management](#17-kubernetes-secrets-management)
18. [Deployment Guide](#18-deployment-guide)
19. [Validation & Testing](#19-validation--testing)
20. [Troubleshooting Guide](#20-troubleshooting-guide)
21. [Challenges & Solutions](#21-challenges--solutions)
22. [Cost Analysis](#22-cost-analysis)
23. [Future Improvements](#23-future-improvements)
24. [Project Structure](#24-project-structure)

---

## 1. Project Overview

### Objective

Deploy a production-ready MERN (MongoDB, Express, React, Node.js) stack microservices application on AWS Elastic Kubernetes Service (EKS) with a complete DevOps lifecycle including:

- Automated container builds and registry management via Jenkins CI/CD
- Kubernetes orchestration with Helm package management
- Self-healing controller that detects and remediates pod failures autonomously
- Horizontal and cluster-level auto-scaling under load
- Real-time observability through Prometheus and Grafana
- Slack-integrated alerting via Alertmanager
- Security hardened with IAM Instance Profiles, OIDC-based pod identity, and scoped RBAC

### Why This Matters

In production Kubernetes environments, pods crash, nodes run out of resources, and traffic spikes unexpectedly. Manual intervention is slow and error-prone. This project implements an automated operations layer that detects problems in real time and heals them without human input — reducing MTTR (Mean Time to Recovery) from minutes to seconds.

---

## 2. Summary of Deliverables

### Deliverable 1 — Automated Health Monitoring Tool

A continuous monitoring system that tracks the health of every component in the Kubernetes cluster:

| What is Monitored | How | Threshold |
|-------------------|-----|-----------|
| Pod restart rate | Prometheus `kube_pod_container_status_restarts_total` | > 1 restart/5min |
| Pod phase | Prometheus `kube_pod_status_phase` | Pending > 5min |
| Node CPU utilization | `node_cpu_seconds_total` | > 80% for 5min |
| Node memory utilization | `node_memory_MemAvailable_bytes` | > 85% for 5min |
| OOMKilled containers | `kube_pod_container_status_last_terminated_reason` | Any occurrence |

All metrics are collected by Prometheus (scrape interval: 15s) and visualized in Grafana dashboards with 30-second auto-refresh.

### Deliverable 2 — Self-Healing Mechanisms

A Python-based Kubernetes controller that runs inside the cluster and performs automated remediation:

**Pod-level healing:**

| Failure Mode | Detection | Action | Cooldown |
|-------------|-----------|--------|----------|
| CrashLoopBackOff | restart_count ≥ 3 | Delete pod (Deployment recreates) | 5 minutes |
| OOMKilled | last_terminated.reason == OOMKilled | Delete pod (fresh restart) | 5 minutes |
| Evicted pod | phase == Failed, reason == Evicted | Delete stale pod object | None |
| ImagePullBackOff | waiting.reason == ImagePullBackOff | Log structured alert | None |

**Healing audit log:** Every action is written as structured JSON to stdout (captured by Kubernetes) and to `/var/log/healing/actions.log`:

```json
{
  "timestamp": "2026-05-30T09:15:00Z",
  "action": "delete_pod",
  "pod": "streaming-service-7dd446cd9c-mlkch",
  "namespace": "default",
  "reason": "CrashLoopBackOff: restarts=4",
  "result": "success"
}
```

### Deliverable 3 — Real-Time Alerting and Notifications

Alertmanager configured to route alerts to Slack with severity-based routing:

| Alert | Severity | Trigger |
|-------|----------|---------|
| PodCrashLooping | critical | > 1 restart/5min for 2min |
| PodOOMKilled | warning | Any occurrence |
| PodPendingTooLong | critical | Pending > 5min |
| NodeHighCPU | warning | CPU > 80% for 5min |
| NodeHighMemory | critical | Memory > 85% for 5min |

### Deliverable 4 — Web Dashboard for Real-Time and Historical Monitoring

Grafana dashboards provide full cluster visibility with pre-built Kubernetes dashboards from kube-prometheus-stack plus custom StreamingApp alert rules.

**Installed dashboards:**
- Kubernetes / Compute Resources / Cluster
- Kubernetes / Compute Resources / Namespace (Pods) — filtered to `default` namespace
- Node Exporter Full (dashboard ID: 1860)

**Data sources configured:**
- Prometheus — `http://monitoring-kube-prometheus-prometheus:9090`
- Dashboard auto-refresh: 30 seconds

### Deliverable 5 — Comprehensive Documentation

This README covers the complete implementation. Additional docs:
- `docs/COMPLETE_PROJECT_DOCUMENTATION.md` — phase-by-phase implementation guide
- `docs/QUICK_REFERENCE.md` — command reference
- `docs/VALIDATION_CHECKLIST.md` — end-to-end validation procedures
- `monitoring-rules.yaml` — PrometheusRule alert definitions (applied to cluster)

---

## 3. Architecture

### High-Level System Architecture

```
Internet Users
      │
      ▼
┌─────────────────────────────────────────────────────┐
│     nginx Ingress Controller (AWS NLB)              │
│  internet-facing, us-west-1                        │
│                                                     │
│  /api/auth      → auth-service:3001                 │
│  /api/streaming → streaming-service:3002            │
│  /api/admin     → admin-service:3003                │
│  /api/chat      → chat-service:3004                 │
│  /              → frontend:80                       │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│              AWS EKS Cluster                        │
│           streamingapp-cluster-pp                   │
│                  us-west-1                          │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  Application Pods (default namespace)       │    │
│  │  auth-service     × 2  (HPA: max 6)         │    │
│  │  streaming-service × 2  (HPA: max 8)        │    │
│  │  admin-service    × 2                       │    │
│  │  chat-service     × 2                       │    │
│  │  frontend         × 2  (HPA: max 6)         │    │
│  │  healing-controller × 1                     │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  Monitoring Stack (monitoring namespace)    │    │
│  │  Prometheus   Grafana   Alertmanager        │    │
│  │  node-exporter   kube-state-metrics         │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌──────────────────┐  ┌──────────────────┐         │
│  │  Node 1          │  │  Node 2          │         │
│  │  t3.medium       │  │  t3.medium       │         │
│  │  us-west-1a      │  │  us-west-1c      │         │
│  │  2 vCPU / 4 GB   │  │  2 vCPU / 4 GB   │         │
│  │  AmazonLinux2023 │  │  AmazonLinux2023 │         │
│  └──────────────────┘  └──────────────────┘         │
└─────────────────────────────────────────────────────┘
          │                           │
          ▼                           ▼
┌──────────────────┐       ┌──────────────────────┐
│  MongoDB Atlas   │       │  AWS S3              │
│  (Cloud DB)      │       │  streamingapp-videos  │
│  cluster0.fhrg87w│       │  -975050024946        │
└──────────────────┘       └──────────────────────┘
```

### CI/CD Pipeline Architecture

```
Developer pushes code
        │
        ▼ GitHub Webhook (pending configuration)
┌───────────────────────────────────────────┐
│  Jenkins (EC2, us-west-1)                 │
│                                           │
│  Stage 1: Checkout                        │
│  Stage 2: Build (parallel × 6)            │
│  Stage 3: ECR Login                       │
│  Stage 4: Push (parallel × 6)             │
│  Stage 5: Deploy → helm upgrade --atomic  │
│  Stage 6: Cleanup                         │
└───────────────────────────────────────────┘
        │
        ▼ docker push
┌─────────────────────────────────┐
│  AWS ECR (us-west-1)            │
│  6 repositories with -pp suffix │
│  :latest + :git-commit-hash     │
└─────────────────────────────────┘
        │
        ▼ helm upgrade --atomic
┌─────────────────────────────────┐
│  EKS Cluster                    │
│  Rolling update — zero downtime │
│  --atomic: auto-rollback on fail│
└─────────────────────────────────┘
```

---

## 4. Technology Stack

### Cloud & Infrastructure

| Tool | Version | Purpose |
|------|---------|---------|
| AWS EKS | Kubernetes 1.32 | Managed Kubernetes control plane |
| AWS EC2 | t3.medium | Jenkins server + EKS worker nodes |
| AWS ECR | — | Private Docker container registry |
| AWS S3 | — | Video and thumbnail file storage |
| AWS NLB | — | Network Load Balancer (via nginx ingress) |
| AWS IAM | — | Identity and access management |
| MongoDB Atlas | — | Managed cloud database (free tier) |

### Container & Orchestration

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24.x | Container runtime and image builds |
| Kubernetes | 1.32.13 | Container orchestration |
| Helm | v4.1.0 | Kubernetes package management |
| eksctl | v0.227.0 | EKS cluster lifecycle management |
| kubectl | v1.35.0 | Kubernetes CLI |

### Application Stack

| Technology | Purpose |
|-----------|---------|
| Node.js 18 (Alpine) | Backend runtime for all 4 services |
| React 18 | Frontend single-page application |
| Express.js | REST API framework |
| Socket.IO | Real-time WebSocket communication (chat) |
| Nginx 1.27 (Alpine) | Frontend static file server |
| Python 3.11 (slim) | Healing controller runtime |
| kubernetes-client 29.0 | Python SDK for Kubernetes API |

### Monitoring & Observability

| Tool | Status | Purpose |
|------|--------|---------|
| Prometheus | ✅ Installed | Metrics collection and storage |
| Grafana | ✅ Installed | Dashboards and visualization |
| Alertmanager | ✅ Installed | Alert routing (Slack config pending) |
| kube-state-metrics | ✅ Installed | Kubernetes object metrics |
| node-exporter | ✅ Installed | Node-level metrics (CPU, memory, disk) |
| Loki + Fluent Bit | 📋 Planned | Log aggregation |

---

## 5. Application Components

### Service Overview

| Service | Port | Image | Health Check | Replicas |
|---------|------|-------|-------------|---------|
| auth-service | 3001 | streamingapp-auth-pp | `GET /health` | 2 (HPA: max 6) |
| streaming-service | 3002 | streamingapp-streaming-pp | `GET /api/health` | 2 (HPA: max 8) |
| admin-service | 3003 | streamingapp-admin-pp | `TCP :3003` | 2 |
| chat-service | 3004 | streamingapp-chat-pp | `TCP :3004` | 2 |
| frontend | 80 | streamingapp-frontend-pp | `GET /health` | 2 (HPA: max 6) |
| healing-controller | N/A | streamingapp-healing-controller-pp | N/A | 1 |

### API Route Structure

Each service mounts its routes at a path matching what nginx forwards:

| Service | Express Mount | nginx Path | Example Full Route |
|---------|--------------|-----------|-------------------|
| auth-service | `app.use('/api/auth', userRoute)` | `/api/auth` | `POST /api/auth/login` |
| streaming-service | `app.use('/api/streaming/streaming', routes)` + `app.use('/api/streaming', routes)` | `/api/streaming` | `GET /api/streaming/videos/featured` |
| admin-service | `app.use('/api/admin', videoRoute)` | `/api/admin` | `GET /api/admin/videos` |
| chat-service | `app.use('/api/chat', chatRoute)` | `/api/chat` | `GET /api/chat/history/:videoId` |

> **Note on streaming dual-mount:** The streaming service uses two mount points because the React frontend's axios baseURL (`/api/streaming`) is prepended to route paths that already include `/streaming/videos/...`, causing a doubled prefix (`/api/streaming/streaming/videos/featured`). The dual mount handles both the doubled-prefix API calls from the frontend AND direct video stream URLs which arrive with a single prefix.

### Service Descriptions

**Auth Service (Port 3001)**
Handles user registration, login, JWT token generation and validation. Routes mounted at `/api/auth` to match nginx forwarding. Health endpoint at `/health` returns `{"status":"OK"}`.

**Streaming Service (Port 3002)**
Manages video catalog, metadata, and playback. Generates signed S3 URLs for video delivery. Health endpoint at `/api/health`. Dual route mount handles both API calls and direct stream URL patterns.

**Admin Service (Port 3003)**
Content management for uploading videos and thumbnails directly to S3. Uses AWS SDK v3 with instance profile credentials (node IAM role has `AmazonS3FullAccess`). Uses TCP socket probe — no dedicated HTTP health endpoint.

**Chat Service (Port 3004)**
Real-time watch party chat using Socket.IO WebSockets. Nginx `proxy-read-timeout: 3600` keeps WebSocket connections alive. Uses TCP socket probe. REST endpoint at `/api/chat/history/:videoId` for message history.

**Frontend (Port 80)**
React SPA served by Nginx. Multi-stage Docker build (~23MB final image). Built with relative API paths (`/api/auth`, `/api/streaming`, etc.) so the image is URL-agnostic — nginx routes handle the actual backend destinations. WebSocket and streaming public URL use the absolute nginx ELB URL.

**Healing Controller**
Python 3.11 with a Kubernetes watch stream (real-time events) plus a periodic scan thread (60s backstop). Runs as non-root user with minimal RBAC (pods: get/list/watch/delete, events: create/patch).

---

## 6. Infrastructure Setup

### Jenkins EC2 Bootstrap

```bash
#!/bin/bash
set -e

sudo apt update -y && sudo apt upgrade -y

# Java 17
sudo apt install -y openjdk-17-jdk

# Docker
sudo apt install -y docker.io
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker ubuntu

# AWS CLI v2
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
sudo apt install -y unzip && unzip -q awscliv2.zip
sudo ./aws/install && rm -rf aws awscliv2.zip

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# eksctl
curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz"
tar -xzf eksctl_Linux_amd64.tar.gz && sudo mv eksctl /usr/local/bin/

# Helm
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Jenkins
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | \
  sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/" | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update -y && sudo apt install -y jenkins
sudo systemctl enable jenkins && sudo systemctl start jenkins
sudo usermod -aG docker jenkins
sudo apt install -y git
```

**Jenkins URL:** `http://<EC2_PUBLIC_IP>:8080`

> **Important:** The EC2 public IP is dynamic (changes on stop/start). Attach an Elastic IP to make the Jenkins URL permanent.

### IAM Instance Profile for Jenkins EC2

Jenkins authenticates to AWS via an EC2 Instance Profile — no static credentials stored anywhere:

```bash
aws iam create-role --role-name StreamingApp-EC2-Role \
  --assume-role-policy-document file://ec2-trust-policy.json

aws iam create-instance-profile \
  --instance-profile-name StreamingApp-EC2-Profile

aws iam add-role-to-instance-profile \
  --instance-profile-name StreamingApp-EC2-Profile \
  --role-name StreamingApp-EC2-Role

aws ec2 associate-iam-instance-profile \
  --instance-id <JENKINS_INSTANCE_ID> \
  --iam-instance-profile Name=StreamingApp-EC2-Profile
```

> **Credential precedence:** AWS CLI checks `~/.aws/credentials` BEFORE the instance metadata service. If static credentials exist in that file, they override the instance profile. Always ensure no static credentials file exists on the Jenkins EC2 — the instance profile is the intended authentication method.

---

## 7. Docker Containerization

### Backend Services

All four backend services use the same single-stage Dockerfile:

```dockerfile
FROM node:18-alpine AS production
WORKDIR /app
COPY package*.json ./
RUN npm install --production  # --production excludes devDependencies
COPY . .
ENV NODE_ENV=production
EXPOSE <PORT>
CMD ["npm", "run", "start"]
```

Layer caching: `package*.json` is copied before source files. `npm install` only re-runs when dependencies change, not on every code push.

### Frontend — Multi-Stage Build

```dockerfile
# Stage 1: Build React bundle
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install

# Build args baked into JS bundle at compile time
ARG REACT_APP_AUTH_API_URL
ARG REACT_APP_STREAMING_API_URL
ARG REACT_APP_STREAMING_PUBLIC_URL
ARG REACT_APP_ADMIN_API_URL
ARG REACT_APP_CHAT_API_URL
ARG REACT_APP_CHAT_SOCKET_URL
ENV REACT_APP_AUTH_API_URL=${REACT_APP_AUTH_API_URL}
ENV REACT_APP_STREAMING_API_URL=${REACT_APP_STREAMING_API_URL}
ENV REACT_APP_STREAMING_PUBLIC_URL=${REACT_APP_STREAMING_PUBLIC_URL}
ENV REACT_APP_ADMIN_API_URL=${REACT_APP_ADMIN_API_URL}
ENV REACT_APP_CHAT_API_URL=${REACT_APP_CHAT_API_URL}
ENV REACT_APP_CHAT_SOCKET_URL=${REACT_APP_CHAT_SOCKET_URL}
COPY . .
RUN npm run build

# Stage 2: Serve with nginx (~23MB final image)
FROM nginx:1.27-alpine AS production
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Frontend URL Strategy

HTTP API calls use **relative paths** — no hardcoded external URLs in the image:

```bash
docker build \
  --build-arg REACT_APP_AUTH_API_URL=/api/auth \
  --build-arg REACT_APP_STREAMING_API_URL=/api/streaming \
  --build-arg REACT_APP_ADMIN_API_URL=/api/admin \
  --build-arg REACT_APP_CHAT_API_URL=/api/chat \
  --build-arg REACT_APP_STREAMING_PUBLIC_URL=http://<NGINX_URL> \
  --build-arg REACT_APP_CHAT_SOCKET_URL=http://<NGINX_URL> \
  -t <ECR>/streamingapp-frontend-pp:latest \
  frontend/
```

Why relative paths: React runs in the user's browser, not inside Kubernetes. `auth-service:3001` (Kubernetes internal DNS) cannot be resolved by the browser. Relative paths like `/api/auth` let the browser send requests to the same origin (the nginx ELB URL), which nginx routes to the correct backend pod.

WebSocket (Socket.IO) and the streaming public URL require absolute URLs because they bypass the browser's relative-URL resolution.

> **Critical:** Always build with `--no-cache` when changing `REACT_APP_*` build args. Docker caches the `npm run build` layer and will reuse the old compiled bundle (with old URLs) if source files haven't changed.

### Nginx Configuration

```nginx
# React Router — without this, every route except / returns 404
location / {
    try_files $uri $uri/ /index.html;
}

# Health check for Kubernetes liveness/readiness probes
location /health {
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}

# Static asset caching — 1 year (React uses content-hashed filenames)
location ~* \.(js|css|png|jpg|svg|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### ECR Repositories (all with -pp suffix)

```
975050024946.dkr.ecr.us-west-1.amazonaws.com/
├── streamingapp-auth-pp
├── streamingapp-streaming-pp
├── streamingapp-admin-pp
├── streamingapp-chat-pp
├── streamingapp-frontend-pp
└── streamingapp-healing-controller-pp
```

---

## 8. CI/CD Pipeline — Jenkins

### Pipeline Stages

```groovy
pipeline {
    agent any
    environment {
        AWS_REGION      = 'us-west-1'
        ECR_REGISTRY    = '975050024946.dkr.ecr.us-west-1.amazonaws.com'
        GIT_COMMIT_SHORT = sh(returnStdout: true,
                              script: 'git rev-parse --short HEAD').trim()
        NGINX_URL = 'http://<nginx-elb-url>'
        EKS_CLUSTER = 'streamingapp-cluster-pp'
    }

    stages {
        stage('Checkout') { ... }

        stage('Build Docker Images') {
            parallel {
                // Builds auth, streaming, admin, chat, frontend, healing-controller
                // Frontend uses relative API paths + absolute NGINX_URL for WebSocket
            }
        }

        stage('Login to ECR') { ... }

        stage('Push Images to ECR') {
            parallel {
                // Pushes :latest and :<git-commit-hash> tags for all 6 images
            }
        }

        stage('Deploy to EKS') {
            // aws eks update-kubeconfig
            // helm upgrade --install --set image.tag=${GIT_COMMIT_SHORT} --atomic
        }

        stage('Cleanup') {
            // docker system prune -af --volumes
        }
    }
}
```

### Key Pipeline Features

- **Parallel builds and pushes:** All 6 services build and push simultaneously (~5 min vs ~20 min sequential)
- **Dual image tagging:** `:latest` for convenience + `:<git-commit-hash>` for immutable rollbacks
- **`--atomic` on Helm:** Auto-rollback to previous revision if any pod fails within timeout
- **Instance profile auth:** Jenkins EC2 uses IAM role — no AWS credentials in Jenkins config
- **GitHub webhook:** Triggers pipeline on every push to `main` (configuration pending)

---

## 9. EKS Cluster Configuration

### Cluster Spec (`cluster-config.yaml`)

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: streamingapp-cluster-pp
  region: us-west-1
  version: "1.32"            # AL2023 requires 1.32+

iam:
  withOIDC: true             # Required: ALB Controller, Cluster Autoscaler

availabilityZones:
  - us-west-1a
  - us-west-1c               # us-west-1b does not exist

managedNodeGroups:
  - name: workers
    amiFamily: AmazonLinux2023  # AL2 deprecated November 2025
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 1
    maxSize: 4
    volumeSize: 20
    volumeType: gp3
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/streamingapp-cluster-pp: "owned"
    iam:
      withAddonPolicies:
        imageBuilder: true
        ebs: true
        albIngress: true
        cloudWatch: true
        autoScaler: true

cloudWatch:
  clusterLogging:
    enableTypes: [api, audit, authenticator]
```

> **Note:** This file documents the cluster as built. The cluster already exists — do NOT re-run `eksctl create cluster`. Use it as reference if recreation is needed.

### aws-auth ConfigMap Mappings

```bash
# Developer access
eksctl create iamidentitymapping \
  --cluster streamingapp-cluster-pp --region us-west-1 \
  --arn arn:aws:iam::975050024946:user/priyankpandey02@gmail.com \
  --group system:masters --username priyank-pp

# Jenkins EC2 role access
eksctl create iamidentitymapping \
  --cluster streamingapp-cluster-pp --region us-west-1 \
  --arn arn:aws:iam::975050024946:role/StreamingApp-EC2-Role \
  --group system:masters --username streamingapp-ec2-pp
```

---

## 10. Helm Chart Structure

```
helm/streamingapp/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── configmap.yaml              # aws-region, s3-bucket, client-urls
    ├── auth-deployment.yaml        # Deployment + ClusterIP Service
    ├── streaming-deployment.yaml   # Deployment + ClusterIP Service
    ├── admin-deployment.yaml       # Deployment + ClusterIP Service (tcpSocket probe)
    ├── chat-deployment.yaml        # Deployment + ClusterIP Service (tcpSocket probe)
    ├── frontend-deployment.yaml    # Deployment + ClusterIP Service
    ├── healing-controller.yaml     # ServiceAccount + ClusterRole + ClusterRoleBinding + Deployment
    ├── ingress.yaml                # nginx ingressClassName with proxy annotations
    ├── hpa.yaml                    # HPA for streaming (max 8), auth (max 6), frontend (max 6)
    └── pdb.yaml                    # PodDisruptionBudgets: minAvailable=1 for auth, streaming, frontend

# Applied separately after Prometheus is installed:
monitoring-rules.yaml              # PrometheusRule — 5 alert rules
```

### Key values.yaml Settings

```yaml
global:
  ecrRegistry: 975050024946.dkr.ecr.us-west-1.amazonaws.com
  awsRegion: us-west-1

replicaCount: 2
image:
  pullPolicy: Always   # Always pull on pod restart — picks up :latest changes
  tag: latest

# All images use -pp suffix (shared AWS account — avoids naming conflicts)
services:
  auth:
    image: streamingapp-auth-pp
  streaming:
    image: streamingapp-streaming-pp
    resources:
      requests: { cpu: 250m, memory: 512Mi }  # Reduced from 500m to fit t3.medium
      limits:   { cpu: 500m, memory: 1Gi }
  admin:
    image: streamingapp-admin-pp
  chat:
    image: streamingapp-chat-pp

frontend:
  image: streamingapp-frontend-pp
  serviceType: ClusterIP   # nginx ingress handles external access — no LoadBalancer per service

healingController:
  image: streamingapp-healing-controller-pp
  restartThreshold: "3"
  cooldownSeconds:  "300"

# Must match the public-facing nginx URL — used for CORS validation in all services
clientUrls: "http://<nginx-elb-url>"

monitoring:
  enabled: false   # Set true after kube-prometheus-stack is installed
```

### Helm Commands

```bash
# Validate
helm lint helm/streamingapp/

# Dry run
helm install streamingapp-pp helm/streamingapp/ --dry-run --debug

# First deploy
helm install streamingapp-pp helm/streamingapp/ \
  --namespace default --timeout 10m --atomic

# Upgrade after changes
helm upgrade streamingapp-pp helm/streamingapp/ \
  --namespace default --reuse-values

# Override a single value at deploy time
helm upgrade streamingapp-pp helm/streamingapp/ \
  --namespace default \
  --set image.tag=abc1234 \
  --reuse-values

# View release history
helm history streamingapp-pp

# Rollback
helm rollback streamingapp-pp 1
```

---

## 11. Self-Healing System

### Architecture

```
Healing Controller Pod (Python 3.11)
         │
         ├── Thread 1 (main): Kubernetes Watch Stream
         │   Real-time ADDED/MODIFIED pod events → evaluate_pod() → action
         │
         └── Thread 2 (daemon): Periodic Full Scan every 60s
             Catches events missed during watch stream reconnects
```

### RBAC — Principle of Least Privilege

```yaml
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]   # read-only — never modifies deployments directly
- apiGroups: [""]
  resources: ["events"]
  verbs: ["get", "list", "watch", "create", "patch"]
```

### Healing Decision Logic

```python
def evaluate_pod(v1, pod):
    phase = pod.status.phase

    if phase in ("Running", "Pending"):
        for cs in pod.status.container_statuses:
            if cs.restart_count >= RESTART_THRESHOLD:   # default: 3
                delete_pod(v1, pod_name, namespace,
                           f"CrashLoopBackOff: restarts={cs.restart_count}")

            if cs.last_state.terminated?.reason == "OOMKilled":
                delete_pod(v1, pod_name, namespace, "OOMKilled")

            if cs.state.waiting?.reason in ("ImagePullBackOff", "ErrImagePull"):
                log_action("alert_only: check ECR repo and image tag")

    if phase == "Failed" and pod.status.reason == "Evicted":
        delete_pod(v1, pod_name, namespace, "Evicted: cleaning stale object")
```

### Cooldown Mechanism

```python
_cooldowns: dict = {}   # pod_name → last_action_timestamp

def is_on_cooldown(pod_name):
    return (time.time() - _cooldowns.get(pod_name, 0)) < COOLDOWN_SECONDS  # 300s

def delete_pod(v1, pod_name, namespace, reason):
    if is_on_cooldown(pod_name):
        return   # Skip — wait for pod to stabilize before acting again
    v1.delete_namespaced_pod(name=pod_name, namespace=namespace,
                             body=V1DeleteOptions(grace_period_seconds=0))
    set_cooldown(pod_name)
    log_action("delete_pod", pod_name, namespace, reason, "success")
```

### Verify Healing Controller

```bash
kubectl get pods -l app=healing-controller
kubectl logs -l app=healing-controller --tail=30
```

### Test Healing

```bash
# Force a crash
kubectl exec -it $(kubectl get pods -l app=auth-service \
  -o jsonpath='{.items[0].metadata.name}') -- kill 1

# Watch healing controller respond (within ~30 seconds at restart_count=3)
kubectl logs -l app=healing-controller -f
```

---

## 12. Auto-Scaling — HPA & Cluster Autoscaler

### Horizontal Pod Autoscaler

| Service | Min | Max | CPU Trigger | Scale-Up | Scale-Down |
|---------|-----|-----|------------|---------|-----------|
| streaming-service | 2 | 8 | 65% | 60s window | 300s window |
| auth-service | 2 | 6 | 70% | — | — |
| frontend | 2 | 6 | 60% | — | — |

```bash
kubectl get hpa -n default -w
```

### Cluster Autoscaler (📋 Pending Installation)

```bash
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=streamingapp-cluster-pp \
  --set awsRegion=us-west-1 \
  --set extraArgs.expander=least-waste \
  --set extraArgs.scale-down-unneeded-time=10m
```

The ASG tags required for Cluster Autoscaler discovery are already set on the node group (added in `cluster-config.yaml`).

### PodDisruptionBudgets

```yaml
spec:
  minAvailable: 1   # At least 1 pod survives node drains/upgrades
```

Applied to: auth-service, streaming-service, frontend.

---

## 13. Ingress & Load Balancing

### Why nginx Ingress (Not AWS ALB Controller)

nginx Ingress was chosen for simplicity — no OIDC IAM service account setup required, works the same across cloud providers, and the nginx controller itself is straightforward to configure. The AWS ALB Controller IS installed in the cluster (for pod-level IAM via OIDC) but is not used for ingress routing.

### nginx Ingress Installation

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer
```

### NLB Security Group Configuration

The nginx ingress creates an **internet-facing** NLB. The NLB has two security groups:

```
sg-07c3db05b6a09fd67  (NLB frontend)
  → port 80 from 0.0.0.0/0     ← allows internet browsers in
  → port 443 from 0.0.0.0/0

sg-0172350e698619332  (backend / shared)
  → used as source in node SG rule for ports 31143-31576
  → allows NLB to reach nodes on NodePort
```

> **Important:** When the nginx ingress service is annotated from `internal` to `internet-facing`, a new NLB is provisioned with a new DNS name and new security groups. The old port 80/443 rules must be re-added to the new NLB's frontend SG.

### Ingress Annotations

```yaml
annotations:
  nginx.ingress.kubernetes.io/proxy-body-size: "100m"    # Video uploads
  nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"  # WebSocket persistence
  nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
  nginx.ingress.kubernetes.io/proxy-http-version: "1.1"   # WebSocket upgrade
```

---

## 14. Monitoring — Prometheus & Grafana

### Installation

```bash
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword='<your-password>' \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

### Verify Installation

```bash
kubectl get pods -n monitoring
# Expected pods:
# alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2 Running
# monitoring-grafana-*                                      3/3 Running
# monitoring-kube-prometheus-operator-*                    1/1 Running
# monitoring-kube-state-metrics-*                          1/1 Running
# monitoring-prometheus-node-exporter-* (one per node)     1/1 Running
# prometheus-monitoring-kube-prometheus-prometheus-0       2/2 Running
```

### Apply Custom Alert Rules

```bash
kubectl apply -f monitoring-rules.yaml -n monitoring
kubectl get prometheusrule -n monitoring
```

Prometheus discovers this `PrometheusRule` via the label `release: monitoring` — no restart needed, Prometheus Operator hot-reloads the rules.

### Access Grafana

**Via SSH tunnel (development):**
```bash
# On EC2:
kubectl port-forward pod/$(kubectl get pod -n monitoring \
  -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=monitoring" \
  -oname) 3000 -n monitoring &

# On Windows (new PowerShell window):
ssh -i "streamingapp-pp.pem" -L 3000:localhost:3000 ubuntu@<EC2_PUBLIC_IP>
# Open: http://localhost:3000  |  Login: admin / <your-password>
```

**Via nginx ingress (permanent — setup steps below):**
```bash
# Step 1: Configure Grafana to serve from /grafana subpath
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --reuse-values \
  --set "grafana.grafana\.ini.server.root_url=http://<NGINX_URL>/grafana" \
  --set "grafana.grafana\.ini.server.serve_from_sub_path=true"

# Step 2: Create Ingress for Grafana in monitoring namespace
kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: monitoring
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /grafana(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: monitoring-grafana
            port:
              number: 80
EOF
# Access: http://<NGINX_URL>/grafana
```

### Key Prometheus Queries

```promql
# Pod restart rate
rate(kube_pod_container_status_restarts_total{namespace="default"}[5m]) * 300

# Node CPU utilization
(1 - avg by(node)(rate(node_cpu_seconds_total{mode="idle"}[5m]))) * 100

# Node memory utilization
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# HPA replica count
kube_horizontalpodautoscaler_status_current_replicas{namespace="default"}
```

---

## 15. Alerting — Alertmanager & Slack

### Status: 📋 Pending Configuration

Alertmanager is installed (part of kube-prometheus-stack). Slack webhook integration requires:

```bash
kubectl create secret generic alertmanager-slack \
  --from-literal=slack-webhook-url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  --namespace monitoring
```

### Alertmanager Config (apply when Slack webhook is ready)

```yaml
apiVersion: monitoring.coreos.com/v1alpha1
kind: AlertmanagerConfig
metadata:
  name: streamingapp-alerts
  namespace: monitoring
spec:
  route:
    groupBy: ['alertname', 'namespace', 'pod']
    groupWait: 30s
    repeatInterval: 3h
    receiver: slack-critical

  receivers:
  - name: slack-critical
    slackConfigs:
    - channel: '#k8s-alerts'
      sendResolved: true
      title: '[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
      text: |
        *Pod:* {{ .CommonLabels.pod }}
        *Summary:* {{ .CommonAnnotations.summary }}
```

---

## 16. Security Implementation

### Credential Strategy

| Component | Auth Method | Why |
|-----------|------------|-----|
| Jenkins EC2 → AWS | IAM Instance Profile (StreamingApp-EC2-Role) | Temporary rotating credentials, no static keys |
| EKS nodes → ECR | Node IAM Role (imageBuilder addon policy) | Pull images without credentials in pods |
| EKS nodes → S3 | Node IAM Role (AmazonS3FullAccess) | Instance profile fallback via SDK credential chain |
| kubectl → EKS | kubeconfig + instance profile | aws-auth ConfigMap maps role to system:masters |
| Pods → MongoDB | Kubernetes Secret (app-secrets) | Encrypted at rest in etcd |

### S3 Access via Instance Profile

The admin and streaming services use an S3 client that conditionally uses credentials:

```javascript
const buildAwsCredentials = () => {
  const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
  const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;
  if (accessKeyId && secretAccessKey) {
    return { accessKeyId, secretAccessKey };
  }
  return undefined;  // SDK falls back to instance profile
};

const s3Client = new S3Client({
  region: process.env.AWS_REGION,
  credentials: buildAwsCredentials(),
});
```

When `aws-secrets` contains empty strings for `access-key-id` and `secret-access-key`, `buildAwsCredentials()` returns `undefined`, and the AWS SDK automatically uses the EKS node's instance profile credentials. The node IAM role has `AmazonS3FullAccess` attached.

### Security Best Practices Applied

- No AWS credentials in Git, Docker images, or Helm values
- Kubernetes Secrets for all sensitive configuration
- Least-privilege RBAC for healing controller
- Non-root user inside healing controller container
- `.dockerignore` prevents `.env` files from entering images
- CloudWatch audit logging for all EKS control plane API calls

---

## 17. Kubernetes Secrets Management

### Create Secrets (Run Once — Never Commit to Git)

```bash
kubectl create secret generic app-secrets \
  --from-literal=mongo-uri="mongodb+srv://user:pass@cluster.mongodb.net/streamingapp" \
  --from-literal=jwt-secret="your-jwt-secret-here"

# AWS secrets — use empty strings to trigger instance profile fallback
# Node IAM role must have AmazonS3FullAccess attached
kubectl create secret generic aws-secrets \
  --from-literal=access-key-id="" \
  --from-literal=secret-access-key=""
```

### Promote a User to Admin

Since MongoDB runs on Atlas (not in-cluster), use the auth service pod which already has MongoDB credentials:

```bash
kubectl exec -it deployment/auth-service -n default -- \
  node -e "
const mongoose = require('mongoose');
mongoose.connect(process.env.MONGO_URI).then(async () => {
  const result = await mongoose.connection.db.collection('users').updateOne(
    { email: 'your-email@example.com' },
    { \$set: { role: 'admin' } }
  );
  console.log('Modified:', result.modifiedCount, 'document(s)');
  process.exit(0);
});
"
```

Log out and back in after the update — the JWT token contains the role and must be refreshed.

---

## 18. Deployment Guide

### Step 1 — Prerequisites

```bash
git clone https://github.com/PriyankP2/StreamingApp.git
cd StreamingApp
kubectl get nodes   # Verify cluster access
```

### Step 2 — Create ECR Repositories

```bash
for repo in streamingapp-auth-pp streamingapp-streaming-pp \
            streamingapp-admin-pp streamingapp-chat-pp \
            streamingapp-frontend-pp streamingapp-healing-controller-pp; do
  aws ecr create-repository --repository-name $repo \
    --region us-west-1 \
    --image-scanning-configuration scanOnPush=true
done
```

### Step 3 — Create Kubernetes Secrets

```bash
kubectl create secret generic app-secrets \
  --from-literal=mongo-uri="<MONGODB_URI>" \
  --from-literal=jwt-secret="<JWT_SECRET>"

kubectl create secret generic aws-secrets \
  --from-literal=access-key-id="" \
  --from-literal=secret-access-key=""
```

### Step 4 — Attach S3 Policy to Node Role

```bash
aws iam attach-role-policy \
  --role-name eksctl-streamingapp-cluster-pp-nod-NodeInstanceRole-9PWFlGlm9I12 \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
  --region us-west-1
```

### Step 5 — Install nginx Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer

kubectl get svc ingress-nginx-controller -n ingress-nginx -w
# Wait for EXTERNAL-IP — this is your NGINX_URL
```

### Step 6 — Build and Push Docker Images

```bash
ECR="975050024946.dkr.ecr.us-west-1.amazonaws.com"
NGINX_URL="http://<your-nginx-elb-url>"

aws ecr get-login-password --region us-west-1 | \
  docker login --username AWS --password-stdin $ECR

# Backend services
for svc in authService streamingService adminService chatService; do
  name=$(echo $svc | tr '[:upper:]' '[:lower:]' | sed 's/service/-pp/')
  docker build -t $ECR/streamingapp-${name}:latest backend/$svc/
  docker push $ECR/streamingapp-${name}:latest
done

# Healing controller
docker build -t $ECR/streamingapp-healing-controller-pp:latest healing-controller/
docker push $ECR/streamingapp-healing-controller-pp:latest

# Frontend — use --no-cache to ensure build args are applied
docker build --no-cache \
  --build-arg REACT_APP_AUTH_API_URL=/api/auth \
  --build-arg REACT_APP_STREAMING_API_URL=/api/streaming \
  --build-arg REACT_APP_STREAMING_PUBLIC_URL=$NGINX_URL \
  --build-arg REACT_APP_ADMIN_API_URL=/api/admin \
  --build-arg REACT_APP_CHAT_API_URL=/api/chat \
  --build-arg REACT_APP_CHAT_SOCKET_URL=$NGINX_URL \
  -t $ECR/streamingapp-frontend-pp:latest \
  frontend/
docker push $ECR/streamingapp-frontend-pp:latest
```

### Step 7 — Deploy with Helm

```bash
helm lint helm/streamingapp/
helm install streamingapp-pp helm/streamingapp/ \
  --namespace default --timeout 10m --atomic

kubectl get pods -n default
kubectl get ingress -n default
```

### Step 8 — Install Monitoring

```bash
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword='<your-password>' \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

kubectl apply -f monitoring-rules.yaml -n monitoring
```

---

## 19. Validation & Testing

### Quick Health Check

```bash
kubectl get pods -n default
kubectl get pods -n monitoring
kubectl get ingress -n default
kubectl get hpa -n default
kubectl logs -l app=healing-controller -n default --tail=10
```

### Test Application Endpoints

```bash
NGINX="http://<your-nginx-url>"

curl $NGINX/health                          # Frontend: returns "healthy"
curl $NGINX/api/auth/health                 # Auth: {"status":"OK"}

curl -X POST $NGINX/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"test1234"}'

curl -X POST $NGINX/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234"}'
```

### Test Self-Healing

```bash
kubectl exec -it $(kubectl get pods -l app=auth-service \
  -o jsonpath='{.items[0].metadata.name}') -- kill 1

kubectl logs -l app=healing-controller -f
# Watch for: HEALING_ACTION {"action":"delete_pod","reason":"CrashLoopBackOff..."}
```

---

## 20. Troubleshooting Guide

### kubectl 401 Unauthorized

```bash
# Cause 1: Static credentials overriding instance profile
mv ~/.aws/credentials ~/.aws/credentials.bak
aws sts get-caller-identity   # Must show IAM role ARN, not user ARN

# Cause 2: kubeconfig stale
aws eks update-kubeconfig --name streamingapp-cluster-pp --region us-west-1

# Cause 3: Clock skew
sudo timedatectl set-ntp true && sudo chronyc makestep
```

### Pod Status Issues

| Status | Cause | Fix |
|--------|-------|-----|
| `ImagePullBackOff` | Wrong image name or missing -pp suffix | Check `values.yaml` image names match ECR repos |
| `CrashLoopBackOff` | App crashes on startup | `kubectl logs <pod> --previous` |
| `Pending` | Insufficient CPU | Reduce resource requests in values.yaml |
| `0/1 Running` | Health probe failing | Check probe path matches actual endpoint |

### Helm Issues

```bash
helm list -n default              # Check release status
helm history streamingapp-pp      # See previous revisions
helm rollback streamingapp-pp 1   # Roll back to previous working revision
helm uninstall streamingapp-pp    # Remove all resources if stuck
```

### CORS Errors (login/API calls fail)

```bash
# Verify clientUrls in ConfigMap matches browser origin
kubectl get configmap app-config -n default -o yaml | grep client-urls

# If wrong, update and restart all services
helm upgrade streamingapp-pp helm/streamingapp/ \
  --set clientUrls="http://<correct-nginx-url>" \
  --reuse-values

kubectl rollout restart deployment/auth-service deployment/streaming-service \
  deployment/admin-service deployment/chat-service -n default
```

### S3 Upload Errors (InvalidAccessKeyId)

```bash
# Check secret content
kubectl get secret aws-secrets -n default \
  -o jsonpath='{.data.access-key-id}' | base64 -d; echo

# If it shows "USE-INSTANCE-PROFILE" or any placeholder, update to empty strings:
kubectl create secret generic aws-secrets \
  --from-literal=access-key-id="" \
  --from-literal=secret-access-key="" \
  --namespace default --dry-run=client -o yaml | kubectl apply -f -

# Ensure node IAM role has S3 access
aws iam list-attached-role-policies \
  --role-name eksctl-streamingapp-cluster-pp-nod-NodeInstanceRole-9PWFlGlm9I12 \
  --region us-west-1

kubectl rollout restart deployment/admin-service deployment/streaming-service -n default
```

### NLB Connection Timeout (ERR_CONNECTION_TIMED_OUT)

```bash
# Step 1: Check NLB scheme (must be internet-facing)
aws elbv2 describe-load-balancers --region us-west-1 \
  --query 'LoadBalancers[?contains(DNSName,`k8s-ingressn`)].{Scheme:Scheme}'

# If "internal", annotate nginx service to recreate as internet-facing:
kubectl annotate svc ingress-nginx-controller -n ingress-nginx \
  service.beta.kubernetes.io/aws-load-balancer-scheme=internet-facing --overwrite

# Step 2: After new NLB is created, find its frontend security group
aws ec2 describe-security-groups --region us-west-1 \
  --query 'SecurityGroups[?contains(GroupName,`k8s-ingressn`)].{ID:GroupId,Name:GroupName}'

# Step 3: Add port 80/443 to NLB frontend SG
aws ec2 authorize-security-group-ingress \
  --region us-west-1 --group-id <NLB_SG_ID> \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
```

### Frontend Still Shows PLACEHOLDER URLs

```bash
# Docker reused cached layers — must force recompile
docker build --no-cache \
  --build-arg REACT_APP_AUTH_API_URL=/api/auth \
  ... (all build args) \
  -t <ECR>/streamingapp-frontend-pp:latest frontend/

docker push <ECR>/streamingapp-frontend-pp:latest
kubectl rollout restart deployment/frontend -n default
```

---

## 21. Challenges & Solutions

### Challenge 1 — Kubernetes Version Compatibility

**Problem:** `eksctl create cluster` failed — Kubernetes 1.29 no longer supported.

**Solution:** Updated to `version: "1.32"`, changed `amiFamily: AmazonLinux2` to `AmazonLinux2023` (AL2 deprecated November 2025).

---

### Challenge 2 — kubectl 401 from Static Credentials Overriding Instance Profile

**Problem:** `kubectl get nodes` returned 401 Unauthorized on the Jenkins EC2. The EC2 had an instance profile attached with system:masters access, but `aws sts get-caller-identity` showed the IAM user ARN, not the role ARN.

**Root cause:** `~/.aws/credentials` file with static IAM user credentials takes precedence over the EC2 instance metadata in the AWS credential provider chain. The kubernetes token was being generated under the IAM user identity. While the user was in aws-auth, the mapping had not been verified as active.

**Solution:**
```bash
mv ~/.aws/credentials ~/.aws/credentials.bak
aws sts get-caller-identity   # Now shows role ARN
aws eks update-kubeconfig --name streamingapp-cluster-pp --region us-west-1
kubectl get nodes              # Works
```

**Learning:** AWS credential precedence: env vars → `~/.aws/credentials` file → instance metadata. The instance profile is only used when nothing higher in the chain is present.

---

### Challenge 3 — Helm --atomic Timeout on First Deploy

**Problem:** `helm install --atomic --timeout 10m` timed out. Auth and streaming pods were in `0/1 Running` with restarts, causing the install to roll back.

**Root cause:** The `--atomic` flag has a hard timeout. On first deploy, all 11 pods start simultaneously and compete for MongoDB Atlas connections. Auth and streaming services were starting but their httpGet liveness probes (initialDelaySeconds: 30) fired before MongoDB connections were established, causing restarts that accumulated past the atomic timeout.

**Solution:** Deploy without `--atomic` on first attempt to allow pods to stabilize:
```bash
helm install streamingapp-pp helm/streamingapp/ --namespace default
kubectl scale deployment healing-controller --replicas=0 -n default  # pause healer
# Wait for all pods to reach 1/1 Running, then scale healer back up
```

**Learning:** `--atomic` is correct for CI/CD upgrades but can be too strict for first deploys on resource-constrained clusters. Use `--timeout 15m` for subsequent atomic deploys.

---

### Challenge 4 — NLB Provisioned as Internal (Not Internet-Facing)

**Problem:** Application URL returned ERR_CONNECTION_TIMED_OUT. nginx ingress controller was running, all pods were healthy, but no traffic reached the cluster.

**Root cause:** The AWS Load Balancer Controller provisioned the nginx ingress service as an **internal** NLB (only reachable within the EKS VPC). Without the `internet-facing` annotation, this is the default. The Jenkins EC2 is in a different VPC (172.31.x.x default VPC) — no VPC peering, so even EC2 → NLB calls timed out.

**Solution:**
```bash
kubectl annotate svc ingress-nginx-controller -n ingress-nginx \
  service.beta.kubernetes.io/aws-load-balancer-scheme=internet-facing --overwrite
```

The controller deletes the internal NLB and creates a new internet-facing NLB with a new DNS name. All references to the old URL must be updated.

**Follow-up:** The new NLB's frontend security group (`k8s-ingressn-*`) had no inbound rules for port 80. Added manually via AWS CLI since the controller didn't auto-populate internet-facing rules.

---

### Challenge 5 — Frontend Built with PLACEHOLDER URLs

**Problem:** Login returned `ERR_NAME_NOT_RESOLVED` — the browser was calling `http://placeholder/api/auth/login`.

**Root cause:** The ECR image was built in a previous session with `REACT_APP_AUTH_API_URL=http://PLACEHOLDER/api`. React `REACT_APP_*` variables are baked into the compiled JavaScript bundle at build time. The new nginx URL wasn't known when the image was originally built.

**Solution:** Rebuild frontend with `--no-cache` and correct build args:
```bash
docker build --no-cache \
  --build-arg REACT_APP_AUTH_API_URL=/api/auth \
  ... \
  -t <ECR>/streamingapp-frontend-pp:latest frontend/
```

**Why `--no-cache`:** Docker cached the `npm run build` layer because source files hadn't changed. Without `--no-cache`, the cached compiled bundle (with old PLACEHOLDER URLs) was reused even with new `--build-arg` values. The content hash of the compiled JS bundle confirms whether the rebuild actually ran.

---

### Challenge 6 — CORS Errors After nginx URL Changed

**Problem:** Login returned 500 Internal Server Error. Auth service logs showed `Error: Not allowed by CORS`.

**Root cause:** The auth service reads `CLIENT_URLS` from the app-config ConfigMap at pod startup time and uses it as the CORS allowed origin. After the nginx URL changed (internal → internet-facing NLB), the ConfigMap was updated via `helm upgrade --set clientUrls=...` but running pods still had the old value in memory. Kubernetes does NOT live-reload environment variables from ConfigMaps.

**Solution:**
```bash
helm upgrade streamingapp-pp helm/streamingapp/ \
  --set clientUrls="http://<new-nginx-url>" --reuse-values

kubectl rollout restart deployment/auth-service deployment/streaming-service \
  deployment/admin-service deployment/chat-service -n default
```

**Learning:** ConfigMap changes require pod restarts to take effect when values are mounted as environment variables. This is intentional — it prevents live config changes from accidentally affecting running production pods.

---

### Challenge 7 — Auth Service Route Path Mismatch (404 on Login)

**Problem:** Login returned 404 Not Found even after CORS was fixed.

**Root cause:** The nginx ingress forwards the full path to backend services. For a request to `/api/auth/login`:
- nginx routes `/api/auth` → auth-service, forwarding full path `/api/auth/login`
- auth-service had `app.use('/api', userRoute)` — userRoute received `/auth/login`
- userRoute has `router.post('/login', ...)` — tries to match `/login` against `/auth/login` → no match → 404

**Solution:** Change auth service route mounting to match what nginx forwards:
```javascript
// Before:
app.use('/api', userRoute);
// After:
app.use('/api/auth', userRoute);  // strip /api/auth → userRoute sees /login ✅
```

Rebuild auth image and rollout restart.

---

### Challenge 8 — Streaming Service Doubled Path Prefix

**Problem:** Browse page showed no videos. Streaming API calls returned 404. Browser called `/api/streaming/streaming/videos/featured` — note the doubled `/streaming/streaming/`.

**Root cause:** The React streaming service sets `baseURL: '/api/streaming'` (from `REACT_APP_STREAMING_API_URL`). The service methods call paths like `streamingApi.get('/streaming/videos/featured')`. Combined: `/api/streaming` + `/streaming/videos/featured` = `/api/streaming/streaming/videos/featured`.

Nginx forwards the full path to the streaming service. The streaming service has `app.use('/api/streaming', streamingRoutes)` — routes receive `/streaming/videos/featured`. Routes define `router.get('/videos/featured', ...)` — no match for `/streaming/videos/featured`.

**Solution — Dual mount (avoids frontend rebuild):**
```javascript
// Handle doubled prefix from frontend API calls:
app.use('/api/streaming/streaming', streamingRoutes);
// Handle single prefix from direct video stream/thumbnail URLs:
app.use('/api/streaming', streamingRoutes);
```

Express handles both correctly — the more specific mount `/api/streaming/streaming` matches first for API calls, and the more general `/api/streaming` handles direct stream URLs.

---

### Challenge 9 — S3 Upload Failing (InvalidAccessKeyId: USE-INSTANCE-PROFILE)

**Problem:** Admin thumbnail/video upload returned 500. Logs showed `InvalidAccessKeyId: The AWS Access Key Id you provided does not exist in our records. AWSAccessKeyId: 'USE-INSTANCE-PROFILE'`.

**Root cause:** The `aws-secrets` Kubernetes secret contained the literal string `USE-INSTANCE-PROFILE` as the access key — a placeholder that was set as a reminder to use instance profiles. The S3 client in the admin service reads `AWS_ACCESS_KEY_ID` from env vars and passes it directly to the SDK. The SDK received `USE-INSTANCE-PROFILE` as an actual access key ID and failed to authenticate.

**Solution — Use the code's existing instance profile fallback:**
The `buildAwsCredentials()` function in `s3.js` already returns `undefined` when credentials are falsy:
```javascript
if (accessKeyId && secretAccessKey) { return { accessKeyId, secretAccessKey }; }
return undefined;  // AWS SDK falls back to instance profile
```

1. Set secret values to empty strings — `buildAwsCredentials()` returns `undefined`
2. Add `AmazonS3FullAccess` to node IAM role
3. SDK uses node instance profile automatically

```bash
aws iam attach-role-policy \
  --role-name eksctl-streamingapp-cluster-pp-nod-NodeInstanceRole-9PWFlGlm9I12 \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

kubectl create secret generic aws-secrets \
  --from-literal=access-key-id="" \
  --from-literal=secret-access-key="" \
  --namespace default --dry-run=client -o yaml | kubectl apply -f -
```

---

### Challenge 10 — Healing Controller Made Debugging Impossible

**Problem:** When diagnosing auth/streaming pod failures, pod names kept changing faster than logs could be retrieved. `kubectl logs auth-service-xxx` returned "pod not found" every 30 seconds.

**Root cause:** The healing controller detected `restart_count >= 3` and deleted pods. Kubernetes ReplicaSets created new pods with new names. This is the healer working correctly — but it prevents reading `--previous` logs during debugging.

**Solution:** Pause the healing controller during debug sessions:
```bash
kubectl scale deployment healing-controller --replicas=0 -n default
# Debug...
kubectl scale deployment healing-controller --replicas=1 -n default
```

---

## 22. Cost Analysis

### Monthly Cost Estimate (us-west-1)

| Resource | Specification | Cost/Month |
|----------|--------------|-----------|
| EKS Control Plane | Managed | $73.00 |
| EC2 Worker Nodes | 2 × t3.medium | $60.35 |
| EC2 Jenkins | 1 × t3.medium | $30.17 |
| EBS Volumes | gp3, 20GB × 3 | $4.80 |
| Network Load Balancer | 1 (nginx ingress) | $16.43 |
| NAT Gateway | 1 | $32.85 |
| ECR Storage | ~5GB | $0.50 |
| S3 Storage | ~10GB | $0.23 |
| CloudWatch Logs | Control plane logs | ~$2.00 |
| **Total** | | **~$220/month** |

### Cost Optimizations Applied

- MongoDB Atlas free tier (saves ~$57/month vs AWS DocumentDB)
- S3 for video storage (far cheaper than EBS for large files)
- Single NLB shared via nginx ingress (saves ~$65/month vs one ALB per service)
- `gp3` volumes (20% cheaper than `gp2` with better baseline throughput)

---

## 23. Future Improvements

### Pending (Next Steps)

- [ ] Jenkins GitHub webhook — auto-trigger pipeline on push to `main`
- [ ] Cluster Autoscaler installation
- [ ] Alertmanager Slack webhook configuration
- [ ] Loki + Fluent Bit for log aggregation
- [ ] Grafana nginx ingress exposure (permanent URL without SSH tunnel)

### Future Enhancements

- **HTTPS:** AWS Certificate Manager + nginx ingress TLS annotation
- **IRSA:** Fine-grained pod-level S3 permissions via OIDC (replace node role approach)
- **ArgoCD:** GitOps pull-based deployment replacing Jenkins push model
- **Network Policies:** Restrict inter-pod communication to only necessary paths
- **External Secrets Operator:** AWS Secrets Manager integration
- **Multi-environment:** dev/staging/prod namespaces with per-environment values

---

## 24. Project Structure

```
StreamingApp/
├── backend/
│   ├── authService/
│   │   ├── Dockerfile              # node:18-alpine, port 3001
│   │   ├── index.js                # app.use('/api/auth', userRoute)
│   │   ├── routes/healthCheck.route.js
│   │   └── util/conn.js            # MongoDB connection (process.exit on failure)
│   ├── streamingService/           # port 3002 — dual mount fix applied
│   ├── adminService/               # port 3003 — S3 via instance profile
│   └── chatService/                # port 3004 — Socket.IO + REST history
│
├── frontend/
│   ├── Dockerfile                  # Multi-stage: node build → nginx (~23MB)
│   ├── nginx.conf                  # SPA routing + health endpoint + gzip
│   └── src/
│       ├── config/env.js           # REACT_APP_* → fallback to localhost
│       └── services/
│           ├── api.js              # axios baseURL from AUTH_API_URL
│           └── auth.service.js     # login, register, verify, logout
│
├── healing-controller/
│   ├── Dockerfile                  # python:3.11-slim, non-root user
│   ├── main.py                     # Watch stream + periodic scan + cooldowns
│   └── requirements.txt            # kubernetes==29.0.0
│
├── helm/streamingapp/
│   ├── Chart.yaml
│   ├── values.yaml                 # All images with -pp suffix
│   └── templates/
│       ├── configmap.yaml
│       ├── auth-deployment.yaml    # httpGet /health probe
│       ├── streaming-deployment.yaml  # httpGet /api/health, CPU 250m
│       ├── admin-deployment.yaml   # tcpSocket probe
│       ├── chat-deployment.yaml    # tcpSocket probe
│       ├── frontend-deployment.yaml
│       ├── healing-controller.yaml # ServiceAccount + RBAC + Deployment
│       ├── ingress.yaml            # ingressClassName: nginx + WebSocket annotations
│       ├── hpa.yaml                # streaming max 8, auth max 6, frontend max 6
│       └── pdb.yaml                # minAvailable: 1 for auth, streaming, frontend
│
├── monitoring-rules.yaml           # PrometheusRule — apply after Prometheus install
├── cluster-config.yaml             # eksctl definition (AS BUILT — do not recreate)
├── Jenkinsfile                     # 6-stage pipeline with parallel build/push
├── docker-compose.yml              # Local development stack
└── README.md                       # This file
```

---

## Quick Reference

```bash
# Connect to cluster
aws eks update-kubeconfig --name streamingapp-cluster-pp --region us-west-1

# Check all pods
kubectl get pods -n default
kubectl get pods -n monitoring

# Get nginx ingress URL
kubectl get svc ingress-nginx-controller -n ingress-nginx \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Deploy
helm install streamingapp-pp helm/streamingapp/ -n default --atomic --timeout 12m

# Upgrade
helm upgrade streamingapp-pp helm/streamingapp/ -n default --reuse-values

# Healing controller logs
kubectl logs -l app=healing-controller -n default -f

# HPA status
kubectl get hpa -n default -w

# Grafana access (port-forward + SSH tunnel from Windows)
kubectl port-forward pod/$(kubectl get pod -n monitoring \
  -l "app.kubernetes.io/name=grafana" -oname) 3000 -n monitoring &
# Windows: ssh -i "streamingapp-pp.pem" -L 3000:localhost:3000 ubuntu@<EC2_IP>
# Browser: http://localhost:3000  |  admin / <your-password>

# Promote user to admin
kubectl exec -it deployment/auth-service -n default -- \
  node -e "const m=require('mongoose');m.connect(process.env.MONGO_URI).then(async()=>{await m.connection.db.collection('users').updateOne({email:'you@example.com'},{\$set:{role:'admin'}});console.log('Done');process.exit(0)})"
```

---

*StreamingApp*
*AWS EKS · Kubernetes 1.32 · Jenkins CI/CD · Prometheus · Grafana · Python Self-Healing*
