import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables from .env file
load_dotenv()

# Initialize S3 client with credentials from .env
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

def get_all_buckets():
    """
    Fetch all S3 buckets in the account
    """
    try:
        response = s3_client.list_buckets()
        return response.get('Buckets', [])
    except ClientError as e:
        print(f"Error fetching buckets: {e}")
        return []

def check_bucket_empty(bucket_name):
    """
    Check if a bucket is empty (has no objects)
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=1
        )
        # If KeyCount is 0 or 'Contents' key doesn't exist, bucket is empty
        return response.get('KeyCount', 0) == 0
    except ClientError as e:
        print(f"Error checking bucket {bucket_name}: {e}")
        return None

def get_bucket_region(bucket_name):
    """
    Get the region of a bucket
    """
    try:
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        location = response.get('LocationConstraint')
        # us-east-1 returns None as LocationConstraint
        return location if location else 'us-east-1'
    except ClientError as e:
        return 'unknown'

def find_empty_buckets():
    """
    Find and list all empty S3 buckets
    """
    print("Fetching all S3 buckets...")
    buckets = get_all_buckets()
    
    if not buckets:
        print("No buckets found.")
        return []
    
    print(f"Found {len(buckets)} buckets. Checking for empty ones...\n")
    
    empty_buckets = []
    
    for bucket in buckets:
        bucket_name = bucket['Name']
        is_empty = check_bucket_empty(bucket_name)
        
        if is_empty:
            region = get_bucket_region(bucket_name)
            empty_buckets.append({
                'bucketName': bucket_name,
                'createdAt': bucket['CreationDate'],
                'region': region
            })
            print(f"[EMPTY] {bucket_name} (Region: {region})")
        elif is_empty is False:
            print(f"[NOT EMPTY] {bucket_name}")
    
    return empty_buckets

def main():
    print("=" * 60)
    print("AWS S3 Empty Bucket Finder")
    print("=" * 60 + "\n")
    
    empty_buckets = find_empty_buckets()
    
    print("\n" + "=" * 60)
    print(f"Summary: Found {len(empty_buckets)} empty buckets")
    print("=" * 60)
    
    if empty_buckets:
        print("\nEmpty Buckets Details:")
        for bucket in empty_buckets:
            print(f"\nBucket Name: {bucket['bucketName']}")
            print(f"Region: {bucket['region']}")
            print(f"Created At: {bucket['createdAt']}")
        
        # Save to file for easy reference
        with open('empty_s3_buckets.txt', 'w', encoding='utf-8') as f:
            f.write("Empty S3 Buckets\n")
            f.write("=" * 60 + "\n\n")
            for bucket in empty_buckets:
                f.write(f"Bucket Name: {bucket['bucketName']}\n")
                f.write(f"Region: {bucket['region']}\n")
                f.write(f"Created At: {bucket['createdAt']}\n")
                f.write("-" * 60 + "\n")
        
        print(f"\nResults saved to: empty_s3_buckets.txt")

if __name__ == "__main__":
    main()
