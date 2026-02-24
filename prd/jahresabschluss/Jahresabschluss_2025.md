# 2025 Year Close-Up: Project Status & Roadmap

## Objective
The goal is to finalize the **2025 Year Close-Up** to gain a holistic view of financial health and set precise budget boundaries for **2026**. This involves consolidating data from Revolut, UBS, and PostFinance into BigQuery for visualization in Looker Studio.

## Current Status (as of 2026-01-27)
*   **Revolut & UBS Data:** Fully integrated. The `monatsabschluss.sankey_v` view already unions all 12 months of 2025 data from BigQuery.
*   **Looker Studio:** A new report is connected to `sankey_v`, ready for visual analysis.
*   **The "Gap":** PostFinance data (Fixed Costs like Rent, SERAFE, subscriptions) is currently missing.
*   **Breakthrough (PostFinance CSV):** Found a way to export high-detail CSVs from the E-Finance Web Portal.
    *   **How to export:** Log in to PostFinance E-Finance -> Transactions -> **Anzeige einstellen** -> Check **"Details im Avisierungstext anzeigen"** -> Apply -> Download CSV.
    *   **Result:** The CSV now includes the "Mitteilung" (e.g., "MAZDA", "HAUS AM SEE") inside the `Avisierungstext` column, allowing for automated classification without PDF processing.

## Next Steps

### 1. 2025 Historical Data (Jahresabschluss) - "Hub & Spoke" Strategy
*   **Strategy:** Focus on the **Main Account (HUB)** first. This is where salary arrives and fixed costs are paid. Savings accounts (Spokes) are secondary unless they pay external bills.
*   **Action:** Export all 2025 CSVs for the Main Account using the "Details" setting.
*   **Action:** Use a local PowerShell script to merge and clean headers/footers for a one-time BigQuery upload.

### 2. 2026 Automation (New Cloud Function)
*   **Action:** Implement a new Cloud Function `cf-pf-csv-transform` to handle monthly PostFinance CSV uploads.
*   **Design:** 
    *   Triggered by GCS upload.
    *   Cleans PF-specific headers/disclaimers.
    *   Partitions by `month` as an **Integer (YYYYMM)** (e.g., 202601) for cost and performance efficiency.
    *   Saves to a Hive-partitioned structure (`gs://.../month=YYYYMM/...`).
    *   **Language:** Keep column names as `month` (KISS) to maintain consistency across the project.

### 3. SQL View Update (The "Virtual TID" Strategy)
*   **Action:** Create a "Master 2025" view (or update `sankey_v`) that includes the new PostFinance data.
*   **Implementation:** 
    *   Keep the raw CSV data intact in the external table.
    *   Perform the string splitting of `Avisierungstext` in the **BigQuery View**.
    *   Calculate a stable `tid` using `FARM_FINGERPRINT` in the view, mirroring the Revolut approach for maximum flexibility.

### 4. Looker Studio Dashboarding
*   **Page 1 (Summary):** Total 2025 Spending.
*   **Page 2 (The CFO Page):** The "Avg vs. Max" table for categories like "PK Leben" to define 2026 boundaries.
*   **Page 3 (Trends):** A Stacked Column Chart to see the monthly flow.
