# StreamingApp - Quick Reference Commands

**Quick access to all important commands for StreamingApp deployment**

---

## 🚀 Deployment Commands

### Initial Setup
```bash
# Configure AWS CLI
aws configure

# Verify AWS identity
aws sts get-caller-identity
```

---

### EKS Cluster Management
```bash
# Create cluster
eksctl create cluster -f cluster-config.yaml

# Get clusters
eksctl get cluster --region us-west-1

# Update kubeconfig
aws eks update-kubeconfig --name streamingapp-cluster-pp --region us-west-1

# Delete cluster (⚠️ DESTRUCTIVE)
eksctl delete cluster --name streamingapp-cluster-pp --region us-west-1
```

---

### Helm Operations
```bash
# Install application
helm install streamingapp ./helm/streamingapp

# Upgrade application
helm upgrade streamingapp ./helm/streamingapp

# Rollback to previous version
helm rollback streamingapp

# Uninstall application
helm uninstall streamingapp

# List all releases
helm list

# Dry run (test without deploying)
helm install streamingapp ./helm/streamingapp --dry-run --debug
```

---

## 📊 Monitoring Commands

### Quick Status Check
```bash
# Everything at once
kubectl get all

# Just pods
kubectl get pods

# Just services
kubectl get svc

# Just deployments
kubectl get deployments

# With more details
kubectl get pods -o wide
```

---

### Detailed Information
```bash
# Describe a resource
kubectl describe pod <pod-name>
kubectl describe svc <service-name>
kubectl describe deployment <deployment-name>

# Get YAML of resource
kubectl get pod <pod-name> -o yaml
kubectl get svc <service-name> -o yaml
```

---

### Logs
```bash
# View logs
kubectl logs <pod-name>

# Follow logs (tail -f style)
kubectl logs -f <pod-name>

# Last 50 lines
kubectl logs <pod-name> --tail=50

# Previous container logs (if crashed)
kubectl logs <pod-name> --previous

# All pods with specific label
kubectl logs -l app=auth-service
```

---

### Resource Usage
```bash
# Node resource usage
kubectl top nodes

# Pod resource usage  
kubectl top pods

# Specific pod details
kubectl top pod <pod-name>
```

---

## 🔍 Troubleshooting Commands

### Get Events
```bash
# All events (sorted by time)
kubectl get events --sort-by='.lastTimestamp'

# Recent events only
kubectl get events --sort-by='.lastTimestamp' | tail -20

# Events for specific resource
kubectl describe pod <pod-name> | grep Events -A 20
```

---

### Pod Debugging
```bash
# Execute command in pod
kubectl exec -it <pod-name> -- /bin/sh

# Run command without shell
kubectl exec <pod-name> -- env

# Copy files from pod
kubectl cp <pod-name>:/path/to/file ./local-file

# Copy files to pod
kubectl cp ./local-file <pod-name>:/path/to/file
```

---

### Service Testing
```bash
# Test service from temporary pod
kubectl run test --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://<service-name>:<port>

# Port forward to local machine
kubectl port-forward svc/<service-name> 8080:3001

# Then access at: http://localhost:8080
```

---

### Network Testing
```bash
# DNS resolution test
kubectl run test-dns --image=busybox --rm -it --restart=Never -- \
  nslookup <service-name>

# Connectivity test
kubectl run test-curl --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://<service-name>:<port>
```

---

## 🔧 Management Commands

### Scale Deployments
```bash
# Scale up
kubectl scale deployment <deployment-name> --replicas=3

# Scale down
kubectl scale deployment <deployment-name> --replicas=1

# Auto-scale
kubectl autoscale deployment <deployment-name> --min=2 --max=10 --cpu-percent=70
```

---

### Update Deployments
```bash
# Update image
kubectl set image deployment/<deployment-name> \
  <container-name>=<new-image>:<tag>

# Restart deployment (rolling restart)
kubectl rollout restart deployment <deployment-name>

# Check rollout status
kubectl rollout status deployment <deployment-name>

# Rollout history
kubectl rollout history deployment <deployment-name>

# Rollback
kubectl rollout undo deployment <deployment-name>
```

---

### Delete Resources
```bash
# Delete pod (will recreate via deployment)
kubectl delete pod <pod-name>

# Delete deployment (and all pods)
kubectl delete deployment <deployment-name>

# Delete service
kubectl delete svc <service-name>

# Delete everything with label
kubectl delete all -l app=<app-name>

# Delete by file
kubectl delete -f deployment.yaml
```

---

## 🔐 Secrets & ConfigMaps

### Create Secrets
```bash
# From literals
kubectl create secret generic <secret-name> \
  --from-literal=key1=value1 \
  --from-literal=key2=value2

# From file
kubectl create secret generic <secret-name> \
  --from-file=ssh-privatekey=~/.ssh/id_rsa

# Docker registry secret
kubectl create secret docker-registry <secret-name> \
  --docker-server=<server> \
  --docker-username=<username> \
  --docker-password=<password>
```

---

### View Secrets
```bash
# List secrets
kubectl get secrets

# Describe secret (shows keys, not values)
kubectl describe secret <secret-name>

# Get secret YAML (base64 encoded values)
kubectl get secret <secret-name> -o yaml

# Decode specific key
kubectl get secret <secret-name> -o jsonpath='{.data.key}' | base64 -d
```

---

### Create ConfigMaps
```bash
# From literals
kubectl create configmap <cm-name> \
  --from-literal=key1=value1 \
  --from-literal=key2=value2

# From file
kubectl create configmap <cm-name> \
  --from-file=config.properties

# From directory
kubectl create configmap <cm-name> \
  --from-file=./config-dir/
```

---

### View ConfigMaps
```bash
# List configmaps
kubectl get configmap

# Describe configmap
kubectl describe configmap <cm-name>

# Get configmap YAML
kubectl get configmap <cm-name> -o yaml
```

---

## 📦 ECR Commands

### Login to ECR
```bash
aws ecr get-login-password --region us-west-1 | \
  docker login --username AWS --password-stdin \
  975050024946.dkr.ecr.us-west-1.amazonaws.com
```

---

### Manage Repositories
```bash
# List repositories
aws ecr describe-repositories --region us-west-1

# Create repository
aws ecr create-repository \
  --repository-name <repo-name> \
  --region us-west-1

# Delete repository
aws ecr delete-repository \
  --repository-name <repo-name> \
  --region us-west-1 \
  --force
```

---

### Manage Images
```bash
# List images in repository
aws ecr list-images \
  --repository-name <repo-name> \
  --region us-west-1

# Describe images (with details)
aws ecr describe-images \
  --repository-name <repo-name> \
  --region us-west-1

# Delete image
aws ecr batch-delete-image \
  --repository-name <repo-name> \
  --image-ids imageTag=<tag> \
  --region us-west-1
```

---

## 🎯 Application-Specific Commands

### Get LoadBalancer URL
```bash
# Get frontend LoadBalancer URL
kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Or more detailed
kubectl get svc frontend
```

---

### Check Service Health
```bash
# Get LoadBalancer URL
LB_URL=$(kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test frontend health
curl http://$LB_URL/health

# Test from within cluster
kubectl run test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://auth-service:3001/health
```

---

### Check MongoDB Connection
```bash
# Auth service
AUTH_POD=$(kubectl get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl logs $AUTH_POD | grep -i mongo

# All services
kubectl logs -l app=auth-service | grep "MongoDB Connected"
kubectl logs -l app=streaming-service | grep "MongoDB"
kubectl logs -l app=admin-service | grep "MongoDB"
kubectl logs -l app=chat-service | grep "MongoDB"
```

---

### Check Environment Variables
```bash
# Get pod name
POD=$(kubectl get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')

# Check env vars
kubectl exec $POD -- env | grep MONGO
kubectl exec $POD -- env | grep AWS
kubectl exec $POD -- env | grep JWT
```

---

## 📈 Useful One-Liners

### Get all pod IPs
```bash
kubectl get pods -o wide | awk '{print $1, $6}'
```

---

### Get all container images
```bash
kubectl get pods -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n'
```

---

### Count running pods
```bash
kubectl get pods | grep Running | wc -l
```

---

### Get pods not running
```bash
kubectl get pods | grep -v Running
```

---

### Get pods with high restarts
```bash
kubectl get pods | awk '$4 > 5'
```

---

### Watch pod status (auto-refresh)
```bash
watch kubectl get pods
```

---

### Get all services with external IPs
```bash
kubectl get svc | grep LoadBalancer
```

---

### Get resource requests/limits
```bash
kubectl describe nodes | grep -A 5 "Allocated resources"
```

---

### Force delete stuck pod
```bash
kubectl delete pod <pod-name> --grace-period=0 --force
```

---

## 🔄 CI/CD Commands

### Jenkins
```bash
# SSH to Jenkins
ssh -i jenkins-key.pem ubuntu@<JENKINS_IP>

# Jenkins logs
sudo journalctl -u jenkins -f

# Restart Jenkins
sudo systemctl restart jenkins

# Jenkins initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

---

### Docker on Jenkins
```bash
# Login to Jenkins server
ssh -i jenkins-key.pem ubuntu@<JENKINS_IP>

# Switch to jenkins user
sudo su - jenkins -s /bin/bash

# Test docker
docker ps

# Test AWS CLI
aws sts get-caller-identity
```

---

## 💾 Backup & Export

### Export Resources
```bash
# Export deployment YAML
kubectl get deployment <name> -o yaml > deployment-backup.yaml

# Export all resources
kubectl get all -o yaml > all-resources-backup.yaml

# Export secrets (⚠️ contains sensitive data)
kubectl get secrets -o yaml > secrets-backup.yaml
```

---

### Helm Values
```bash
# Export current values
helm get values streamingapp > current-values.yaml

# Export all values (including defaults)
helm get values streamingapp --all > all-values.yaml
```

---

## 🧹 Cleanup Commands

### Clean up Failed Pods
```bash
# Delete all failed pods
kubectl delete pods --field-selector=status.phase=Failed

# Delete all evicted pods
kubectl get pods | grep Evicted | awk '{print $1}' | xargs kubectl delete pod
```

---

### Clean up Old ReplicaSets
```bash
# List old replica sets
kubectl get rs

# Delete specific replica set
kubectl delete rs <rs-name>

# Delete all replica sets with 0 desired
kubectl get rs | awk '$2 == 0 {print $1}' | xargs kubectl delete rs
```

---

### Complete Cleanup (⚠️ DESTRUCTIVE)
```bash
# Uninstall helm release
helm uninstall streamingapp

# Delete all resources
kubectl delete all --all

# Delete secrets
kubectl delete secrets app-secrets aws-secrets

# Delete configmap
kubectl delete configmap app-config

# Delete cluster
eksctl delete cluster --name streamingapp-cluster-pp --region us-west-1
```

---

## 🎓 Learning Commands

### Explain Resources
```bash
# Explain pod
kubectl explain pod

# Explain specific field
kubectl explain pod.spec.containers

# All fields
kubectl explain pod --recursive
```

---

### API Resources
```bash
# List all API resources
kubectl api-resources

# List with short names
kubectl api-resources -o wide

# List API versions
kubectl api-versions
```

---

## 📱 Quick Access URLs

### Application
```bash
# Frontend (get URL)
echo "http://$(kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"

# Health check
echo "http://$(kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')/health"
```

---

### AWS Console
- EKS Clusters: https://us-west-1.console.aws.amazon.com/eks/home?region=us-west-1#/clusters
- ECR Repositories: https://us-west-1.console.aws.amazon.com/ecr/repositories?region=us-west-1
- EC2 Instances: https://us-west-1.console.aws.amazon.com/ec2/v2/home?region=us-west-1#Instances:
- S3 Buckets: https://s3.console.aws.amazon.com/s3/buckets?region=us-west-1

---

## 🆘 Emergency Commands

### Cluster Not Responding
```bash
# Update kubeconfig
aws eks update-kubeconfig --name streamingapp-cluster-pp --region us-west-1

# Check kubectl config
kubectl config view

# Switch context
kubectl config use-context <context-name>
```

---

### Application Down
```bash
# Restart all deployments
kubectl rollout restart deployment --all

# Scale down and up
kubectl scale deployment --all --replicas=0
sleep 30
kubectl scale deployment --all --replicas=2
```

---

### Out of Resources
```bash
# Check node resources
kubectl describe nodes | grep -A 5 Allocated

# Check which pods are using most
kubectl top pods --sort-by=memory
kubectl top pods --sort-by=cpu

# Delete resource-heavy pods
kubectl delete pod <pod-name>
```

---

**End of Quick Reference**

*Bookmark this page for quick access to common commands!*

**Actual LoadBalancer URL for this deployment:**
```
http://a83bc627a2a2248b59348d50b8e01678-364020149.us-west-1.elb.amazonaws.com
```
