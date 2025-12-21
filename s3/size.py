import boto3
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()
env_path = script_dir / '.env'

# Load environment variables from .env file in script directory
load_dotenv(dotenv_path=env_path)

def get_bucket_size(bucket_name, aws_access_key_id=None, aws_secret_access_key=None):

        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        total_size = 0
        object_count = 0

        print(f"Calculating size for bucket: {bucket_name}")
        print("Note: Processing first 1000 objects only\n")

        response = s3.list_objects_v2(Bucket=bucket_name)

        if 'Contents' in response:
            for obj in response['Contents']:
                total_size += obj['Size']
                object_count += 1

        result = {
            'bytes': total_size,
            'mb': total_size / (1024 * 1024),
            'gb': total_size / (1024 * 1024 * 1024),
            'object_count': object_count
        }

        return result

def format_size(size_bytes):
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


if __name__ == "__main__":
    # Configuration

    BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Error: .env file not found in current directory")
        print(f"Current directory: {os.getcwd()}")
        print("\nPlease create a .env file with the following content:")
        print("S3_BUCKET_NAME=your-bucket-name")
        print("AWS_ACCESS_KEY_ID=your-access-key-id")
        print("AWS_SECRET_ACCESS_KEY=your-secret-access-key")
        exit(1)

    if not BUCKET_NAME:
        print("Error: S3_BUCKET_NAME not found in .env file")
        print("Please add S3_BUCKET_NAME=your-bucket-name to your .env file")
        exit(1)

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        print("Warning: AWS credentials not found in .env file, using default credentials")

    result = get_bucket_size(BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

    if result:
        print("\n" + "=" * 50)
        print(f"Bucket: {BUCKET_NAME}")
        print("=" * 50)
        print(f"Total Objects: {result['object_count']:,}")
        print(f"Total Size: {format_size(result['bytes'])}")
        print(f"  - {result['bytes']:,} bytes")
        print(f"  - {result['mb']:.2f} MB")
        print(f"  - {result['gb']:.2f} GB")
        print("=" * 50)