echo "=== Creating StreamingApp PP ECR repositories ==="

for repo in \
  streamingapp-auth-pp \
  streamingapp-streaming-pp \
  streamingapp-admin-pp \
  streamingapp-chat-pp \
  streamingapp-frontend-pp \
  streamingapp-healing-controller-pp; do

  aws ecr create-repository \
    --repository-name $repo \
    --region us-west-1 \
    --image-scanning-configuration scanOnPush=true \
    2>/dev/null \
    && echo "✅ Created: $repo" \
    || echo "⚠️  Already exists: $repo"
done

echo ""
echo "=== Verifying all 6 PP repos ==="
aws ecr describe-repositories \
  --region us-west-1 \
  --query "repositories[?contains(repositoryName,'streamingapp') && contains(repositoryName,'-pp')].{Name:repositoryName,URI:repositoryUri}" \
  --output table
