#!/bin/bash

# This script generates a BigQuery external table definition for a specific month
# and uses it to create the table in BigQuery.

# --- CONFIGURATION ---
# The CSV file containing table names and their corresponding Google Sheet URIs.
INPUT_CSV="transak.monatsabschluss.csv"
# The directory where the temporary JSON definition file will be stored.
OUTPUT_DIR="transak_i1/external_table_definitions"
# Your Google Cloud Project ID.
PROJECT_ID="af-finanzen"
# The BigQuery dataset where the table should be created.
DATASET_ID="monatsabschluss"

# --- SCRIPT LOGIC ---

# 1. Check for the month parameter
if [ -z "$1" ]; then
    echo "Error: Please provide the month as an argument."
    echo "Usage: $0 YYYYMM"
    exit 1
fi
TARGET_MONTH=$1

# Ensure the input CSV file exists
if [ ! -f "$INPUT_CSV" ]; then
    echo "Error: Input file '$INPUT_CSV' not found."
    exit 1
fi

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# 2. Find the specific row for the target month
TARGET_TABLE_NAME="revolut_abrechnung_${TARGET_MONTH}"
echo "TARGET_TABLE_NAME: $TARGET_TABLE_NAME"
MATCHING_LINE=$(grep "${TARGET_TABLE_NAME}," "$INPUT_CSV")

# Exit if no matching line was found
if [ -z "$MATCHING_LINE" ]; then
    echo "Error: No entry '$TARGET_TABLE_NAME' found for month '$TARGET_MONTH' in '$INPUT_CSV'."
    exit 1
fi

# 3. Split the line into variables
# We use 'read' with a changed Internal Field Separator (IFS) to split the line.
IFS=',' read -r table_name uri <<< "$MATCHING_LINE"

# Trim potential whitespace from the variables
table_name=$(echo "$table_name" | tr -d '[:space:]')
uri=$(echo "$uri" | tr -d '[:space:]')

echo "Processing table: $table_name"

# 4. JSON template for the external table definition
JSON_TEMPLATE=$(cat <<'EOF'
{
  "sourceFormat": "GOOGLE_SHEETS",
  "sourceUris": [
    "__URI__"
  ],
  "googleSheetsOptions": {
    "skipLeadingRows": 1,
    "range": "'Revolut Abrechnung'!A:W"
  },
  "schema": {
    "fields": [
      { "name": "tid", "type": "INTEGER", "mode": "NULLABLE" },
      { "name": "type", "type": "STRING", "mode": "NULLABLE" },
      { "name": "product", "type": "STRING", "mode": "NULLABLE" },
      { "name": "started", "type": "TIMESTAMP", "mode": "NULLABLE" },
      { "name": "completed", "type": "TIMESTAMP", "mode": "NULLABLE" },
      { "name": "description", "type": "STRING", "mode": "NULLABLE" },
      { "name": "amount", "type": "FLOAT", "mode": "NULLABLE" },
      { "name": "fee", "type": "FLOAT", "mode": "NULLABLE" },
      { "name": "currency", "type": "STRING", "mode": "NULLABLE" },
      { "name": "state", "type": "STRING", "mode": "NULLABLE" },
      { "name": "balance", "type": "FLOAT", "mode": "NULLABLE" },
      { "name": "account", "type": "STRING", "mode": "NULLABLE" },
      { "name": "month", "type": "INTEGER", "mode": "NULLABLE" },
      { "name": "first_started", "type": "TIMESTAMP", "mode": "NULLABLE" },
      { "name": "i1_pred_label", "type": "STRING", "mode": "NULLABLE" },
      { "name": "c_msp", "type": "STRING", "mode": "NULLABLE", "description": "Confidence: Max Softmax Probability." },
      { "name": "c_marigin", "type": "STRING", "mode": "NULLABLE", "description": "Confidence: Marigin between max and the second biggest softmax probability." },
      { "name": "c_entropy", "type": "STRING", "mode": "NULLABLE", "description": "Confidence: Low entropy means foccused softmax distribution. High entropy means flat softmax distribution" },
      { "name": "i0_new_label", "type": "STRING", "mode": "NULLABLE" },
      { "name": "i1_true_label", "type": "STRING", "mode": "NULLABLE" },
      { "name": "status", "type": "STRING", "mode": "NULLABLE" },
      { "name": "last_updated", "type": "STRING", "mode": "NULLABLE" },
      { "name": "comment", "type": "STRING", "mode": "NULLABLE" }
    ]
  }
}
EOF
)

# 5. Generate the definition file and create the BQ table
# Set the path for the output JSON definition file
OUTPUT_JSON_PATH="$OUTPUT_DIR/${table_name}.json"

# Replace the __URI__ placeholder with the actual URI from the CSV file.
MODIFIED_JSON=$(echo "$JSON_TEMPLATE" | sed "s|__URI__|$uri|")

# Write the resulting JSON to the output file
echo "$MODIFIED_JSON" > "$OUTPUT_JSON_PATH"
echo "  -> Created definition file: $OUTPUT_JSON_PATH"

# Create the BigQuery external table
echo "Attempting to create or update BigQuery table: ${PROJECT_ID}:${DATASET_ID}.${table_name}"
echo "  -> Deleting table if it exists..."
bq rm -f -t "${PROJECT_ID}:${DATASET_ID}.${table_name}"
echo "  -> Creating table..."
bq mk --external_table_definition="$OUTPUT_JSON_PATH" --force=true "${PROJECT_ID}:${DATASET_ID}.${table_name}"

# Check if the bq command was successful
if [ $? -eq 0 ]; then
    echo "  -> Successfully created/updated BigQuery table: $table_name"
else
    echo "  -> Error: Failed to create BigQuery table. Please check your 'bq' configuration and permissions."
    exit 1
fi

echo "Script finished successfully."
