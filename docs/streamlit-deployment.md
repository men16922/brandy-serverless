# Streamlit Deployment Guide

## Overview

This guide covers deploying the Streamlit web interface to AWS ECS Fargate with Application Load Balancer (ALB).

## Architecture

- **ECS Fargate**: Serverless container orchestration
- **Application Load Balancer**: HTTP/WebSocket support
- **ECR**: Docker image registry
- **CloudWatch Logs**: Centralized logging

## Why ECS Fargate + ALB?

✅ **WebSocket Support**: ALB fully supports WebSocket connections required by Streamlit  
✅ **Scalability**: Auto-scaling based on CPU/memory  
✅ **Cost-Effective**: Pay only for running tasks  
✅ **No Server Management**: Fully managed infrastructure

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Docker installed and running
3. SAM backend deployed (API Gateway URL needed)

## Deployment Steps

### 1. Deploy Backend First

Ensure your SAM backend is deployed:

```bash
sam build
sam deploy --config-env dev
```

Get the API Gateway URL:

```bash
aws cloudformation describe-stacks \
  --stack-name ai-branding-chatbot-dev \
  --region us-west-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

### 2. Deploy Streamlit to ECS Fargate

Run the deployment script:

```bash
./scripts/deploy_ecs_fargate.sh
```

This script will:
1. Build Docker image for linux/amd64
2. Push image to ECR
3. Create ECS cluster
4. Create security groups
5. Create Application Load Balancer
6. Create target group
7. Register ECS task definition
8. Create/update ECS service
9. Wait for service to stabilize

### 3. Access the Application

After deployment completes, you'll see:

```
✅ Deployment complete!

🌐 Streamlit URL: http://ai-branding-chatbot-alb-XXXXXXXXXX.us-west-2.elb.amazonaws.com
```

## Monitoring

### View Logs

```bash
# Real-time logs
aws logs tail /ecs/ai-branding-chatbot-streamlit --follow --region us-west-2

# Last 10 minutes
aws logs tail /ecs/ai-branding-chatbot-streamlit --since 10m --region us-west-2
```

### Check Service Status

```bash
aws ecs describe-services \
  --cluster ai-branding-chatbot-cluster \
  --services ai-branding-chatbot-streamlit \
  --region us-west-2
```

### Check Running Tasks

```bash
aws ecs list-tasks \
  --cluster ai-branding-chatbot-cluster \
  --service-name ai-branding-chatbot-streamlit \
  --region us-west-2
```

## Updating the Application

### Update Code

1. Make changes to `src/streamlit/app.py`
2. Run deployment script again:

```bash
./scripts/deploy_ecs_fargate.sh
```

The script will:
- Build new Docker image
- Push to ECR
- Force new deployment with updated image

### Update Environment Variables

Edit the task definition in `scripts/deploy_ecs_fargate.sh`:

```json
"environment": [
  {"name": "PORT", "value": "8501"},
  {"name": "ENVIRONMENT", "value": "dev"},
  {"name": "AWS_REGION", "value": "us-west-2"},
  {"name": "API_BASE_URL", "value": "YOUR_API_URL"}
]
```

Then redeploy.

## Cleanup

To remove all ECS resources:

```bash
./scripts/cleanup_ecs.sh
```

This will delete:
- ECS service
- ECS cluster
- Application Load Balancer
- Target group
- Security groups

## Troubleshooting

### Service Won't Start

Check task logs:

```bash
aws logs tail /ecs/ai-branding-chatbot-streamlit --since 30m --region us-west-2
```

Common issues:
- **Image pull error**: Check ECR permissions
- **Port conflict**: Ensure port 8501 is exposed
- **API connection**: Verify API_BASE_URL is correct

### WebSocket Connection Failed

- Ensure ALB is used (not App Runner)
- Check security group allows traffic from ALB to ECS tasks
- Verify Streamlit is configured with WebSocket compression

### Health Check Failing

Check Streamlit health endpoint:

```bash
# Get task IP
TASK_ARN=$(aws ecs list-tasks --cluster ai-branding-chatbot-cluster --service-name ai-branding-chatbot-streamlit --region us-west-2 --query 'taskArns[0]' --output text)

# Get task details
aws ecs describe-tasks --cluster ai-branding-chatbot-cluster --tasks $TASK_ARN --region us-west-2
```

## Cost Estimation

- **ECS Fargate**: ~$0.04/hour (0.5 vCPU, 1GB RAM)
- **ALB**: ~$0.0225/hour + $0.008/LCU-hour
- **Data Transfer**: $0.09/GB (out to internet)

**Estimated monthly cost**: ~$35-50 for 24/7 operation

## Local Development

For local testing:

```bash
# Run Streamlit locally
streamlit run src/streamlit/app.py --server.port 8501

# Access at http://localhost:8501
```

Set environment variable:

```bash
export API_BASE_URL=https://YOUR_API_GATEWAY_URL/dev
```

## Production Considerations

### Custom Domain

1. Create Route 53 hosted zone
2. Request ACM certificate
3. Add HTTPS listener to ALB
4. Create Route 53 alias record

### Auto-scaling

Add auto-scaling to ECS service:

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/ai-branding-chatbot-cluster/ai-branding-chatbot-streamlit \
  --min-capacity 1 \
  --max-capacity 4
```

### High Availability

- Deploy tasks across multiple availability zones (already configured)
- Increase desired count to 2+ for redundancy
- Configure ALB health checks appropriately

## References

- [ECS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [Streamlit Documentation](https://docs.streamlit.io/)
