#!/bin/bash

revolut_home=~/Downloads/revolut
processed_months=()

for file in `ls ${revolut_home}/*/*account-statement*`; do
    # Extract the dates
    start_date=$(echo "$file" | cut -d_ -f2)
    end_date=$(echo "$file" | cut -d_ -f3)

    # Calculate the new dates (subtract one month)
    # new_start_date=$(date -d "$start_date - 1 month" +%Y-%m-%d)
    month=$(date -d "$start_date" +%Y%m)


    # Extract currency
    dirname=$(dirname "$file")  # /home/artur/Downloads/revolut/chf
    currency=$(basename "${dirname^^}")  # chf

    echo $month $currency

    # Extract the ID
    id=$(echo "$file" | cut -d_ -f5 | cut -d. -f1)


    # Construct the new filename with the month partition first
    new_dir="${revolut_home}/month=${month}/account=${currency}"
    new_file="${new_dir}/revolut-${currency}-account-statement_${start_date}_${end_date}_de-ch_${id}.csv"

    # create dir
    echo mkdir -p $new_dir
    mkdir -p $new_dir
    echo mv $file $new_file

    # Rename the file
    mv $file $new_file
    processed_months+=($month)

    echo "Moving to GCP"
    echo gsutil mv $new_file "gs://af-finanzen-banks/raw/revolut/month=${month}/account=${currency}/"
    gsutil mv $new_file "gs://af-finanzen-banks/raw/revolut/month=${month}/account=${currency}/"
done

# Determine Region to write (Default: europe-west6)
# User can provide a region as the first argument to the script
target_region="${1:-europe-west6}"

# Get unique months that were processed
unique_months=$(printf "%s\n" "${processed_months[@]}" | sort -u)

for month in $unique_months; do
    echo "Creating sentinel file for month $month with region $target_region"
    # Write month on first line, region on second line
    printf "%s\n%s" "$month" "$target_region" > "/tmp/_SUCCESS"
    
    echo "Uploading _SUCCESS file..."
    full_cmd="gsutil cp /tmp/_SUCCESS gs://af-finanzen-banks/raw/revolut/month=${month}/_SUCCESS"
    echo "Executing: $full_cmd"
    $full_cmd
    
    rm "/tmp/_SUCCESS"
done