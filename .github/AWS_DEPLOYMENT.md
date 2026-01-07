# AWS App Runner Deployment Setup

This document describes how to set up AWS resources and GitHub secrets for automated deployment to AWS App Runner.

## Prerequisites

- AWS Account with appropriate permissions
- GitHub repository with admin access
- AWS CLI installed (for initial setup)

## AWS Resources Setup

### 1. Create ECR Repository

First, create an Amazon ECR repository to store your Docker images:

```bash
aws ecr create-repository \
  --repository-name image-story-generator \
  --region us-east-1
```

### 2. Create IAM Roles

#### A. GitHub Actions Role (for OIDC)

Create an IAM role that GitHub Actions will assume to deploy:

1. Create a trust policy file `github-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:IritaSee/image-story-generator:*"
        }
      }
    }
  ]
}
```

2. Create the role:

```bash
aws iam create-role \
  --role-name GitHubActionsAppRunnerRole \
  --assume-role-policy-document file://github-trust-policy.json
```

3. Attach necessary policies:

```bash
# ECR permissions
aws iam attach-role-policy \
  --role-name GitHubActionsAppRunnerRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

# App Runner permissions
aws iam attach-role-policy \
  --role-name GitHubActionsAppRunnerRole \
  --policy-arn arn:aws:iam::aws:policy/AWSAppRunnerFullAccess
```

#### B. App Runner Access Role (for ECR)

Create a role that App Runner will use to pull images from ECR:

1. Create trust policy `apprunner-trust-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

2. Create the role:

```bash
aws iam create-role \
  --role-name AppRunnerECRAccessRole \
  --assume-role-policy-document file://apprunner-trust-policy.json
```

3. Attach ECR read policy:

```bash
aws iam attach-role-policy \
  --role-name AppRunnerECRAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
```

### 3. Configure GitHub OIDC Provider in AWS

If not already configured, add GitHub as an OIDC provider:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

### Required Secrets

1. **AWS_ROLE_TO_ASSUME**
   - Value: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsAppRunnerRole`
   - Description: IAM role ARN that GitHub Actions will assume

2. **APP_RUNNER_ACCESS_ROLE_ARN**
   - Value: `arn:aws:iam::YOUR_ACCOUNT_ID:role/AppRunnerECRAccessRole`
   - Description: IAM role ARN that App Runner uses to access ECR

### How to Add Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the name and value specified above

## Workflow Configuration

### Environment Variables

The workflow uses the following environment variables (can be customized in `.github/workflows/aws-apprunner-deploy.yml`):

- `AWS_REGION`: AWS region for deployment (default: `us-east-1`)
- `ECR_REPOSITORY`: Name of the ECR repository (default: `image-story-generator`)
- `APP_RUNNER_SERVICE`: Name of the App Runner service (default: `image-story-generator-service`)

### Workflow Triggers

The workflow is triggered on:
- **Push to main branch**: Automatic deployment on code changes
- **Manual dispatch**: Can be triggered manually from GitHub Actions tab

## App Runner Service Configuration

The workflow configures App Runner with:
- **CPU**: 1 vCPU
- **Memory**: 2 GB
- **Port**: 5000 (Flask application port)
- **Auto-scaling**: Enabled by default

### Customizing Resources

To adjust CPU and memory, edit the workflow file:

```yaml
- name: Deploy to App Runner
  uses: awslabs/amazon-app-runner-deploy@main
  with:
    cpu: 2          # Change CPU (0.25, 0.5, 1, 2, 4)
    memory: 4       # Change Memory in GB (0.5, 1, 2, 3, 4, 6, 8, 10, 12)
```

## Deployment Process

### Automatic Deployment

1. Push code to the `main` branch
2. GitHub Actions workflow triggers automatically
3. Docker image is built from the Dockerfile
4. Image is pushed to Amazon ECR
5. App Runner service is updated with the new image
6. Service URL is displayed in the workflow output

### Manual Deployment

1. Go to **Actions** tab in GitHub
2. Select **Build and Deploy to AWS App Runner** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Monitoring and Troubleshooting

### View Deployment Status

- **GitHub Actions**: Check workflow runs in the Actions tab
- **AWS Console**: Monitor App Runner service in AWS Console
- **Logs**: View application logs in App Runner → Service → Logs

### Common Issues

1. **Authentication Failed**
   - Verify OIDC provider is configured correctly
   - Check IAM role trust relationships
   - Ensure GitHub secrets are set correctly

2. **ECR Push Failed**
   - Verify ECR repository exists
   - Check IAM role has ECR permissions
   - Ensure repository name matches in workflow

3. **App Runner Deployment Failed**
   - Check App Runner access role permissions
   - Verify Docker image runs locally
   - Review App Runner service logs

### Useful Commands

Check ECR images:
```bash
aws ecr list-images \
  --repository-name image-story-generator \
  --region us-east-1
```

Get App Runner service status:
```bash
aws apprunner list-services --region us-east-1
```

View App Runner service details:
```bash
aws apprunner describe-service \
  --service-arn <service-arn> \
  --region us-east-1
```

## Cost Considerations

### ECR Costs
- Storage: $0.10 per GB/month
- Data transfer: Standard AWS rates

### App Runner Costs
- **Provisioned instances**: Pay for compute and memory even when idle
- **1 vCPU + 2 GB**: ~$0.064/hour (~$46/month)
- **Active requests**: $0.064 per vCPU-hour + $0.007 per GB-hour

### Cost Optimization
- Delete old ECR images regularly
- Use App Runner auto-pause for dev environments
- Monitor usage in AWS Cost Explorer

## Security Best Practices

1. **Use IAM roles with least privilege**
   - Review and restrict IAM policies
   - Regularly audit role permissions

2. **Enable ECR image scanning**
   ```bash
   aws ecr put-image-scanning-configuration \
     --repository-name image-story-generator \
     --image-scanning-configuration scanOnPush=true
   ```

3. **Use private ECR repositories**
   - Don't make repositories public unless necessary

4. **Rotate credentials regularly**
   - Review and update IAM roles periodically

5. **Enable AWS CloudTrail**
   - Monitor API calls and deployments

## Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [Amazon ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [App Runner Pricing](https://aws.amazon.com/apprunner/pricing/)
