# StreamingApp - Validation & Testing Checklist

---

## Quick Validation Commands

### 1. Overall System Health

```bash
# Check all resources at once
kubectl get all

# Expected: 
# - 10 pods (all Running or 9 Running if streaming issue persists)
# - 5 deployments (all Ready)
# - 5 services
```

---

### 2. Pod Status Validation

```bash
kubectl get pods
```

**Expected Output:**
```
NAME                                 READY   STATUS    RESTARTS   AGE
admin-service-xxxxx-xxxxx            1/1     Running   0          Xh
admin-service-xxxxx-xxxxx            1/1     Running   0          Xh
auth-service-xxxxx-xxxxx             1/1     Running   0          Xh
auth-service-xxxxx-xxxxx             1/1     Running   0          Xh
chat-service-xxxxx-xxxxx             1/1     Running   0          Xh
chat-service-xxxxx-xxxxx             1/1     Running   0          Xh
frontend-xxxxx-xxxxx                 1/1     Running   0          Xh
frontend-xxxxx-xxxxx                 1/1     Running   0          Xh
streaming-service-xxxxx-xxxxx        1/1     Running   0          Xh
streaming-service-xxxxx-xxxxx        1/1     Running   0          Xh
```

**✅ Pass Criteria:**
- All pods show `1/1` in READY column
- All pods show `Running` in STATUS column
- RESTARTS should be low (< 5)

**❌ Fail Indicators:**
- `0/1` Ready
- `Pending`, `CrashLoopBackOff`, `Error`, `ImagePullBackOff`
- High restart count (> 10)

---

### 3. Service Validation

```bash
kubectl get svc
```

**Expected Output:**
```
NAME                TYPE           CLUSTER-IP       EXTERNAL-IP                              PORT(S)
admin-service       ClusterIP      10.100.x.x       <none>                                   3003/TCP
auth-service        ClusterIP      10.100.x.x       <none>                                   3001/TCP
chat-service        ClusterIP      10.100.x.x       <none>                                   3004/TCP
frontend            LoadBalancer   10.100.x.x       aXXXXXXX.us-west-1.elb.amazonaws.com    80:XXXXX/TCP
streaming-service   ClusterIP      10.100.x.x       <none>                                   3002/TCP
```

**✅ Pass Criteria:**
- 4 backend services with type `ClusterIP`
- 1 frontend service with type `LoadBalancer`
- Frontend has EXTERNAL-IP (ELB URL)

---

### 4. Deployment Status

```bash
kubectl get deployments
```

**Expected Output:**
```
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
admin-service       2/2     2            2           Xh
auth-service        2/2     2            2           Xh
chat-service        2/2     2            2           Xh
frontend            2/2     2            2           Xh
streaming-service   2/2     2            2           Xh
```

**✅ Pass Criteria:**
- All deployments show `2/2` in READY column
- UP-TO-DATE matches desired count
- AVAILABLE matches desired count

---

## Frontend Validation

### Test 1: LoadBalancer Accessibility

```bash
# Get LoadBalancer URL
kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

**Save this URL for browser testing!**

---

### Test 2: Health Endpoint

```bash
# Get LB URL
LB_URL=$(kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health endpoint
curl http://$LB_URL/health
```

**Expected Response:** `healthy`

**✅ Pass:** Returns "healthy" with 200 status  
**❌ Fail:** Timeout, 404, or error response

---

### Test 3: Homepage Loading

**Open in browser:**
```
http://<LOAD_BALANCER_URL>/
```

**✅ Pass Criteria:**
- Page loads within 5 seconds
- No console errors (F12)
- Images load
- CSS styles applied
- Navigation works

**❌ Fail Indicators:**
- Blank page
- 404 error
- Network errors in console
- Missing styles

---

### Test 4: Static Assets

**Check in browser console (F12 → Network tab):**
- CSS files load (200 status)
- JavaScript files load (200 status)
- Images load (200 status)

**✅ Pass:** All assets return 200  
**❌ Fail:** 404 or network errors

---

### Test 5: React Router

**Test navigation:**
1. Click on different menu items
2. Try direct URL access to routes
3. Check browser back button

**✅ Pass:** All routes load correctly, no 404  
**❌ Fail:** 404 on route navigation

---

## Backend Service Validation

### Test 1: Auth Service (Port 3001)

#### Internal Connectivity Test:
```bash
kubectl run test-auth --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://auth-service:3001/health
```

**Expected:** JSON response or "OK"  
**✅ Pass:** Returns response  
**❌ Fail:** Connection refused or timeout

---

#### MongoDB Connection Test:
```bash
# Check auth service logs
AUTH_POD=$(kubectl get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl logs $AUTH_POD | grep -i mongo
```

**Expected Output:**
```
Connecting to MongoDB at: mongodb+srv://dbXUser:...
DB connection established
MongoDB Connected Successfully
```

**✅ Pass:** See "MongoDB Connected Successfully"  
**❌ Fail:** Connection errors, authentication failures

---

#### Registration Endpoint Test (if accessible):
```bash
# If you have direct access to auth service
curl -X POST http://auth-service:3001/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "name": "Test User"
  }'
```

**Expected:** User created response or user exists error

---

### Test 2: Streaming Service (Port 3002)

#### Service Connectivity:
```bash
kubectl run test-streaming --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://streaming-service:3002/
```

**Expected:** HTML response or JSON  
**✅ Pass:** Returns response  
**❌ Fail:** Connection refused

---

#### Check Logs:
```bash
STREAMING_POD=$(kubectl get pods -l app=streaming-service -o jsonpath='{.items[0].metadata.name}')
kubectl logs $STREAMING_POD | tail -20
```

**Look for:**
- "Streaming service running on port 3002"
- "MongoDB connection established"
- No error messages

---

### Test 3: Admin Service (Port 3003)

```bash
kubectl run test-admin --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://admin-service:3003/
```

**Expected:** Response from service  
**✅ Pass:** Connection successful  
**❌ Fail:** Connection refused

---

### Test 4: Chat Service (Port 3004)

```bash
kubectl run test-chat --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://chat-service:3004/
```

**Expected:** Response from service  
**✅ Pass:** Connection successful  
**❌ Fail:** Connection refused

---

## Database Validation

### Test 1: MongoDB Atlas Connection

```bash
# Check all service logs for MongoDB connection
kubectl logs -l app=auth-service | grep -i "mongodb connected"
kubectl logs -l app=streaming-service | grep -i "mongodb"
kubectl logs -l app=admin-service | grep -i "mongodb"
kubectl logs -l app=chat-service | grep -i "mongodb"
```

**✅ Pass:** All services show successful MongoDB connection  
**❌ Fail:** Authentication errors, connection timeouts

---

### Test 2: Database Operations

**If auth service is working, try:**
1. Register a user (via frontend or API)
2. Check if user appears in MongoDB Atlas
3. Try to login with created user

---

## Configuration Validation

### Test 1: Secrets Exist

```bash
kubectl get secrets
```

**Expected:**
```
NAME          TYPE     DATA   AGE
app-secrets   Opaque   2      Xh
aws-secrets   Opaque   2      Xh
```

**✅ Pass:** Both secrets exist with correct data count  
**❌ Fail:** Secrets missing

---

### Test 2: ConfigMap Exists

```bash
kubectl get configmap app-config
```

**Expected:** ConfigMap exists

**View contents:**
```bash
kubectl describe configmap app-config
```

**Should contain:**
- aws-region: us-west-1
- s3-bucket: streamingapp-videos-975050024946
- client-urls: http://localhost:3000

---

### Test 3: Environment Variables in Pods

```bash
# Pick any backend pod
POD_NAME=$(kubectl get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')

# Check environment variables
kubectl exec $POD_NAME -- env | grep -E "MONGO_URI|JWT_SECRET|AWS"
```

**Expected:**
- MONGO_URI should be set
- JWT_SECRET should be set
- AWS_ACCESS_KEY_ID should be set
- AWS_SECRET_ACCESS_KEY should be set
- AWS_REGION should be set
- AWS_S3_BUCKET should be set

**✅ Pass:** All required env vars present  
**❌ Fail:** Missing variables

---

## Resource Validation

### Test 1: CPU and Memory Usage

```bash
# Node resources
kubectl top nodes

# Pod resources
kubectl top pods
```

**✅ Pass:**
- Nodes under 80% CPU usage
- Nodes under 80% memory usage
- No pods consuming excessive resources

**❌ Fail:**
- Nodes over 90% CPU
- Pods being OOMKilled
- High CPU throttling

---

### Test 2: Resource Limits Applied

```bash
kubectl describe pod <any-pod-name> | grep -A 10 Limits
```

**Expected:** CPU and memory limits defined

---

## Network Validation

### Test 1: Pod-to-Pod Communication

```bash
# From frontend to auth service
FRONTEND_POD=$(kubectl get pods -l app=frontend -o jsonpath='{.items[0].metadata.name}')
kubectl exec $FRONTEND_POD -- wget -qO- http://auth-service:3001/health
```

**✅ Pass:** Successful response  
**❌ Fail:** Connection timeout or refused

---

### Test 2: Service DNS Resolution

```bash
# Test DNS from any pod
kubectl run test-dns --image=busybox --rm -it --restart=Never -- \
  nslookup auth-service
```

**Expected:** IP address resolved

---

### Test 3: External Connectivity (from pods)

```bash
# Test internet access from pod
kubectl run test-internet --image=busybox --rm -it --restart=Never -- \
  wget -qO- https://www.google.com
```

**✅ Pass:** Successfully reaches internet  
**❌ Fail:** DNS resolution failure or timeout

---

## Persistence Validation

### Test 1: Pod Restart Resilience

```bash
# Delete a pod (it will recreate)
POD_NAME=$(kubectl get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $POD_NAME

# Wait 30 seconds
sleep 30

# Check if new pod is running
kubectl get pods -l app=auth-service
```

**✅ Pass:** New pod comes up in Running state  
**❌ Fail:** Pod stuck in Pending or CrashLoopBackOff

---

### Test 2: Data Persistence

**Create test data:**
1. Register a user via frontend
2. Delete auth service pods
3. Wait for pods to recreate
4. Try to login with same user

**✅ Pass:** Can login (data persisted in MongoDB Atlas)  
**❌ Fail:** User not found

---

## Security Validation

### Test 1: Secrets Not Exposed

```bash
# Secrets should be base64 encoded, not plaintext
kubectl get secret app-secrets -o yaml | grep -A 5 data
```

**✅ Pass:** Values are base64 encoded  
**❌ Fail:** Plaintext secrets visible

---

### Test 2: Non-Root Containers (Optional)

```bash
kubectl exec <pod-name> -- id
```

**Best Practice:** Should not be uid=0 (root)

---

## Performance Validation

### Test 1: Response Time

```bash
# Test frontend response time
time curl -o /dev/null -s -w '%{time_total}\n' http://<LB_URL>/
```

**✅ Pass:** < 2 seconds  
**⚠️ Warning:** 2-5 seconds  
**❌ Fail:** > 5 seconds

---

### Test 2: Concurrent Requests

**Use Apache Bench (if available):**
```bash
ab -n 100 -c 10 http://<LB_URL>/
```

**Check:**
- No failed requests
- Average response time < 3 seconds

---

## Complete Validation Script

Save this as `complete-validation.sh`:

```bash
#!/bin/bash

echo "=========================================="
echo "   StreamingApp Validation Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

# Function to check and report
check_test() {
    local test_name="$1"
    local test_command="$2"
    local expected="$3"
    
    echo -n "Testing: $test_name ... "
    
    result=$(eval "$test_command" 2>&1)
    
    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((pass_count++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        ((fail_count++))
    fi
}

echo "1. Checking Cluster Status..."
check_test "Cluster Info" "kubectl cluster-info" "Kubernetes control plane"

echo ""
echo "2. Checking Nodes..."
check_test "Nodes Ready" "kubectl get nodes | grep -c Ready" "2"

echo ""
echo "3. Checking Pods..."
check_test "Auth Pods Running" "kubectl get pods -l app=auth-service | grep -c Running" "2"
check_test "Streaming Pods" "kubectl get pods -l app=streaming-service | grep -c Running" "1"
check_test "Admin Pods Running" "kubectl get pods -l app=admin-service | grep -c Running" "2"
check_test "Chat Pods Running" "kubectl get pods -l app=chat-service | grep -c Running" "2"
check_test "Frontend Pods Running" "kubectl get pods -l app=frontend | grep -c Running" "2"

echo ""
echo "4. Checking Services..."
check_test "Services Count" "kubectl get svc | grep -c service" "5"
check_test "LoadBalancer External IP" "kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'" "elb.amazonaws.com"

echo ""
echo "5. Checking Secrets..."
check_test "App Secrets Exist" "kubectl get secret app-secrets" "app-secrets"
check_test "AWS Secrets Exist" "kubectl get secret aws-secrets" "aws-secrets"

echo ""
echo "6. Checking ConfigMap..."
check_test "ConfigMap Exists" "kubectl get configmap app-config" "app-config"

echo ""
echo "7. Checking MongoDB Connection..."
AUTH_POD=$(kubectl get pods -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
check_test "Auth MongoDB Connected" "kubectl logs $AUTH_POD | grep -i 'mongodb connected'" "Connected"

echo ""
echo "8. Testing Frontend Health..."
LB_URL=$(kubectl get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
check_test "Frontend Health Endpoint" "curl -s http://$LB_URL/health" "healthy"

echo ""
echo "=========================================="
echo "   Validation Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $pass_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
total=$((pass_count + fail_count))
percentage=$((pass_count * 100 / total))
echo "Success Rate: $percentage%"

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi
```

**Run:**
```bash
chmod +x complete-validation.sh
./complete-validation.sh
```

---

## Manual Browser Testing Checklist

### Frontend Tests

- [ ] Homepage loads without errors
- [ ] Navigation menu works
- [ ] All images load
- [ ] CSS styles applied correctly
- [ ] No console errors (F12)
- [ ] Can navigate to different routes
- [ ] Browser back button works
- [ ] Page is responsive on mobile

### Authentication Tests (if working)

- [ ] Registration form appears
- [ ] Can submit registration
- [ ] Login form appears
- [ ] Can attempt login
- [ ] Error messages display correctly

### Video Browsing Tests (if working)

- [ ] Video list/catalog displays
- [ ] Can click on videos
- [ ] Video details page loads

---

## Quick Health Check (30 seconds)

**Run these 3 commands:**

```bash
# 1. All pods running?
kubectl get pods | grep -v Running

# 2. LoadBalancer ready?
kubectl get svc frontend | grep elb

# 3. MongoDB connected?
kubectl logs -l app=auth-service | grep "MongoDB Connected"
```

**If all three return expected results, deployment is healthy!**

---

## Troubleshooting Quick Reference

### If Pods are Pending:
```bash
kubectl describe pod <pod-name> | grep Events -A 10
```
Look for: Insufficient CPU, Insufficient memory

---

### If Pods are CrashLoopBackOff:
```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous
```
Look for: Application errors, missing env vars

---

### If Services Not Responding:
```bash
kubectl get endpoints <service-name>
```
Check if endpoints exist (should match pod IPs)

---

### If LoadBalancer Stuck in Pending:
```bash
kubectl describe svc frontend | grep Events -A 10
```
Wait 2-3 minutes for AWS to provision

---

## Success Criteria Summary

**Minimum for PASS:**
- ✅ 9/10 pods Running (streaming may have issues)
- ✅ All 5 services exist
- ✅ Frontend LoadBalancer has External IP
- ✅ Frontend accessible in browser
- ✅ Auth service connected to MongoDB
- ✅ No ImagePullBackOff errors

**Ideal State:**
- ✅ 10/10 pods Running
- ✅ All health checks passing
- ✅ Login/registration working
- ✅ Zero restarts on pods
- ✅ All services responding

---

**End of Validation Checklist**

*Use this document to systematically verify your deployment!*
