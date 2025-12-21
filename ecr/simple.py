
# Uses your AWS keys

# Connects to ECR

# Lists all ECR repositories

# Prints repository name + created date + year


# 1️⃣ Prerequisite

# Install boto3:

# pip install boto3


# ---

# 2️⃣ Python Script (Using AWS Keys)

import boto3

# 🔐 AWS Credentials (DO NOT SHARE PUBLICLY)
AWS_ACCESS_KEY = "YOUR_ACCESS_KEY"
AWS_SECRET_KEY = "YOUR_SECRET_KEY"
AWS_REGION = "ap-south-1"   # change if needed

# Create ECR client
ecr_client = boto3.client(
    'ecr',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def get_ecr_repo_creation_year():
    response = ecr_client.describe_repositories()

    for repo in response['repositories']:
        repo_name = repo['repositoryName']
        created_at = repo['createdAt']
        year = created_at.year

        print(f"Repository: {repo_name}")
        print(f"Created At: {created_at}")
        print(f"Year: {year}")
        print("-" * 40)

# get_ecr_repo_creation_year()


# ---

# 3️⃣ Sample Output

# Repository: my-backend-app
# Created At: 2021-06-15 10:25:30+00:00
# Year: 2021
# ----------------------------------------
# Repository: frontend-ui
# Created At: 2023-02-10 08:12:11+00:00
# Year: 2023
# ----------------------------------------


# ---

# 4️⃣ If You Want a Specific Repository Only

# Replace the function with this:

def get_specific_repo_year(repo_name):
    response = ecr_client.describe_repositories(
        repositoryNames=[repo_name]
    )

    repo = response['repositories'][0]
    print("Repository:", repo['repositoryName'])
    print("Created At:", repo['createdAt'])
    print("Year:", repo['createdAt'].year)

get_specific_repo_year("my-repo-name")

