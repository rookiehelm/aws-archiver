#!/bin/bash
set -euo pipefail

# ======================
# Jenkins parameters
# ======================
YEARS="${1:-1}"              # Year-wise run (default 1 year)
SERVER_INDEX="${2:-0}"       # 0,1,2,3
TOTAL_SERVERS=4

# ======================
# Config
# ======================
ECR_REPO=""
S3_BUCKET=""
LOGIN_REFRESH_INTERVAL=$((12 * 60 * 60))
LAST_LOGIN_FILE="/tmp/docker_login_timestamp"

black_list=(
)

# ======================
# Functions
# ======================
refresh_docker_login() {
    echo "Refreshing Docker login credentials..."
    aws ecr get-login-password \
        | docker login --username AWS --password-stdin "$ECR_REPO"
    date +%s > "$LAST_LOGIN_FILE"
}

should_refresh_login() {
    [ ! -f "$LAST_LOGIN_FILE" ] && return 0
    last_login=$(cat "$LAST_LOGIN_FILE")
    (( $(date +%s) - last_login >= LOGIN_REFRESH_INTERVAL ))
}

is_repo_blacklisted() {
    local repo="$1"
    for item in "${black_list[@]}"; do
        [[ "$item" == "$repo" ]] && return 0
    done
    return 1
}

# ======================
# Time calculation
# ======================
current_timestamp=$(date -u +%s)
one_year_ago=$((current_timestamp - (365 * YEARS * 24 * 60 * 60)))

# ======================
# Fetch repositories
# ======================
repositories=$(aws ecr describe-repositories \
    | jq -r '.repositories[].repositoryName' | sort)

if [ -z "$repositories" ]; then
    echo "No repositories found"
    exit 0
fi

# ======================
# Login
# ======================
refresh_docker_login

repo_index=0
total_unpulled_count=0
total_unpulled_size=0

# ======================
# Main loop
# ======================
for repo_name in $repositories; do

    # distribute repos across servers
    if (( repo_index % TOTAL_SERVERS != SERVER_INDEX )); then
        ((repo_index++))
        continue
    fi
    ((repo_index++))

    echo "[$SERVER_INDEX] Processing repo: $repo_name"

    if is_repo_blacklisted "$repo_name"; then
        echo "Skipping blacklisted repo $repo_name"
        continue
    fi

    images=$(aws ecr list-images --repository-name "$repo_name" \
        | jq -r '.imageIds[].imageDigest' | sort -u)

    [ -z "$images" ] && continue

    aws s3api put-object --bucket "$S3_BUCKET" --key "$repo_name/"

    for image in $images; do
        should_refresh_login && refresh_docker_login

        image_full=$(aws ecr describe-images \
            --repository-name "$repo_name" \
            --image-ids imageDigest="$image")

        image_pulled=$(echo "$image_full" | jq -r '.imageDetails[].lastRecordedPullTime')
        image_size=$(echo "$image_full" | jq -r '.imageDetails[].imageSizeInBytes')

        if [ "$image_pulled" != "null" ]; then
            pulled_ts=$(date -d "$image_pulled" +%s)
        else
            pulled_ts=1672425000
        fi

        if (( pulled_ts < one_year_ago )); then
            echo "Archiving image $image from $repo_name"

            ((total_unpulled_count++))
            ((total_unpulled_size+=image_size))

            image_file="${image}.tar.gz"

            docker pull --quiet "$ECR_REPO/$repo_name@$image"
            docker save "$ECR_REPO/$repo_name@$image" | gzip > "$image_file"
            aws s3 cp "$image_file" "s3://$S3_BUCKET/$repo_name/"

            rm -f "$image_file"
            docker rmi "$ECR_REPO/$repo_name@$image"

            aws ecr batch-delete-image \
                --repository-name "$repo_name" \
                --image-ids imageDigest="$image"
        fi
    done
done

echo "[$SERVER_INDEX] Total images archived: $total_unpulled_count"
echo "[$SERVER_INDEX] Total size archived: $total_unpulled_size"
