#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# --- Configuration ---
PROJECT_ID="af-finanzen"
DATASET_ID="monatsabschluss"
TABLE_INFO_FILE="transak.monatsabschluss.csv" # Uses the same CSV input
OUTPUT_TABLE_PREFIX="sankey_" # Prefix for the new tables

# Schema source JSON file
SCHEMA_JSON_FILE_PATH="$SCRIPT_DIR/../terraform/bq-schemas/monatsabschluss.sankey.json"

# Fixed Google Sheet details
FIXED_SHEET_RANGE="Sankey!A:D"
FIXED_SKIP_ROWS=1

# --- Helper function to check for jq ---
check_jq() {
    if ! command -v jq &> /dev/null
    then
        echo "Error: jq is not installed. Please install jq to proceed." >&2
        exit 1
    fi
}

# --- Main Script ---

# 1. Check for jq
check_jq

# 2. Prepare the schema from the JSON file
echo "Preparing schema definition from $SCHEMA_JSON_FILE_PATH..." >&2
if [ ! -f "$SCHEMA_JSON_FILE_PATH" ]; then
    echo "Error: Schema JSON file '$SCHEMA_JSON_FILE_PATH' not found." >&2
    exit 1
fi

SCHEMA_FIELDS_AS_JSON_ARRAY=$(jq -c '.' "$SCHEMA_JSON_FILE_PATH")

if [ -z "$SCHEMA_FIELDS_AS_JSON_ARRAY" ] || [ "$SCHEMA_FIELDS_AS_JSON_ARRAY" == "null" ] || [ "$SCHEMA_FIELDS_AS_JSON_ARRAY" == "[]" ]; then
    echo "Error: Could not read, parse, or schema is empty in $SCHEMA_JSON_FILE_PATH." >&2
    exit 1
fi
echo "Schema definition prepared successfully." >&2
echo "---" >&2

# 3. Check if the table info file exists
if [ ! -f "$TABLE_INFO_FILE" ]; then
    echo "Error: Table info file '$TABLE_INFO_FILE' not found." >&2
    exit 1
fi

# 4. Loop through the CSV and recreate tables
while IFS=, read -r old_table_name gsheet_url || [[ -n "$old_table_name" ]];
do
    # Trim whitespace
    old_table_name=$(echo "$old_table_name" | xargs)
    gsheet_url=$(echo "$gsheet_url" | xargs)

    if [ -z "$old_table_name" ] || [ -z "$gsheet_url" ]; then
        continue
    fi

    # Extract suffix (e.g. 202512 from revolut_abrechnung_202512)
    # Assumes format: prefix_YYYYMM. We take everything after the last underscore.
    table_suffix="${old_table_name##*_}"
    
    # Construct new table name
    new_table_name="${OUTPUT_TABLE_PREFIX}${table_suffix}"

    # FULL_TABLE_ID for messages
    LOGGING_FULL_TABLE_ID="$PROJECT_ID.$DATASET_ID.$new_table_name"
    # TABLE_ID_FOR_BQ_MK
    TABLE_ID_FOR_BQ_MK="$DATASET_ID.$new_table_name"

    echo "Processing table: $LOGGING_FULL_TABLE_ID" >&2
    echo "  Source GSheet: $gsheet_url" >&2
    echo "  Sheet Range: $FIXED_SHEET_RANGE" >&2

    # Delete the table if it exists
    # echo "  Attempting to delete table $LOGGING_FULL_TABLE_ID if it exists..." >&2
    bq rm -f -t "$TABLE_ID_FOR_BQ_MK" > /dev/null 2>&1

    # Create the external table definition file
    DEF_FILE_PATH="temp_sankey_def_${table_suffix}.json"
    
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
        echo "Error: Failed to create definition file: $DEF_FILE_PATH" >&2
        continue
    fi

    echo "  Creating table $new_table_name..." >&2
    bq mk --table --location=europe-west6 --external_table_definition="$DEF_FILE_PATH" "$TABLE_ID_FOR_BQ_MK"

    if [ $? -eq 0 ]; then
        echo "  -> Success: $new_table_name" >&2
    else
        echo "  -> Error: Failed to create $new_table_name" >&2
    fi

    # Clean up
    rm -f "$DEF_FILE_PATH"

done < "$TABLE_INFO_FILE"

echo "All Sankey tables processed." >&2
