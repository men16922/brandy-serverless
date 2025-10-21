#!/bin/bash
set -e

REGION="us-west-2"
CLUSTER_NAME="ai-branding-chatbot-cluster"
SERVICE_NAME="ai-branding-chatbot-streamlit"
TASK_FAMILY="ai-branding-chatbot-streamlit"
ECR_REPO="908601828278.dkr.ecr.us-west-2.amazonaws.com/ai-branding-chatbot-streamlit"
API_URL="https://67y0voa4yd.execute-api.us-west-2.amazonaws.com/dev"

echo "🚀 Deploying Streamlit to ECS Fargate..."

# 1. Build and push Docker image for linux/amd64
echo "📦 Building Docker image for linux/amd64..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

docker buildx build --platform linux/amd64 \
  -t $ECR_REPO:latest \
  --push \
  -f Dockerfile .

echo "✅ Image pushed: $ECR_REPO:latest"

# 2. Create ECS cluster if not exists
echo "🔧 Creating ECS cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION 2>/dev/null || echo "Cluster already exists"

# 3. Create CloudWatch log group
echo "📝 Creating CloudWatch log group..."
aws logs create-log-group --log-group-name /ecs/$TASK_FAMILY --region $REGION 2>/dev/null || echo "Log group already exists"

# 4. Get default VPC and subnets
echo "🌐 Getting VPC configuration..."
VPC_ID=$(aws ec2 describe-vpcs --region $REGION --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text | tr '\t' ',')

echo "VPC: $VPC_ID"
echo "Subnets: $SUBNET_IDS"

# 5. Create security group for ALB
echo "🔒 Creating security group for ALB..."
ALB_SG_ID=$(aws ec2 create-security-group \
  --group-name ai-branding-chatbot-alb-sg \
  --description "Security group for Streamlit ALB" \
  --vpc-id $VPC_ID \
  --region $REGION \
  --query 'GroupId' \
  --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=ai-branding-chatbot-alb-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text)

# Allow HTTP from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region $REGION 2>/dev/null || echo "Ingress rule already exists"

echo "ALB Security Group: $ALB_SG_ID"

# 6. Create security group for ECS tasks
echo "🔒 Creating security group for ECS tasks..."
ECS_SG_ID=$(aws ec2 create-security-group \
  --group-name ai-branding-chatbot-ecs-sg \
  --description "Security group for Streamlit ECS tasks" \
  --vpc-id $VPC_ID \
  --region $REGION \
  --query 'GroupId' \
  --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=ai-branding-chatbot-ecs-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text)

# Allow traffic from ALB
aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG_ID \
  --protocol tcp \
  --port 8501 \
  --source-group $ALB_SG_ID \
  --region $REGION 2>/dev/null || echo "Ingress rule already exists"

echo "ECS Security Group: $ECS_SG_ID"

# 7. Create Application Load Balancer
echo "⚖️  Creating Application Load Balancer..."
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ai-branding-chatbot-alb \
  --subnets $(echo $SUBNET_IDS | tr ',' ' ') \
  --security-groups $ALB_SG_ID \
  --region $REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text 2>/dev/null || \
  aws elbv2 describe-load-balancers \
    --region $REGION \
    --names ai-branding-chatbot-alb \
    --query "LoadBalancers[0].LoadBalancerArn" \
    --output text)

ALB_DNS=$(aws elbv2 describe-load-balancers \
  --region $REGION \
  --load-balancer-arns $ALB_ARN \
  --query "LoadBalancers[0].DNSName" \
  --output text)

echo "ALB ARN: $ALB_ARN"
echo "ALB DNS: $ALB_DNS"

# 8. Create target group
echo "🎯 Creating target group..."
TG_ARN=$(aws elbv2 create-target-group \
  --name ai-branding-chatbot-tg \
  --protocol HTTP \
  --port 8501 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path / \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text 2>/dev/null || \
  aws elbv2 describe-target-groups \
    --region $REGION \
    --names ai-branding-chatbot-tg \
    --query "TargetGroups[0].TargetGroupArn" \
    --output text)

echo "Target Group ARN: $TG_ARN"

# 9. Create ALB listener
echo "👂 Creating ALB listener..."
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --region $REGION 2>/dev/null || echo "Listener already exists"

# 10. Create IAM role for ECS task execution
echo "🔑 Creating IAM role..."
ROLE_NAME="ecsTaskExecutionRole"
aws iam create-role \
  --role-name $ROLE_NAME \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || echo "Role already exists"

aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || echo "Policy already attached"

ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "Role ARN: $ROLE_ARN"

# Wait for role to be available
echo "⏳ Waiting for IAM role to propagate..."
sleep 10

# 11. Register task definition
echo "📋 Registering ECS task definition..."
cat > /tmp/task-def.json <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "$ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "streamlit",
      "image": "$ECR_REPO:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "PORT", "value": "8501"},
        {"name": "ENVIRONMENT", "value": "dev"},
        {"name": "AWS_REGION", "value": "$REGION"},
        {"name": "API_BASE_URL", "value": "$API_URL"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$TASK_FAMILY",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-def.json \
  --region $REGION

echo "✅ Task definition registered"

# 12. Create or update ECS service
echo "🚀 Creating ECS service..."
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --task-definition $TASK_FAMILY \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$ECS_SG_ID],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=streamlit,containerPort=8501" \
  --region $REGION 2>/dev/null || \
  aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_FAMILY \
    --force-new-deployment \
    --region $REGION

echo "✅ ECS service created/updated"

# 13. Wait for service to stabilize
echo "⏳ Waiting for service to become stable (this may take 2-3 minutes)..."
aws ecs wait services-stable \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --region $REGION

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Streamlit URL: http://$ALB_DNS"
echo ""
echo "📊 Monitor logs:"
echo "   aws logs tail /ecs/$TASK_FAMILY --follow --region $REGION"
echo ""
echo "🔍 Check service status:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION"
