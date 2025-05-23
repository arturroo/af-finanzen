#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# --- Configuration ---
PROJECT_ID="af-finanzen"  # Replace with your Project ID
DATASET_ID="monatsabschluss"    # Replace with your Dataset ID
TABLE_INFO_FILE="transak.monatsabschluss.csv" # Your CSV with table_name,gsheet_url

# Schema source JSON file
SCHEMA_JSON_FILE_PATH="$SCRIPT_DIR/../terraform/bq-schemas/monatsabschluss.revolut_abrechnung.json"

# Fixed Google Sheet details
FIXED_SHEET_RANGE="Revolut Abrechnung!A:T" # UPDATED to A:T, and removed extra shell quotes
FIXED_SKIP_ROWS=1

# --- Helper function to check for jq ---
check_jq() {
    if ! command -v jq &> /dev/null
    then
        echo "Error: jq is not installed. Please install jq to proceed." >&2
        echo "For example: sudo apt-get install jq OR brew install jq" >&2
        exit 1
    fi
}

# --- Main Script ---

# 1. Check for jq
check_jq

# 2. Prepare the schema from the JSON file
echo "Preparing schema definition from $SCHEMA_JSON_FILE_PATH..." >&2 # Diagnostic to stderr
if [ ! -f "$SCHEMA_JSON_FILE_PATH" ]; then
    echo "Error: Schema JSON file '$SCHEMA_JSON_FILE_PATH' not found." >&2
    exit 1
fi

SCHEMA_FIELDS_AS_JSON_ARRAY=$(jq -c '.' "$SCHEMA_JSON_FILE_PATH")

if [ -z "$SCHEMA_FIELDS_AS_JSON_ARRAY" ] || [ "$SCHEMA_FIELDS_AS_JSON_ARRAY" == "null" ] || [ "$SCHEMA_FIELDS_AS_JSON_ARRAY" == "[]" ]; then
    echo "Error: Could not read, parse, or schema is empty in $SCHEMA_JSON_FILE_PATH." >&2
    echo "jq output: $SCHEMA_FIELDS_AS_JSON_ARRAY" >&2
    exit 1
fi
echo "Schema definition prepared successfully." >&2
# For debugging the schema string itself (optional, send to stderr)
# echo "Schema JSON: ${SCHEMA_FIELDS_AS_JSON_ARRAY}" >&2
echo "---" >&2


# 3. Check if the table info file exists
if [ ! -f "$TABLE_INFO_FILE" ]; then
    echo "Error: Table info file '$TABLE_INFO_FILE' not found." >&2
    exit 1
fi

# 4. Loop through the CSV and recreate tables
while IFS=, read -r bq_table_name gsheet_url || [[ -n "$bq_table_name" ]]; # Process last line even if no trailing newline
do
    # Trim potential leading/trailing whitespace
    bq_table_name=$(echo "$bq_table_name" | xargs)
    gsheet_url=$(echo "$gsheet_url" | xargs)

    if [ -z "$bq_table_name" ] || [ -z "$gsheet_url" ]; then
        if [ -n "$bq_table_name" ] || [ -n "$gsheet_url" ]; then # only print if not a completely empty line
             echo "Skipping line with missing data: table_name='${bq_table_name}', url='${gsheet_url}'" >&2
        fi
        continue
    fi

    # FULL_TABLE_ID for messages and deletion still includes project for clarity in logs
    LOGGING_FULL_TABLE_ID="$PROJECT_ID.$DATASET_ID.$bq_table_name"
    # TABLE_ID_FOR_BQ_MK for the bq mk command itself, without project ID
    TABLE_ID_FOR_BQ_MK="$DATASET_ID.$bq_table_name"

    echo "Processing table: $LOGGING_FULL_TABLE_ID" >&2
    echo "  Source GSheet: $gsheet_url" >&2
    echo "  Sheet Range: $FIXED_SHEET_RANGE" >&2
    echo "  Skip Rows: $FIXED_SKIP_ROWS" >&2

    # Delete the table if it exists (for recreation)
    echo "  Attempting to delete table $LOGGING_FULL_TABLE_ID if it exists..." >&2
    echo bq rm -f -t "$TABLE_ID_FOR_BQ_MK"
    bq rm -f -t "$TABLE_ID_FOR_BQ_MK"

    # Create the external table definition file (Full Table Resource)
    DEF_FILE_PATH="temp_external_table_def.json"
    echo "  Creating temporary definition file (Full Table Resource): $DEF_FILE_PATH" >&2
    cat <<EOF > "$DEF_FILE_PATH"
{
    "sourceFormat": "GOOGLE_SHEETS",
    "sourceUris": ["$gsheet_url"],
    "schema": {
      "fields": $SCHEMA_FIELDS_AS_JSON_ARRAY
    },
    "googleSheetsOptions": {
      "range": "$FIXED_SHEET_RANGE",
      "skipLeadingRows": $FIXED_SKIP_ROWS
    },
    "ignoreUnknownValues": false
}
EOF

    if [ ! -s "$DEF_FILE_PATH" ]; then
        echo "Error: Failed to create or temporary definition file is empty: $DEF_FILE_PATH" >&2
        echo "-----------------------------------------------------" >&2
        continue # Skip to next table
    fi

    echo "  Creating table $LOGGING_FULL_TABLE_ID using definition file..." >&2
    # For debugging the exact command (optional):
    # echo "  Executing: bq mk --table --external_table_definition=\"$DEF_FILE_PATH\" \"$TABLE_ID_FOR_BQ_MK\"" >&2
    # Updated command for full table resource definition:
    # echo "  Executing: bq mk --table \"$DEF_FILE_PATH\"" >&2

    echo bq mk --table --location=europe-west6 --external_table_definition="$DEF_FILE_PATH" "$TABLE_ID_FOR_BQ_MK"
    bq mk --table --location=europe-west6 --external_table_definition="$DEF_FILE_PATH" "$TABLE_ID_FOR_BQ_MK"

    if [ $? -eq 0 ]; then
        echo "Successfully recreated table: $bq_table_name" >&2
    else
        echo "Error recreating table: $bq_table_name (bq mk command failed using $DEF_FILE_PATH)" >&2
    fi

    # Clean up the temporary definition file
    rm -f "$DEF_FILE_PATH"
    echo "-----------------------------------------------------" >&2
done < "$TABLE_INFO_FILE"

echo "All tables processed." >&2