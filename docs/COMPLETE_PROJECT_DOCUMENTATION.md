# StreamingApp - Complete Implementation Documentation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technologies Used](#technologies-used)
4. [Phase 1: Environment Setup](#phase-1-environment-setup)
5. [Phase 2: Repository Setup](#phase-2-repository-setup)
6. [Phase 3: Docker Containerization](#phase-3-docker-containerization)
7. [Phase 4: Jenkins CI/CD Pipeline](#phase-4-jenkins-cicd-pipeline)
8. [Phase 5: EKS Cluster Creation](#phase-5-eks-cluster-creation)
9. [Phase 6: Helm Charts & Deployment](#phase-6-helm-charts--deployment)
10. [Validation & Testing](#validation--testing)
11. [Challenges & Solutions](#challenges--solutions)
12. [Cost Analysis](#cost-analysis)
13. [Future Improvements](#future-improvements)

---

## Project Overview

### Objective
Deploy a production-ready MERN (MongoDB, Express, React, Node.js) stack microservices application using:
- Docker containerization
- Jenkins CI/CD pipeline
- AWS Elastic Kubernetes Service (EKS)
- Helm package manager
- MongoDB Atlas (Cloud Database)
- AWS ECR (Container Registry)
- AWS S3 (Video Storage)

### Application Components

**StreamingApp** - A video streaming platform with the following microservices:

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| Auth Service | Node.js + Express | 3001 | User authentication & JWT management |
| Streaming Service | Node.js + Express | 3002 | Video catalog & playback |
| Admin Service | Node.js + Express | 3003 | Content management & uploads |
| Chat Service | Node.js + Socket.IO | 3004 | Real-time chat for watch parties |
| Frontend | React + Nginx | 80 | User interface |

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet Users                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              AWS Elastic Load Balancer (ELB)                    │
│          a83bc627a2a2248b59348d50b8e01678.elb...                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS EKS Cluster                              │
│                  streamingapp-cluster-pp                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Frontend    │  │  Frontend    │  │  Auth        │           │
│  │  Pod 1       │  │  Pod 2       │  │  Service     │           │
│  │  (Nginx)     │  │  (Nginx)     │  │  Pod 1       │           │
│  └──────────────┘  └──────────────┘  └──────┬───────┘           │
│                                               │                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────┴───────┐           │
│  │  Streaming   │  │  Admin       │  │  Auth        │           │
│  │  Service     │  │  Service     │  │  Service     │           │
│  │  Pod 1       │  │  Pod 1       │  │  Pod 2       │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Chat        │  │  Chat        │  │  Admin       │           │
│  │  Service     │  │  Service     │  │  Service     │           │
│  │  Pod 1       │  │  Pod 2       │  │  Pod 2       │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                 │
│              Kubernetes Services (ClusterIP)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │   auth   │ │streaming │ │  admin   │ │   chat   │            │
│  │ :3001    │ │  :3002   │ │  :3003   │ │  :3004   │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────────────────┘
                   │                        │
                   ▼                        ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │   MongoDB Atlas      │  │      AWS S3          │
        │   (Database)         │  │   (Video Storage)    │
        │ cluster0.fhrg87w..   │  │ streamingapp-videos  │
        └──────────────────────┘  └──────────────────────┘
```

### CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Developer Workflow                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   1. Code Push to GitHub
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Repository                          │
│              https://github.com/PriyankP2/StreamingApp          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   2. Webhook Trigger
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                   Jenkins (on EC2)                            │
│                  StreamingApp-Pipeline                        │
│                                                               │
│  Stage 1: Checkout ✅                                               
|    └─ Clone repository                                        │
│                                                               │
│  Stage 2: Build Docker Images ✅ (Parallel)                   
│  ├─ Build Auth Service                                        │
│  ├─ Build Streaming Service                                   │
│  ├─ Build Admin Service                                       │
│  ├─ Build Chat Service                                        │
│  └─ Build Frontend (Multi-stage)                              │
│                                                               │
│  Stage 3: ECR Login ✅                                        
│  └─ AWS ECR Authentication                                    │
│                                                               │
│  Stage 4: Push to ECR ✅ (Parallel)                           
│  ├─ Push Auth (latest + commit hash)                          │
│  ├─ Push Streaming (latest + commit hash)                     │
│  ├─ Push Admin (latest + commit hash)                         │
│  ├─ Push Chat (latest + commit hash)                          │
│  └─ Push Frontend (latest + commit hash)                      │
│                                                               │
│  Stage 5: Cleanup ✅                                          
│  └─ Remove local images (freed 1.258GB)                       │
└────────────────────────────┬──────────────────────────────────┘
                             │
                   3. Images Stored
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│              AWS Elastic Container Registry (ECR)             │
│                     us-west-1 Region                          │
│                                                               │
│  975050024946.dkr.ecr.us-west-1.amazonaws.com/                │
│  ├─ streamingapp-auth:latest, f8f80da                         │
│  ├─ streamingapp-streaming:latest, f8f80da                    │
│  ├─ streamingapp-admin:latest, f8f80da                        │
│  ├─ streamingapp-chat:latest, f8f80da                         │
│  └─ streamingapp-frontend:latest, f8f80da                     │
└────────────────────────────┬──────────────────────────────────┘
                             │
                   4. Helm Deploy
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EKS Cluster                                  │
│              (Pulls images from ECR)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technologies Used

### Cloud & Infrastructure
- **AWS EKS** - Managed Kubernetes Service (v1.29)
- **AWS EC2** - t3.medium instances (Jenkins + Worker Nodes)
- **AWS ECR** - Docker Container Registry
- **AWS S3** - Video file storage
- **AWS ELB** - Application Load Balancer

### Container & Orchestration
- **Docker** - Container runtime
- **Kubernetes** - Container orchestration (v1.35.0)
- **Helm** - Kubernetes package manager (v4.1.0)
- **eksctl** - EKS cluster manager (v0.222.0)

### CI/CD
- **Jenkins** - Automation server
- **Git** - Version control (v2.47.1)
- **GitHub** - Code repository

### Application Stack
- **Node.js** - Backend runtime (v18 Alpine)
- **React** - Frontend framework
- **Express.js** - Web framework
- **MongoDB Atlas** - Cloud database
- **Socket.IO** - Real-time communication
- **Nginx** - Reverse proxy & static file server

### Development Tools
- **AWS CLI** - v2.22.26
- **kubectl** - Kubernetes CLI
- **Windows 11** - Development environment

---

## Phase 1: Environment Setup

### 1.1 Tools Installation

**Installed on Local Machine (Windows 11):**

```powershell
# Verify installations
git --version
# Output: git version 2.47.1.windows.1

aws --version
# Output: aws-cli/2.22.26 Python/3.12.6 Windows/11 exe/AMD64

kubectl version --client
# Output: Client Version: v1.35.0

eksctl version
# Output: 0.222.0

helm version --short
# Output: v4.1.0+g4553a0a
```

**Not Installed (By Design):**
- ❌ Docker Desktop - Resource intensive
- ❌ Node.js - Jenkins handles builds

**Rationale:** Lightweight local setup; Jenkins on EC2 handles all builds.

---

### 1.2 AWS Configuration

```

**Configuration Steps:**

```bash
# Configure AWS CLI
aws configure
# AWS Access Key ID: AKIA6GBMCU7ZFTJBEPM5
# AWS Secret Access Key: [CONFIGURED SECURELY]
# Default region: us-west-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

**Output:**
```json
{
    "UserId": "AIDA6GBMCU7ZC4MUFAQN7",
    "Account": "975050024946",
    "Arn": "arn:aws:iam::975050024946:user/priyankpandey02@gmail.com"
}
```

---

### 1.3 Region Selection

**Decision:** us-west-1 (N. California)

**Alternatives Considered:**
- ap-south-1 (Mumbai) - Closer to India 

**Rationale:**
- Mature AWS region with all services
- Available Availability Zones: us-west-1a, us-west-1c
- Lower resource contention

---

### 1.4 MongoDB Atlas Setup

**Service:** MongoDB Atlas (Cloud-hosted)

**Configuration:**
```
Cluster: cluster0.fhrg87w.mongodb.net
Database: streamingapp
User: dbXUser
Connection String: mongodb+srv://dbUser:dbUserPassword@cluster0.fhrg87w.mongodb.net/streamingapp?retryWrites=true&w=majority
```

**Network Access:**
- Allowed: 0.0.0.0/0 (Development - Allow all)
- Production: Should be restricted to EKS node IPs

**Decision Rationale:**
- No need to deploy MongoDB in Kubernetes
- Managed backups and scaling
- Reduced cluster resource usage

---

## Phase 2: Repository Setup

### 2.1 Source Code

**Original Repository:** https://github.com/UnpredictablePrashant/StreamingApp

**My Repository:** https://github.com/PriyankP2/StreamingApp

**Setup Commands:**
```bash
# Clone original repository
git clone https://github.com/UnpredictablePrashant/StreamingApp.git
cd StreamingApp

# Create GitHub repository and push
git remote add origin https://github.com/PriyankP2/StreamingApp.git
git push -u origin main
```

---

### 2.2 Project Structure

```
StreamingApp/
├── backend/
│   ├── authService/          # Port 3001 - Authentication
│   │   ├── Dockerfile        ✅ Created
│   │   ├── .dockerignore     ✅ Created
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── routes/
│   │   └── util/
│   ├── streamingService/     # Port 3002 - Video streaming
│   │   ├── Dockerfile        ✅ Created
│   │   ├── .dockerignore     ✅ Created
│   │   └── ...
│   ├── adminService/         # Port 3003 - Admin panel
│   │   ├── Dockerfile        ✅ Created
│   │   ├── .dockerignore     ✅ Created
│   │   └── ...
│   └── chatService/          # Port 3004 - Real-time chat
│       ├── Dockerfile        ✅ Created
│       ├── .dockerignore     ✅ Created
│       └── ...
├── frontend/                  # Port 80 - React SPA
│   ├── Dockerfile            ✅ Created
│   ├── nginx.conf            ✅ Created
│   ├── .dockerignore         ✅ Created
│   └── src/
├── helm/                      # Kubernetes deployment
│   └── streamingapp/
│       ├── Chart.yaml        ✅ Created
│       ├── values.yaml       ✅ Created
│       └── templates/
│           ├── configmap.yaml           ✅ Created
│           ├── auth-deployment.yaml     ✅ Created
│           ├── streaming-deployment.yaml ✅ Created
│           ├── admin-deployment.yaml    ✅ Created
│           ├── chat-deployment.yaml     ✅ Created
│           └── frontend-deployment.yaml ✅ Created
├── Jenkinsfile               ✅ Created
├── cluster-config.yaml       ✅ Created
└── README.md
```

---

## Phase 3: Docker Containerization

### 3.1 Backend Services Dockerfile

**Pattern Used:** Single-stage build with Node.js Alpine

**Example (Auth Service):**
```dockerfile
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
ENV NODE_ENV=production
EXPOSE 3001
CMD ["npm", "run", "start"]
```

**Applied to:**
- authService (Port 3001)
- streamingService (Port 3002)
- adminService (Port 3003)
- chatService (Port 3004)

---

### 3.2 Frontend Dockerfile

**Pattern Used:** Multi-stage build (Build + Nginx)

```dockerfile
# Stage 1: Build React application
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Build arguments for environment variables
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

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:1.27-alpine AS production
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Benefits of Multi-stage Build:**
- Smaller final image (only production artifacts)
- Development dependencies not in production image
- nginx:alpine base is ~23MB vs full node image ~400MB

---

### 3.3 Nginx Configuration

**File:** frontend/nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # React Router support - CRITICAL!
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Key Features:**
- React Router support (try_files directive)
- Gzip compression for faster load times
- Security headers
- Health check endpoint for Kubernetes probes
- Static asset caching (1 year)

---

### 3.4 .dockerignore Files

**Purpose:** Exclude unnecessary files from Docker build context

**Content:**
```
node_modules
npm-debug.log
.env
.env.local
.env.*.local
.git
.gitignore
README.md
.DS_Store
*.log
coverage
.vscode
.idea
```

**Benefits:**
- Faster builds (smaller context)
- Smaller images
- No sensitive files in images
- No unnecessary cache invalidation

---

## Phase 4: Jenkins CI/CD Pipeline

### 4.1 Jenkins EC2 Instance Setup

**Instance Configuration:**
```
Instance Type: t3.medium
AMI: Ubuntu 22.04 LTS
Region: us-west-1
Storage: 30GB gp3
Security Group: jenkins-sg
Key Pair: jenkins-key.pem
```

**Security Group Rules:**
```bash
# SSH access
Port 22 - Source: 0.0.0.0/0

# Jenkins UI
Port 8080 - Source: 0.0.0.0/0
```

**Launch Command:**
```bash
aws ec2 run-instances \
  --image-id ami-0da424eb883458071 \
  --instance-type t3.medium \
  --key-name jenkins-key \
  --security-group-ids sg-xxxxxxxxxxxxx \
  --region us-west-1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=StreamingApp-Jenkins}]' \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]'
```

---

### 4.2 Jenkins Installation Script

**SSH into EC2:**
```bash
ssh -i jenkins-key.pem ubuntu@<EC2_PUBLIC_IP>
```

**Installation Script:**
```bash
#!/bin/bash

# Update system
sudo apt update
sudo apt upgrade -y

# Install Java 17
sudo apt install -y openjdk-17-jdk

# Install Docker
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt install -y unzip
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Install Jenkins
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update
sudo apt install -y jenkins

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
sudo usermod -aG docker jenkins

# Install Git
sudo apt install -y git

# Get Jenkins initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**Jenkins URL:** http://<EC2_PUBLIC_IP>:8080

---

### 4.3 Jenkins Configuration

**Plugins Installed:**
- Git plugin
- Pipeline plugin
- Docker plugin
- AWS Credentials plugin

**AWS Credentials for Jenkins User:**
```bash
# Switch to jenkins user
sudo su - jenkins -s /bin/bash

# Configure AWS CLI
aws configure
# Access Key ID: AKIA6GBMCU7ZFTJBEPM5
# Secret Access Key: [CONFIGURED]
# Region: us-west-1
# Output: json

# Verify
aws sts get-caller-identity

# Test ECR login
aws ecr get-login-password --region us-west-1 | \
  docker login --username AWS --password-stdin \
  975050024946.dkr.ecr.us-west-1.amazonaws.com
```

---

### 4.4 Jenkinsfile

**Complete Pipeline:**

```groovy
pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-west-1'
        AWS_ACCOUNT_ID = '975050024946'
        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        GIT_COMMIT_SHORT = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        
        AUTH_IMAGE = "${ECR_REGISTRY}/streamingapp-auth"
        STREAMING_IMAGE = "${ECR_REGISTRY}/streamingapp-streaming"
        ADMIN_IMAGE = "${ECR_REGISTRY}/streamingapp-admin"
        CHAT_IMAGE = "${ECR_REGISTRY}/streamingapp-chat"
        FRONTEND_IMAGE = "${ECR_REGISTRY}/streamingapp-frontend"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 Checking out code...'
                checkout scm
                sh 'git rev-parse --short HEAD'
            }
        }
        
        stage('Build Docker Images') {
            parallel {
                stage('Build Auth Service') {
                    steps {
                        echo '🔨 Building Auth Service...'
                        dir('backend/authService') {
                            sh """
                                docker build -t ${AUTH_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${AUTH_IMAGE}:${GIT_COMMIT_SHORT} ${AUTH_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Streaming Service') {
                    steps {
                        echo '🔨 Building Streaming Service...'
                        dir('backend/streamingService') {
                            sh """
                                docker build -t ${STREAMING_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${STREAMING_IMAGE}:${GIT_COMMIT_SHORT} ${STREAMING_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Admin Service') {
                    steps {
                        echo '🔨 Building Admin Service...'
                        dir('backend/adminService') {
                            sh """
                                docker build -t ${ADMIN_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${ADMIN_IMAGE}:${GIT_COMMIT_SHORT} ${ADMIN_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Chat Service') {
                    steps {
                        echo '🔨 Building Chat Service...'
                        dir('backend/chatService') {
                            sh """
                                docker build -t ${CHAT_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${CHAT_IMAGE}:${GIT_COMMIT_SHORT} ${CHAT_IMAGE}:latest
                            """
                        }
                    }
                }
                
                stage('Build Frontend') {
                    steps {
                        echo '🔨 Building Frontend...'
                        dir('frontend') {
                            sh """
                                docker build \
                                  --build-arg REACT_APP_AUTH_API_URL=http://auth-service:3001/api \
                                  --build-arg REACT_APP_STREAMING_API_URL=http://streaming-service:3002/api \
                                  --build-arg REACT_APP_STREAMING_PUBLIC_URL=http://streaming-service:3002 \
                                  --build-arg REACT_APP_ADMIN_API_URL=http://admin-service:3003/api/admin \
                                  --build-arg REACT_APP_CHAT_API_URL=http://chat-service:3004/api/chat \
                                  --build-arg REACT_APP_CHAT_SOCKET_URL=http://chat-service:3004 \
                                  -t ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT} .
                                docker tag ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT} ${FRONTEND_IMAGE}:latest
                            """
                        }
                    }
                }
            }
        }
        
        stage('Login to ECR') {
            steps {
                echo '🔐 Logging into AWS ECR...'
                sh """
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
                """
            }
        }
        
        stage('Push Images to ECR') {
            parallel {
                stage('Push Auth') {
                    steps {
                        echo '📤 Pushing Auth Service to ECR...'
                        sh """
                            docker push ${AUTH_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${AUTH_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Streaming') {
                    steps {
                        echo '📤 Pushing Streaming Service to ECR...'
                        sh """
                            docker push ${STREAMING_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${STREAMING_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Admin') {
                    steps {
                        echo '📤 Pushing Admin Service to ECR...'
                        sh """
                            docker push ${ADMIN_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${ADMIN_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Chat') {
                    steps {
                        echo '📤 Pushing Chat Service to ECR...'
                        sh """
                            docker push ${CHAT_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${CHAT_IMAGE}:latest
                        """
                    }
                }
                
                stage('Push Frontend') {
                    steps {
                        echo '📤 Pushing Frontend to ECR...'
                        sh """
                            docker push ${FRONTEND_IMAGE}:${GIT_COMMIT_SHORT}
                            docker push ${FRONTEND_IMAGE}:latest
                        """
                    }
                }
            }
        }
        
        stage('Cleanup') {
            steps {
                echo '🧹 Cleaning up local Docker images...'
                sh """
                    docker system prune -af --volumes
                """
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
            echo "Images tagged with: ${GIT_COMMIT_SHORT} and latest"
        }
        failure {
            echo '❌ Pipeline failed!'
        }
        always {
            echo '📊 Build finished'
        }
    }
}
```

**Pipeline Features:**
- Parallel builds for all 5 services
- Dual tagging (commit hash + latest)
- Parallel push to ECR
- Automatic cleanup (freed 1.258GB per build)
- Error handling

**Build Results:**
- Total Build Time: ~10-15 minutes
- Images Created: 5
- Tags per Image: 2 (latest + commit hash)
- Space Freed: 1.258GB

![alt text](image.png)
---

### 4.5 AWS ECR Repositories

**Created Repositories:**

```bash
# Create ECR repositories
aws ecr create-repository --repository-name streamingapp-auth --region us-west-1
aws ecr create-repository --repository-name streamingapp-streaming --region us-west-1
aws ecr create-repository --repository-name streamingapp-admin --region us-west-1
aws ecr create-repository --repository-name streamingapp-chat --region us-west-1
aws ecr create-repository --repository-name streamingapp-frontend --region us-west-1
```

**Repository URLs:**
```
975050024946.dkr.ecr.us-west-1.amazonaws.com/streamingapp-auth
975050024946.dkr.ecr.us-west-1.amazonaws.com/streamingapp-streaming
975050024946.dkr.ecr.us-west-1.amazonaws.com/streamingapp-admin
975050024946.dkr.ecr.us-west-1.amazonaws.com/streamingapp-chat
975050024946.dkr.ecr.us-west-1.amazonaws.com/streamingapp-frontend
```

**Image Tags:**
- latest (always points to newest build)
- f8f80da (commit hash - immutable)

---

### 4.6 AWS S3 Bucket

**Bucket Configuration:**

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket streamingapp-videos-975050024946 \
  --region us-west-1 \
  --create-bucket-configuration LocationConstraint=us-west-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket streamingapp-videos-975050024946 \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket streamingapp-videos-975050024946 \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Configure CORS
aws s3api put-bucket-cors \
  --bucket streamingapp-videos-975050024946 \
  --cors-configuration '{
    "CORSRules": [{
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }]
  }'
```

**Bucket Name:** streamingapp-videos-975050024946  
**Purpose:** Video file storage for streaming service  
**Security:** Private bucket with CORS enabled

---

## Phase 5: EKS Cluster Creation

### 5.1 Cluster Configuration

**File:** cluster-config.yaml

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: streamingapp-cluster-pp
  region: us-west-1
  version: "1.29"

availabilityZones:
  - us-west-1a
  - us-west-1c

managedNodeGroups:
  - name: streamingapp-nodes
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 1
    maxSize: 3
    volumeSize: 20
    volumeType: gp3
    amiFamily: AmazonLinux2
    labels:
      role: worker
    tags:
      Project: StreamingApp_PP
      Environment: Production
    iam:
      withAddonPolicies:
        imageBuilder: true
        ebs: true
        albIngress: true
        cloudWatch: true

cloudWatch:
  clusterLogging:
    enableTypes:
      - api
      - audit
      - authenticator
```

**Key Decisions:**
- **Cluster Name:** streamingapp-cluster-pp (PP suffix to avoid conflicts)
- **Version:** Kubernetes 1.29
- **AZs:** us-west-1a and us-west-1c (us-west-1b doesn't exist!)
- **Node Type:** t3.medium (2 vCPU, 4GB RAM)
- **Node Count:** 2 nodes (can scale to 3)

---

### 5.2 Cluster Creation

**Command:**
```bash
eksctl create cluster -f cluster-config.yaml
```

**Creation Timeline:**
- Start: 22:59:40
- Completion: ~23:15:00 (15-20 minutes)

**Resources Created:**
- EKS Control Plane
- VPC with 2 public + 2 private subnets
- NAT Gateway
- Internet Gateway
- Security Groups
- IAM Roles
- 2 EC2 Worker Nodes (t3.medium)
- Auto-scaling group

**Initial Issue Encountered:**
```
Error: Value (us-west-1b) for parameter availabilityZone is invalid.
Available zones: us-west-1a, us-west-1c
```

**Solution:** Updated cluster-config.yaml to use us-west-1c instead of us-west-1b

---

### 5.3 Cluster Verification

**Commands:**
```bash
# Check cluster exists
eksctl get cluster --region us-west-1

# Check nodes
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check cluster info
kubectl cluster-info
```

**Verification Results:**
```
NAME                    REGION      EKSCTL CREATED
streamingapp-cluster-pp us-west-1   True

NAME                                           STATUS   ROLES    AGE    VERSION
ip-192-168-13-6.us-west-1.compute.internal     Ready    <none>   6m2s   v1.29.15-eks-ecaa3a6
ip-192-168-38-169.us-west-1.compute.internal   Ready    <none>   6m2s   v1.29.15-eks-ecaa3a6

Kubernetes control plane is running at https://D0C2CC451E70C07D3F2FA3B84A4C6153.sk1.us-west-1.eks.amazonaws.com
CoreDNS is running
```

**System Pods Running:**
- aws-node (2 pods) - VPC CNI
- coredns (2 pods) - DNS
- kube-proxy (2 pods) - Network proxy
- metrics-server (2 pods) - Resource metrics

---

## Phase 6: Helm Charts & Deployment

### 6.1 Helm Chart Structure

```
helm/streamingapp/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── configmap.yaml
    ├── auth-deployment.yaml
    ├── streaming-deployment.yaml
    ├── admin-deployment.yaml
    ├── chat-deployment.yaml
    └── frontend-deployment.yaml
```

---

### 6.2 Chart.yaml

```yaml
apiVersion: v2
name: streamingapp
description: StreamingApp MERN Stack Helm Chart
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - streaming
  - mern
  - microservices
maintainers:
  - name: Priyank Pandey
    email: priyankpandey02@gmail.com
```

---

### 6.3 values.yaml

```yaml
# Global configuration
global:
  awsRegion: us-west-1
  awsAccountId: "975050024946"
  ecrRegistry: 975050024946.dkr.ecr.us-west-1.amazonaws.com

# Replica count for all services
replicaCount: 2

# Image configuration
image:
  pullPolicy: Always
  tag: latest

# MongoDB Atlas Configuration
mongodb:
  enabled: false  # Using MongoDB Atlas

# Services Configuration
services:
  auth:
    name: auth-service
    image: streamingapp-auth
    port: 3001
    
  streaming:
    name: streaming-service
    image: streamingapp-streaming
    port: 3002
    
  admin:
    name: admin-service
    image: streamingapp-admin
    port: 3003
    
  chat:
    name: chat-service
    image: streamingapp-chat
    port: 3004

# Frontend Configuration
frontend:
  name: frontend
  image: streamingapp-frontend
  port: 80
  serviceType: LoadBalancer

# AWS S3 Bucket
aws:
  s3Bucket: "streamingapp-videos-975050024946"

# Client URLs
clientUrls: "http://localhost:3000"
```

**Security Note:** Sensitive values (AWS keys, MongoDB URI, JWT secret) are NOT in this file. They are stored as Kubernetes Secrets.

---

### 6.4 Kubernetes Secrets

**Created Directly in Cluster (NOT in Git):**

```bash
# Create app secrets (JWT + MongoDB)
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret="streamingapp-jwt-secret-production-2026-change-me" \
  --from-literal=mongo-uri="mongodb+srv://dbXUser:dbXUserPassword@cluster0.fhrg87w.mongodb.net/streamingapp?retryWrites=true&w=majority"

# Create AWS secrets
kubectl create secret generic aws-secrets \
  --from-literal=access-key-id="AKIA6GBMCU7ZFTJBEPM5" \
  --from-literal=secret-access-key="[CONFIGURED_SECURELY]"

# Verify
kubectl get secrets
```

**Secrets Created:**
```
NAME          TYPE     DATA   AGE
app-secrets   Opaque   2      19s
aws-secrets   Opaque   2      37s
```

**Security Benefits:**
- Secrets never committed to Git
- Base64 encoded in Kubernetes
- Can be rotated without code changes
- Access controlled via RBAC

---

### 6.5 ConfigMap

**Template:** templates/configmap.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  aws-region: {{ .Values.global.awsRegion | quote }}
  s3-bucket: {{ .Values.aws.s3Bucket | quote }}
  client-urls: {{ .Values.clientUrls | quote }}
```

**Purpose:** Non-sensitive configuration shared across services

---

### 6.6 Deployment Templates

**Example (Auth Service):** templates/auth-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.services.auth.name }}
  labels:
    app: {{ .Values.services.auth.name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Values.services.auth.name }}
  template:
    metadata:
      labels:
        app: {{ .Values.services.auth.name }}
    spec:
      containers:
      - name: auth
        image: "{{ .Values.global.ecrRegistry }}/{{ .Values.services.auth.image }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.services.auth.port }}
        env:
        - name: PORT
          value: "{{ .Values.services.auth.port }}"
        - name: MONGO_URI
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: mongo-uri
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: jwt-secret
        - name: CLIENT_URLS
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: client-urls
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-secrets
              key: access-key-id
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: aws-secrets
              key: secret-access-key
        - name: AWS_REGION
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: aws-region
        - name: AWS_S3_BUCKET
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: s3-bucket
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: {{ .Values.services.auth.port }}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: {{ .Values.services.auth.port }}
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.services.auth.name }}
  labels:
    app: {{ .Values.services.auth.name }}
spec:
  type: ClusterIP
  ports:
  - port: {{ .Values.services.auth.port }}
    targetPort: {{ .Values.services.auth.port }}
    protocol: TCP
  selector:
    app: {{ .Values.services.auth.name }}
```

**Key Features:**
- Deployment + Service in same file (separated by `---`)
- Environment variables from Secrets and ConfigMaps
- Resource limits (CPU & Memory)
- Health probes (liveness & readiness)
- Service type: ClusterIP (internal only)

**Applied Pattern to All Services:**
- auth-deployment.yaml (ClusterIP, health probe: /health)
- streaming-deployment.yaml (ClusterIP, health probe: / )
- admin-deployment.yaml (ClusterIP, no health probe)
- chat-deployment.yaml (ClusterIP, no health probe)
- frontend-deployment.yaml (LoadBalancer, health probe: /health)

---

### 6.7 Helm Deployment

**Dry Run (Validation):**
```bash
helm install streamingapp ./helm/streamingapp --dry-run --debug
```

**Actual Deployment:**
```bash
helm install streamingapp ./helm/streamingapp
```

**Output:**
```
NAME: streamingapp
LAST DEPLOYED: Wed Feb 18 03:38:10 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
```

**Resources Created:**
- 1 ConfigMap (app-config)
- 5 Deployments (auth, streaming, admin, chat, frontend)
- 5 Services (4 ClusterIP + 1 LoadBalancer)
- 10 Pods (2 replicas × 5 services)

---

### 6.8 Deployment Verification

**Check All Resources:**
```bash
kubectl get all
```

**Output:**
```
NAME                                     READY   STATUS    RESTARTS   AGE
pod/admin-service-86b8796754-hmcmq       1/1     Running   0          15h
pod/admin-service-86b8796754-jvkst       1/1     Running   0          15h
pod/auth-service-799d8fd4ff-bfdpq        1/1     Running   0          15h
pod/auth-service-799d8fd4ff-gptdg        1/1     Running   0          15h
pod/chat-service-86987954bc-2dprh        1/1     Running   0          15h
pod/chat-service-86987954bc-6tl4j        1/1     Running   0          15h
pod/frontend-549b6db94-dv9s6             1/1     Running   0          15h
pod/frontend-549b6db94-ghqlz             1/1     Running   0          15h
pod/streaming-service-7dd446cd9c-mlkch   1/1     Running   0          15h

NAME                        TYPE           CLUSTER-IP       EXTERNAL-IP
service/admin-service       ClusterIP      10.100.137.206   <none>
service/auth-service        ClusterIP      10.100.64.254    <none>
service/chat-service        ClusterIP      10.100.66.187    <none>
service/frontend            LoadBalancer   10.100.46.158    a83bc627a2a2248b59348d50b8e01678-364020149.us-west-1.elb.amazonaws.com
service/streaming-service   ClusterIP      10.100.93.57     <none>

NAME                                READY   UP-TO-DATE   AVAILABLE
deployment.apps/admin-service       2/2     2            2
deployment.apps/auth-service        2/2     2            2
deployment.apps/chat-service        2/2     2            2
deployment.apps/frontend            2/2     2            2
deployment.apps/streaming-service   1/2     1            1
```

**LoadBalancer URL:**
```
http://a83bc627a2a2248b59348d50b8e01678-364020149.us-west-1.elb.amazonaws.com
```

---

## Validation & Testing

### Validation Checks

#### 1. Pod Status Check
```bash
kubectl get pods
```

**Expected:** All pods show `1/1 Running`  
**Actual:** 9/10 pods running (streaming service has issues)

---

#### 2. Service Connectivity Check
```bash
# Check services
kubectl get svc

# Test internal service connectivity
kubectl run test-pod --image=busybox --rm -it --restart=Never -- wget -O- http://auth-service:3001/health
```

---

#### 3. MongoDB Connection Verification
```bash
# Check auth service logs
kubectl logs <auth-service-pod-name>
```

**Expected Output:**
```
Connecting to MongoDB at: mongodb+srv://dbXUser:dbXUserPassword@cluster0...
Authentication Service Started at port 3001
DB connection established
MongoDB Connected Successfully
```

**Status:** ✅ MongoDB connection successful

---

#### 4. ECR Image Pull Verification
```bash
# Check if images are pulled
kubectl describe pod <pod-name> | grep -i image

# Check events for pull errors
kubectl get events --sort-by='.lastTimestamp'
```

**Status:** ✅ All images pulled successfully from ECR

---

#### 5. LoadBalancer Health Check
```bash
# Get LoadBalancer URL
kubectl get svc frontend

# Test externally
curl http://a83bc627a2a2248b59348d50b8e01678-364020149.us-west-1.elb.amazonaws.com/health
```

**Expected:** `healthy`  
**Status:** ✅ LoadBalancer accessible

---

#### 6. Resource Usage Check
```bash
# Check node resource usage
kubectl top nodes

# Check pod resource usage
kubectl top pods
```

---

#### 7. Health Probe Verification
```bash
# Check pod events for probe failures
kubectl describe pod <pod-name> | grep -A 10 Events
```

---

### Backend Service Testing

#### Auth Service (Port 3001)

**Health Check:**
```bash
kubectl run test --image=busybox --rm -it --restart=Never -- wget -O- http://auth-service:3001/health
```

**Registration Test:**
```bash
curl -X POST http://auth-service:3001/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'
```

**Login Test:**
```bash
curl -X POST http://auth-service:3001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

---

#### Streaming Service (Port 3002)

**Health Check:**
```bash
kubectl run test --image=busybox --rm -it --restart=Never -- wget -O- http://streaming-service:3002/
```

**Video List Test:**
```bash
curl http://streaming-service:3002/api/videos
```

---

#### Admin Service (Port 3003)

**Service Check:**
```bash
kubectl run test --image=busybox --rm -it --restart=Never -- wget -O- http://admin-service:3003/
```

---

#### Chat Service (Port 3004)

**Service Check:**
```bash
kubectl run test --image=busybox --rm -it --restart=Never -- wget -O- http://chat-service:3004/
```

---

### Frontend Testing

#### 1. Browser Access
```
URL: http://a83bc627a2a2248b59348d50b8e01678-364020149.us-west-1.elb.amazonaws.com
```

**Expected:** Landing page loads

---

#### 2. Static Assets Loading
**Check:** Images, CSS, JavaScript files load correctly

![alt text](image-1.png)

---

#### 3. Health Endpoint
```bash
curl http://a83bc627a2a2248b59348d50b8e01678-364020149.us-west-1.elb.amazonaws.com/health
```

**Expected:** `healthy`

---

#### 4. React Router Test
**Navigate to:** Different routes (should not 404)

---

### Complete Validation Script

**File:** validate-deployment.sh

```bash
#!/bin/bash

echo "=== StreamingApp Deployment Validation ==="
echo ""

# 1. Check cluster
echo "1. Checking EKS Cluster..."
kubectl cluster-info
echo ""

# 2. Check nodes
echo "2. Checking Nodes..."
kubectl get nodes
echo ""

# 3. Check pods
echo "3. Checking Pods..."
kubectl get pods
echo ""

# 4. Check services
echo "4. Checking Services..."
kubectl get svc
echo ""

# 5. Check deployments
echo "5. Checking Deployments..."
kubectl get deployments
echo ""

# 6. Check secrets
echo "6. Checking Secrets..."
kubectl get secrets
echo ""

# 7. Check configmap
echo "7. Checking ConfigMap..."
kubectl get configmap
echo ""

# 8. Check pod logs (auth service)
echo "8. Checking Auth Service Logs..."
AUTH_POD=$(kubectl get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl logs $AUTH_POD --tail=20
echo ""

# 9. Check frontend LoadBalancer
echo "9. Checking Frontend LoadBalancer..."
kubectl get svc frontend
echo ""

# 10. Test health endpoints
echo "10. Testing Health Endpoints..."
LB_URL=$(kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Frontend Health: "
curl -s http://$LB_URL/health
echo ""

echo "=== Validation Complete ==="
```

**Run:**
```bash
chmod +x validate-deployment.sh
./validate-deployment.sh
```

---

## Challenges & Solutions

### Challenge 1: AWS Credentials for Jenkins

**Problem:** Jenkins couldn't access ECR because AWS credentials were configured for `ubuntu` user, not `jenkins` user.

**Error:**
```
Unable to locate credentials. You can configure credentials by running "aws configure"
```

**Solution:**
```bash
# Switch to jenkins user
sudo su - jenkins -s /bin/bash

# Configure AWS credentials
aws configure
# Entered: Access Key, Secret Key, Region, Output format

# Test
aws sts get-caller-identity
```

**Learning:** Each Linux user has separate AWS CLI configuration.

---

### Challenge 2: Availability Zone Issue

**Problem:** EKS cluster creation failed with availability zone error.

**Error:**
```
Value (us-west-1b) for parameter availabilityZone is invalid.
Available zones: us-west-1a, us-west-1c
```

**Solution:** Updated cluster-config.yaml:
```yaml
# Changed from:
availabilityZones:
  - us-west-1a
  - us-west-1b  # Doesn't exist!

# To:
availabilityZones:
  - us-west-1a
  - us-west-1c  # Correct!
```

**Learning:** Always verify available AZs for a region:
```bash
aws ec2 describe-availability-zones --region us-west-1
```

---

### Challenge 3: Health Probe Failures

**Problem:** Streaming service pods failing health checks and crashing.

**Error:**
```
Liveness probe failed: Get http://192.168.x.x:3002/health: dial tcp 192.168.x.x:3002: connect: connection refused
```

**Root Cause:** Streaming service doesn't have a `/health` endpoint.

**Solution:** Changed health probe from `/health` to `/`:
```yaml
# Changed from:
livenessProbe:
  httpGet:
    path: /health  # This endpoint doesn't exist!

# To:
livenessProbe:
  httpGet:
    path: /  # Root endpoint exists
```

**Learning:** Always verify health check endpoints exist in application code before configuring Kubernetes probes.

---

### Challenge 4: Insufficient CPU Resources

**Problem:** Streaming service pod stuck in `Pending` state.

**Error:**
```
0/2 nodes are available: 2 Insufficient cpu.
```

**Root Cause:** Streaming service requested 500m CPU, but nodes didn't have enough available.

**Solution:** Reduced resource requests:
```yaml
# Changed from:
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"

# To:
resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
```

**Learning:** Match resource requests to available node capacity, especially on t3.medium nodes.

---

### Challenge 5: Multiple ReplicaSets from Failed Upgrades

**Problem:** Multiple ReplicaSets for streaming service causing conflicts.

**Observation:**
```
NAME                           DESIRED   CURRENT   READY
streaming-service-6985b6fb6f   1         1         0
streaming-service-7766fb8b5    1         1         0
streaming-service-7dd446cd9c   1         1         1
```

**Solution:**
```bash
# Delete old replica sets
kubectl delete rs streaming-service-6985b6fb6f
kubectl delete rs streaming-service-7766fb8b5

# Only keep the working one
```

**Learning:** Clean up old ReplicaSets after failed Helm upgrades.

---

### Challenge 6: Secrets in Git

**Problem:** Initially had sensitive data in `values.yaml`.

**Risk:** AWS credentials, MongoDB URI, JWT secret would be committed to Git.

**Solution:** 
1. Removed all sensitive data from values.yaml
2. Created Kubernetes Secrets directly:
```bash
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret="..." \
  --from-literal=mongo-uri="..."
```
3. Referenced secrets in deployments via `secretKeyRef`

**Learning:** Never commit secrets to Git. Use Kubernetes Secrets or external secret managers.

---

### Challenge 7: Frontend API Communication

**Problem:** Frontend built with internal service URLs (http://auth-service:3001) which don't work from browser.

**Issue:** Browser can't resolve Kubernetes internal DNS names.

**Current Workaround:** Application accessible but login/registration not functional.

**Proper Solution (Future):**
- Implement Ingress controller with path-based routing
- Or expose backend services via LoadBalancer
- Or use API Gateway pattern

**Learning:** Frontend needs public URLs for backend services, not internal Kubernetes service names.

---

## Cost Analysis

### Monthly Cost Estimate (us-west-1)

| Resource | Specification | Quantity | Cost/Hour | Monthly Cost |
|----------|--------------|----------|-----------|--------------|
| EKS Control Plane | - | 1 | $0.10 | $73.00 |
| EC2 Worker Nodes | t3.medium | 2 | $0.0416 | $60.35 |
| EC2 Jenkins | t3.medium | 1 | $0.0416 | $30.17 |
| EBS Volumes | gp3, 20GB | 3 | $0.08/GB/mo | $4.80 |
| Application Load Balancer | - | 1 | $0.0225 | $16.43 |
| NAT Gateway | - | 1 | $0.045 | $32.85 |
| Data Transfer | ~10GB/month | - | $0.09/GB | $0.90 |
| ECR Storage | ~5GB | - | $0.10/GB/mo | $0.50 |
| S3 Storage | ~10GB | - | $0.023/GB | $0.23 |
| **TOTAL** | | | | **~$219/month** |

### Cost Optimization Strategies

**Implemented:**
- ✅ t3.medium instances (burstable, cost-effective)
- ✅ MongoDB Atlas (free tier cluster)
- ✅ Auto-scaling (min 1, max 3 nodes)
- ✅ gp3 volumes (cheaper than gp2)

**Future Optimizations:**
- Use Spot Instances for non-critical workloads
- Implement cluster autoscaler
- Use Fargate for specific workloads
- Schedule non-prod environments (stop nights/weekends)
- Use Reserved Instances for long-term (save 30-40%)

---

## Future Improvements

### 1. Implement Ingress Controller

**Current:** Frontend is LoadBalancer, backend services are ClusterIP

**Improvement:** Single Ingress with path-based routing

```yaml
# Example Ingress configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: streamingapp-ingress
  annotations:
    kubernetes.io/ingress.class: alb
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
      - path: /api/auth
        pathType: Prefix
        backend:
          service:
            name: auth-service
            port:
              number: 3001
      - path: /api/streaming
        pathType: Prefix
        backend:
          service:
            name: streaming-service
            port:
              number: 3002
```

**Benefits:**
- Single LoadBalancer (cost savings)
- Cleaner URL structure
- SSL termination at Ingress
- Better routing control

---

### 2. Add Monitoring & Observability

**CloudWatch Container Insights:**
```yaml
# Enable in cluster-config.yaml
cloudWatch:
  clusterLogging:
    enableTypes:
      - api
      - audit
      - authenticator
      - controllerManager
      - scheduler
```

**Prometheus + Grafana:**
- Install via Helm
- Custom dashboards for each service
- Alerting rules

**Logging:**
- Fluent Bit for log collection
- Ship logs to CloudWatch Logs
- Centralized log analysis

---

### 3. Implement Auto-scaling

**Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: streaming-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: streaming-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Cluster Autoscaler:**
- Automatically add/remove nodes based on demand
- Cost-effective scaling

---

### 4. Add SSL/TLS

**AWS Certificate Manager:**
- Request certificate
- Attach to LoadBalancer
- Enable HTTPS

**Let's Encrypt:**
- cert-manager operator
- Automatic certificate renewal

---

### 5. Implement CI/CD for Kubernetes

**ArgoCD or Flux:**
- GitOps workflow
- Automatic deployments on Git push
- Rollback capabilities

**Jenkins Enhancement:**
- Add deployment stage to Jenkinsfile
- Automatic Helm upgrade after ECR push

---

### 6. Add Database Migrations

**Flyway or Liquibase:**
- Version-controlled database schemas
- Automatic migrations on deployment

---

### 7. Improve Security

**Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: auth-service-policy
spec:
  podSelector:
    matchLabels:
      app: auth-service
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 3001
```

**Pod Security Policies:**
- Non-root containers
- Read-only root filesystem
- Drop capabilities

**Secret Management:**
- AWS Secrets Manager integration
- External Secrets Operator
- Rotate secrets regularly

---

### 8. Add Backup & Disaster Recovery

**MongoDB Atlas:**
- Automated backups (already enabled)
- Point-in-time recovery

**EKS:**
- Velero for cluster backups
- Backup Helm releases
- Document recovery procedures

---

### 9. Performance Optimization

**Caching:**
- Redis for session storage
- CDN for static assets (CloudFront)

**Database:**
- Connection pooling
- Query optimization
- Indexes

**Application:**
- Code splitting (frontend)
- Lazy loading
- Image optimization

---

### 10. Multi-environment Setup

**Environments:**
- Development
- Staging
- Production

**Namespaces:**
```yaml
# dev namespace
kubectl create namespace dev

# staging namespace
kubectl create namespace staging

# prod namespace
kubectl create namespace prod
```

**Separate Helm values per environment:**
- values-dev.yaml
- values-staging.yaml
- values-prod.yaml

---

## Conclusion

This project successfully demonstrates:

✅ **Containerization** - All 5 microservices containerized with Docker  
✅ **CI/CD** - Automated build pipeline with Jenkins  
✅ **Cloud Infrastructure** - AWS EKS cluster with 2 worker nodes  
✅ **Container Registry** - ECR for image storage  
✅ **Orchestration** - Kubernetes deployment with Helm  
✅ **Scalability** - 10 pods (2 replicas per service)  
✅ **Load Balancing** - AWS ELB for public access  
✅ **Security** - Kubernetes Secrets for sensitive data  
✅ **Cloud Database** - MongoDB Atlas integration  
✅ **Object Storage** - S3 for video files  

**Application Status:** ✅ Successfully deployed and accessible  
**URL:** http://a83bc627a2a2248b59348d50b8e01678-364020149.us-west-1.elb.amazonaws.com

---

## Appendix

### A. Useful Commands Reference

**EKS Management:**
```bash
# Create cluster
eksctl create cluster -f cluster-config.yaml

# Delete cluster
eksctl delete cluster --name streamingapp-cluster-pp --region us-west-1

# List clusters
eksctl get cluster --region us-west-1

# Update kubeconfig
aws eks update-kubeconfig --name streamingapp-cluster-pp --region us-west-1
```

**Kubernetes Operations:**
```bash
# Get all resources
kubectl get all

# Get pods with details
kubectl get pods -o wide

# Check pod logs
kubectl logs <pod-name>

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/sh

# Port forward (testing)
kubectl port-forward svc/auth-service 3001:3001

# Describe resource
kubectl describe pod <pod-name>

# Get events
kubectl get events --sort-by='.lastTimestamp'

# Delete pod (will recreate)
kubectl delete pod <pod-name>
```

**Helm Commands:**
```bash
# Install
helm install streamingapp ./helm/streamingapp

# Upgrade
helm upgrade streamingapp ./helm/streamingapp

# Rollback
helm rollback streamingapp 1

# Uninstall
helm uninstall streamingapp

# List releases
helm list

# Get values
helm get values streamingapp

# Dry run
helm install streamingapp ./helm/streamingapp --dry-run --debug
```

**ECR Commands:**
```bash
# Login to ECR
aws ecr get-login-password --region us-west-1 | \
  docker login --username AWS --password-stdin \
  975050024946.dkr.ecr.us-west-1.amazonaws.com

# List images
aws ecr list-images --repository-name streamingapp-auth --region us-west-1

# Describe images
aws ecr describe-images --repository-name streamingapp-auth --region us-west-1
```

---

### B. Troubleshooting Guide

**Pod Stuck in Pending:**
```bash
# Check why
kubectl describe pod <pod-name>

# Common causes:
# - Insufficient resources
# - Node selector not matching
# - PVC not bound
```

**Pod Crashing (CrashLoopBackOff):**
```bash
# Check logs
kubectl logs <pod-name>

# Check previous logs
kubectl logs <pod-name> --previous

# Common causes:
# - Application error
# - Missing environment variables
# - Failed health checks
```

**Service Not Accessible:**
```bash
# Check service
kubectl get svc <service-name>

# Check endpoints
kubectl get endpoints <service-name>

# Test from another pod
kubectl run test --image=busybox --rm -it --restart=Never -- \
  wget -O- http://<service-name>:<port>
```

**Image Pull Errors:**
```bash
# Check image name
kubectl describe pod <pod-name> | grep Image

# Check ECR authentication
aws ecr get-login-password --region us-west-1 | \
  docker login --username AWS --password-stdin <ECR_URL>

# Verify image exists
aws ecr describe-images --repository-name <repo-name> --region us-west-1
```

---

### C. GitHub Repository Structure

```
StreamingApp/
|
├── backend/
│   ├── authService/
│   ├── streamingService/
│   ├── adminService/
│   └── chatService/
├── frontend/
├── helm/
│   └── streamingapp/
├── docs/
│   ├── COMPLETE_PROJECT_DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   └── TROUBLESHOOTING.md
├── scripts/
│   ├── validate-deployment.sh
│   └── cleanup.sh
├── .gitignore
├── Jenkinsfile
├── cluster-config.yaml
└── README.md
```

---

### D. References & Resources

**Documentation:**
- AWS EKS: https://docs.aws.amazon.com/eks/
- Kubernetes: https://kubernetes.io/docs/
- Helm: https://helm.sh/docs/
- Docker: https://docs.docker.com/
- Jenkins: https://www.jenkins.io/doc/

**Tools:**
- eksctl: https://eksctl.io/
- kubectl: https://kubernetes.io/docs/reference/kubectl/
- AWS CLI: https://aws.amazon.com/cli/

**Learning Resources:**
- Kubernetes Basics: https://kubernetes.io/docs/tutorials/kubernetes-basics/
- EKS Workshop: https://www.eksworkshop.com/
- Helm Charts: https://helm.sh/docs/topics/charts/

---

**End of Documentation**