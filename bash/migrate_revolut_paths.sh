#!/bin/bash
# This script migrates Revolut transaction files from the old directory structure
# to the new, more efficient Hive-partitioned structure.
# It copies files from gs://af-finanzen-banks/revolut_raw/account=.../month=...
# to gs://af-finanzen-banks/raw/revolut/month=.../account=...

# --- CONFIGURATION ---
SOURCE_BUCKET="gs://af-finanzen-banks/revolut_raw"
DEST_BUCKET="gs://af-finanzen-banks/raw/revolut"

# --- SCRIPT ---
echo "Starting GCS file migration for Revolut data..."
echo "Source: $SOURCE_BUCKET"
echo "Destination: $DEST_BUCKET"
echo "---"

# Get all .csv files from the source location recursively and pipe to a while loop
gcloud storage ls "$SOURCE_BUCKET/**.csv" | while read -r file; do
    # Use regex to extract the account and month values from the file path
    if [[ "$file" =~ account=([^/]+)/month=([^/]+) ]]; then
        account=${BASH_REMATCH[1]}
        month=${BASH_REMATCH[2]}
        fileName=$(basename "$file")

        # Construct the new, correct Hive-partitioned path
        newPath="${DEST_BUCKET}/month=${month}/account=${account}/${fileName}"

        echo "Copying..."
        echo "  FROM: $file"
        echo "  TO:   $newPath"

        # Execute the copy command
        gcloud storage cp "$file" "$newPath"

        # Check for errors
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to copy $file. Halting script." >&2
            exit 1
        fi
        echo "  ...Success"
        echo ""

    else
        echo "WARNING: Could not parse path for file: $file. Skipping." >&2
    fi
done

echo "---"
echo "Migration script completed."
echo "Please verify the copied files in the destination: $DEST_BUCKET"
echo "Once you have confirmed the data is correct, you can delete the old directory with:"
echo "gcloud storage rm -r $SOURCE_BUCKET"
