#!/bin/bash
# Cleanup ECS Fargate resources

set -euo pipefail

REGION="us-west-2"
CLUSTER_NAME="ai-branding-chatbot-cluster"
SERVICE_NAME="ai-branding-chatbot-streamlit"
ALB_NAME="ai-branding-chatbot-alb"
TARGET_GROUP_NAME="ai-branding-chatbot-tg"
ALB_SG_NAME="ai-branding-chatbot-alb-sg"
ECS_SG_NAME="ai-branding-chatbot-ecs-sg"

echo "🗑️  Cleaning up ECS Fargate resources..."

# Delete service
echo "Deleting ECS service..."
aws ecs update-service --region ${REGION} \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --desired-count 0 2>/dev/null || true

aws ecs delete-service --region ${REGION} \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --force 2>/dev/null || true

# Delete cluster
echo "Deleting ECS cluster..."
aws ecs delete-cluster --region ${REGION} \
    --cluster ${CLUSTER_NAME} 2>/dev/null || true

# Delete ALB
echo "Deleting ALB..."
ALB_ARN=$(aws elbv2 describe-load-balancers --region ${REGION} \
    --names ${ALB_NAME} --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text 2>/dev/null || echo "")

if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
    aws elbv2 delete-load-balancer --region ${REGION} \
        --load-balancer-arn ${ALB_ARN} 2>/dev/null || true
fi

# Delete target group
echo "Deleting target group..."
TG_ARN=$(aws elbv2 describe-target-groups --region ${REGION} \
    --names ${TARGET_GROUP_NAME} --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null || echo "")

if [ -n "$TG_ARN" ] && [ "$TG_ARN" != "None" ]; then
    sleep 10  # Wait for ALB deletion
    aws elbv2 delete-target-group --region ${REGION} \
        --target-group-arn ${TG_ARN} 2>/dev/null || true
fi

# Delete security groups
echo "Deleting security groups..."
sleep 30  # Wait for resources to be fully deleted

ALB_SG_ID=$(aws ec2 describe-security-groups --region ${REGION} \
    --filters "Name=group-name,Values=${ALB_SG_NAME}" \
    --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo "")

ECS_SG_ID=$(aws ec2 describe-security-groups --region ${REGION} \
    --filters "Name=group-name,Values=${ECS_SG_NAME}" \
    --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo "")

if [ -n "$ECS_SG_ID" ] && [ "$ECS_SG_ID" != "None" ]; then
    aws ec2 delete-security-group --region ${REGION} \
        --group-id ${ECS_SG_ID} 2>/dev/null || echo "Could not delete ECS security group"
fi

if [ -n "$ALB_SG_ID" ] && [ "$ALB_SG_ID" != "None" ]; then
    aws ec2 delete-security-group --region ${REGION} \
        --group-id ${ALB_SG_ID} 2>/dev/null || echo "Could not delete ALB security group"
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Note: IAM roles and ECR repository are NOT deleted."
echo "Delete them manually if needed:"
echo "  - IAM Role: ecsTaskExecutionRole"
echo "  - ECR Repo: ai-branding-chatbot-streamlit"
