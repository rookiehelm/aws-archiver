import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables from .env file
load_dotenv()

# Initialize ECR client with credentials from .env
ecr_client = boto3.client(
    'ecr',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

def get_all_repositories():
    """
    Fetch all ECR repositories in the account
    """
    repositories = []
    try:
        paginator = ecr_client.get_paginator('describe_repositories')
        for page in paginator.paginate():
            repositories.extend(page['repositories'])
        return repositories
    except ClientError as e:
        print(f"Error fetching repositories: {e}")
        return []

def check_repository_empty(repository_name):
    """
    Check if a repository is empty (has no images)
    """
    try:
        response = ecr_client.list_images(repositoryName=repository_name)
        image_count = len(response.get('imageIds', []))
        return image_count == 0
    except ClientError as e:
        print(f"Error checking repository {repository_name}: {e}")
        return None

def find_empty_repositories():
    """
    Find and list all empty ECR repositories
    """
    print("Fetching all ECR repositories...")
    repositories = get_all_repositories()
    
    if not repositories:
        print("No repositories found.")
        return []
    
    print(f"Found {len(repositories)} repositories. Checking for empty ones...\n")
    
    empty_repos = []
    
    for repo in repositories:
        repo_name = repo['repositoryName']
        is_empty = check_repository_empty(repo_name)
        
        if is_empty:
            empty_repos.append({
                'repositoryName': repo_name,
                'repositoryArn': repo['repositoryArn'],
                'repositoryUri': repo['repositoryUri'],
                'createdAt': repo['createdAt']
            })
            print(f"[EMPTY] {repo_name}")
        elif is_empty is False:
            print(f"[NOT EMPTY] {repo_name}")
    
    return empty_repos

def main():
    print("=" * 60)
    print("AWS ECR Empty Repository Finder")
    print("=" * 60 + "\n")
    
    empty_repositories = find_empty_repositories()
    
    print("\n" + "=" * 60)
    print(f"Summary: Found {len(empty_repositories)} empty repositories")
    print("=" * 60)
    
    if empty_repositories:
        print("\nEmpty Repositories Details:")
        for repo in empty_repositories:
            print(f"\nRepository Name: {repo['repositoryName']}")
            print(f"ARN: {repo['repositoryArn']}")
            print(f"URI: {repo['repositoryUri']}")
            print(f"Created At: {repo['createdAt']}")
        
        # Save to file for easy reference
        with open('empty_ecr_repositories.txt', 'w', encoding='utf-8') as f:
            f.write("Empty ECR Repositories\n")
            f.write("=" * 60 + "\n\n")
            for repo in empty_repositories:
                f.write(f"Repository Name: {repo['repositoryName']}\n")
                f.write(f"ARN: {repo['repositoryArn']}\n")
                f.write(f"URI: {repo['repositoryUri']}\n")
                f.write(f"Created At: {repo['createdAt']}\n")
                f.write("-" * 60 + "\n")
        
        print(f"\nResults saved to: empty_ecr_repositories.txt")

if __name__ == "__main__":
    main()