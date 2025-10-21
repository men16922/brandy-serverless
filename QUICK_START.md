# Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Prerequisites
- AWS CLI configured
- Docker installed
- Python 3.9+

### Step 1: Deploy Backend (2 min)
```bash
# Clone and setup
git clone <repository-url>
cd ai-branding-chatbot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Deploy SAM
sam build
sam deploy --config-env dev
```

### Step 2: Configure S3 (1 min)
```bash
# Get bucket name
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name ai-branding-chatbot-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Configure public access
aws s3api delete-public-access-block --bucket $BUCKET
aws s3api put-bucket-cors --bucket $BUCKET --cors-configuration '{
  "CORSRules": [{"AllowedOrigins": ["*"], "AllowedMethods": ["GET", "HEAD"], "AllowedHeaders": ["*"], "MaxAgeSeconds": 3000}]
}'
aws s3api put-bucket-policy --bucket $BUCKET --policy "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{\"Effect\": \"Allow\", \"Principal\": \"*\", \"Action\": \"s3:GetObject\", \"Resource\": \"arn:aws:s3:::$BUCKET/*\"}]
}"
```

### Step 3: Deploy Frontend (2 min)
```bash
# Deploy Streamlit to ECS Fargate
./scripts/deploy_ecs_fargate.sh

# Wait for deployment to complete
# URL will be displayed: http://ai-branding-chatbot-alb-XXXXXXXXXX.us-west-2.elb.amazonaws.com
```

### Step 4: Access Application
Open the ALB URL in your browser and start generating branding materials!

## 📊 Monitor

```bash
# Backend logs (Lambda)
aws logs tail /aws/lambda/ai-branding-chatbot-supervisor-agent-dev --follow

# Frontend logs (ECS)
aws logs tail /ecs/ai-branding-chatbot-streamlit --follow

# Check ECS service
aws ecs describe-services \
  --cluster ai-branding-chatbot-cluster \
  --services ai-branding-chatbot-streamlit
```

## 🧹 Cleanup

```bash
# Remove frontend
./scripts/cleanup_ecs.sh

# Remove backend
sam delete --stack-name ai-branding-chatbot-dev
```

## 📚 Documentation

- **[README.md](README.md)** - Complete project documentation
- **[docs/streamlit-deployment.md](docs/streamlit-deployment.md)** - Detailed deployment guide
- **[docs/DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md)** - Quick reference

## 🆘 Troubleshooting

### Images not loading?
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket $BUCKET

# Check CORS
aws s3api get-bucket-cors --bucket $BUCKET
```

### Streamlit not accessible?
```bash
# Check ECS service status
aws ecs describe-services \
  --cluster ai-branding-chatbot-cluster \
  --services ai-branding-chatbot-streamlit

# Check ALB health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names ai-branding-chatbot-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)
```

### API Gateway errors?
```bash
# Check Lambda function
aws lambda get-function \
  --function-name ai-branding-chatbot-supervisor-agent-dev

# View recent logs
aws logs tail /aws/lambda/ai-branding-chatbot-supervisor-agent-dev --since 10m
```

## 🎯 Next Steps

1. **Custom Domain**: Add Route 53 + ACM certificate
2. **HTTPS**: Configure ALB HTTPS listener
3. **Auto-scaling**: Configure ECS service auto-scaling
4. **Monitoring**: Set up CloudWatch alarms
5. **CI/CD**: Implement GitHub Actions pipeline

## 💡 Tips

- Use `sam sync --watch` for rapid development
- Run Streamlit locally: `streamlit run src/streamlit/app.py`
- Check AWS costs: `aws ce get-cost-and-usage`
- Enable CloudWatch Container Insights for better monitoring
