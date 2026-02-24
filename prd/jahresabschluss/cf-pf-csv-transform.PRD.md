# PRD: Cloud Function cf-pf-csv-transform

## 1. Objective
To automate the ingestion and cleaning of PostFinance CSV transaction exports into Google BigQuery. This function acts as the "Bronze" layer processor, stripping bank-specific headers/footers and organizing data into a Hive-partitioned structure in GCS.

## 2. Technical Requirements

### 2.1 Framework & Environment
- **Runtime:** Python 3.10+ please check which is supported for pyptoject.toml https://docs.cloud.google.com/run/docs/runtimes/python-dependencies
- **Entry Point:** main (as a wrapper for start with traceback handling).
- **Dependency Management:** Use pyproject.toml (standardizing on PEP 517/518 as per latest GCP best practices) instead of 
equirements.txt.
- **Infrastructure:** Managed via Terraform (ariables.tf and module definitions).

### 2.2 Trigger
- **Event:** GCS Finalize (Triggered when a raw PostFinance CSV is uploaded to the landing zone). Similar to cf-transform-csv.

### 2.3 Logic Flow (The "Cleaner")
1. **Header Stripping:** Skip the first 6 lines of the PostFinance CSV (Metadata rows like "Datum von:", "Konto:", etc.).
2. **Footer Stripping:** Remove the "Disclaimer" and empty lines at the end of the file.
3. **Partitioning & Filename Normalization:**
    - Extract the month from the first transaction row.
    - Format: **YYYYMM** (Integer).
    - **Crucial:** The source filename (e.g., `export_bewegungen_...`) must be ignored.
4. **Output Path (GCS):**
    - Convention: `gs://{BUCKET_ID}/postfinance/month={YYYYMM}/pf_{YYYYMM}_transactions.csv`
    - Partition Key: `month` (Integer).
    - Filename includes the month for self-documentation and safety (idempotency).
5. **Encoding:** Handle `utf-8` or `windows-1252` as per source data requirements.

### 2.4 Error Handling & Logging
- Use google-cloud-logging for structured logs.
- Wrap start() in a main() function with a 60-second event age timeout (to prevent infinite retry loops).
- Include full traceback logging on failure.

## 3. Architecture Context
- This function strictly performs **Cleaning (ELT)**. 
- Business logic like splitting the Avisierungstext or generating 	id via FARM_FINGERPRINT is **RESERVED** for the BigQuery View (Silver Layer).

## 4. Coding Conventions
- Strictly follow the patterns in cf-i1-predict/main.py.
- No carats (^) in pyproject.toml versions; use precise versions.
