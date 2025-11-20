#!/bin/bash

revolut_home=~/Downloads/revolut
for file in `ls ${revolut_home}/*/account-statement*`; do
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


    # Construct the new filename
    new_dir="${revolut_home}/account=${currency}/month=${month}"
    new_file="${new_dir}/revolut-${currency}-account-statement_${start_date}_${end_date}_de-ch_${id}.csv"
    
    # create dir
    echo mkdir -p $new_dir
    mkdir -p $new_dir
    echo mv $file $new_file

    # Rename the file
    mv $file $new_file

    echo "Moving to GCP"
    echo gsutil mv $new_file "gs://af-finanzen-banks/revolut_raw/account=${currency}/month=${month}/"
    gsutil mv $new_file "gs://af-finanzen-banks/revolut_raw/account=${currency}/month=${month}/"
done
