#!/bin/bash

# This script reads a CSV file with table names and Google Sheet URIs,
# then generates a BigQuery external table definition JSON file for each entry.

# Configuration
INPUT_CSV="transak.monatsabschluss.csv"
OUTPUT_DIR="transak_i1/external_table_definitions"

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# JSON template for the external table definition.
# The __URI__ placeholder will be replaced with the actual URI from the CSV.
JSON_TEMPLATE=$(cat <<'EOF'
{
  "sourceFormat": "GOOGLE_SHEETS",
  "sourceUris": [
    "__URI__"
  ],
  "googleSheetsOptions": {
    "skipLeadingRows": 1,
    "range": "'Revolut Abrechnung'!A:T"
  },
  "schema": {
    "fields": [
      {
        "name": "tid",
        "type": "INTEGER",
        "mode": "NULLABLE"
      },
      {
        "name": "type",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "product",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "started",
        "type": "TIMESTAMP",
        "mode": "NULLABLE"
      },
      {
        "name": "completed",
        "type": "TIMESTAMP",
        "mode": "NULLABLE"
      },
      {
        "name": "description",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "amount",
        "type": "FLOAT",
        "mode": "NULLABLE"
      },
      {
        "name": "fee",
        "type": "FLOAT",
        "mode": "NULLABLE"
      },
      {
        "name": "currency",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "state",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "balance",
        "type": "FLOAT",
        "mode": "NULLABLE"
      },
      {
        "name": "account",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "month",
        "type": "INTEGER",
        "mode": "NULLABLE"
      },
      {
        "name": "first_started",
        "type": "TIMESTAMP",
        "mode": "NULLABLE"
      },
      {
        "name": "true_label",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "pred_label",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "i0_new_label",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "i1_true_label",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "status",
        "type": "STRING",
        "mode": "NULLABLE"
      },
      {
        "name": "comment",
        "type": "STRING",
        "mode": "NULLABLE"
      }
    ]
  }
}
EOF
)

# Ensure the input CSV file exists
if [ ! -f "$INPUT_CSV" ]; then
    echo "Error: Input file '$INPUT_CSV' not found."
    exit 1
fi

# Read the CSV file line by line
while IFS=',' read -r table_name uri || [ -n "$table_name" ]; do
    # Trim potential whitespace and handle carriage returns
    table_name=$(echo "$table_name" | tr -d '[:space:]')
    uri=$(echo "$uri" | tr -d '[:space:]')

    # Skip empty lines that might result from parsing
    if [ -z "$table_name" ]; then
        continue
    fi

    echo "Processing table: $table_name"

    # Set the path for the output JSON file
    OUTPUT_JSON_PATH="$OUTPUT_DIR/${table_name}.json"

    # Replace the __URI__ placeholder with the actual URI from the CSV file.
    # Using '|' as a delimiter for sed to avoid conflicts with '/' in the URI.
    MODIFIED_JSON=$(echo "$JSON_TEMPLATE" | sed "s|__URI__|$uri|")

    # Write the resulting JSON to the output file
    echo "$MODIFIED_JSON" > "$OUTPUT_JSON_PATH"

    echo "  -> Created definition file: $OUTPUT_JSON_PATH"
done < "$INPUT_CSV"

echo "Script finished successfully."

