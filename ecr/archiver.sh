#!/bin/bash
# this is ecr archiver
# this is ecr archiver
# this is ecr archiver
# this is ecr archiver
# this is ecr archiver
YEARS=1
ECR_REPO=""
S3_BUCKET=""
LOGIN_REFRESH_INTERVAL=$((12 * 60 * 60))  # 12 hours in seconds
LAST_LOGIN_FILE="/tmp/docker_login_timestamp"
black_list=(
)

refresh_docker_login() {
    echo "Refreshing Docker login credentials..."
    aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REPO
    if [ $? -eq 0 ]; then
        echo $(date +%s) > $LAST_LOGIN_FILE
        echo "Docker login successful"
    else
        echo "Docker login failed"
        return 1
    fi
}

should_refresh_login() {
    # If login file doesn't exist, login is needed
    if [ ! -f $LAST_LOGIN_FILE ]; then
        return 0
    fi

    # Check if 12 hours have passed since last login
    last_login=$(cat $LAST_LOGIN_FILE)
    current_time=$(date +%s)
    time_diff=$((current_time - last_login))
    if [ $time_diff -ge $LOGIN_REFRESH_INTERVAL ]; then
        return 0
    fi

    return 1
}

is_repo_blacklisted() {
    local string="$1"
    shift
    local array=("$@")
    for item in "${array[@]}"; do
        if [ "$item" = "$string" ]; then
            return 0  # Return success if string is found
        fi
    done
    return 1  # Return failure if string is not found
}


# Get the current timestamp
current_timestamp=$(date -u +%s)

# Calculate the timestamp from one year ago
one_year_ago=$((current_timestamp - (365 * $YEARS * 24 * 60 * 60)))

# AWS CLI command to list repositories in the ECR registry
aws_ecr_list_repositories_command="aws ecr describe-repositories"
repositories=$(eval $aws_ecr_list_repositories_command)
if [ -z "$repositories" ]; then
    echo "No repositories found in the ECR registry."
    exit 0
fi

total_unpulled_size=0
total_unpulled_count=0

# login to docker
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REPO

# Iterate over each repository
for repo_name in $(echo "$repositories" | jq -r '.repositories[].repositoryName'); do
#for repo_name in "${white_list[@]}"; do
    echo "Checking repository: $repo_name"
    if is_repo_blacklisted "$repo_name" "${black_list[@]}"; then
      echo "repo already migrated $repo_name"
      continue
    fi

    aws_ecr_list_images_command="aws ecr list-images --repository-name $repo_name"

    # Get images in the repository
    images=$(eval $aws_ecr_list_images_command)

    if [ -z "$images" ]; then
        echo "No images found in the repository: $repo_name"
        continue
    fi

    # create subdirectory in s3 folder
    aws s3api put-object --bucket $S3_BUCKET --key $repo_name"/"

    # Iterate over each image in the repository
    for image in $(echo "$images" | jq -r '.imageIds[].imageDigest' | sort | uniq); do
       # Refresh login every 12 hours
        if should_refresh_login; then
            refresh_docker_login
        fi
        image_full=$(aws ecr describe-images --repository-name $repo_name --image-ids imageDigest=$image)
        image_pulled=$(echo $image_full | jq -r '.imageDetails[].lastRecordedPullTime')
        image_pulled_size=$(echo $image_full | jq -r '.imageDetails[].imageSizeInBytes')
        if [ "$image_pulled" != "null" ]; then
            image_pulled_timestamp=$(date -d "$image_pulled" +%s)
        else
            image_pulled_timestamp="1672425000" # year 2022
        fi

        if [ $image_pulled_timestamp -lt $one_year_ago ]; then
            echo "Image with digest $image in repository $repo_name was pulled more than ${YEARS} years ago."
            echo "It's time to archive!"
            total_unpulled_count=$((total_unpulled_count+1))
            total_unpulled_size=$((total_unpulled_size+image_pulled_size))
#            continue

            image_name=$image".tar.gz"
            docker image pull --quiet $ECR_REPO/$repo_name@$image
            docker save $ECR_REPO/$repo_name@$image | gzip > $image_name
            aws s3 cp $image_name s3://$S3_BUCKET/$repo_name/

            # cleanup
            rm $image_name
            docker image rm $ECR_REPO/$repo_name@$image
            aws ecr batch-delete-image --repository-name $repo_name --image-ids imageDigest=$image

        fi
    done
done
echo "total number of images unpulled in ${YEARS} years is $total_unpulled_count"
echo "total size of images unpulled in ${YEARS} years is $total_unpulled_size"
