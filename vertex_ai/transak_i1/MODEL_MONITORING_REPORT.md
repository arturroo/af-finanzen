# Vertex AI Model Monitoring Report

**Date:** 2025-11-08

This document summarizes the findings from an investigation into the Vertex AI Model Monitoring service for the `transak-i1-train-model`.

## 1. Monitoring Configuration

An existing model monitor instance was investigated.

*   **Monitor Resource Name:** `projects/819397114258/locations/europe-west6/modelMonitors/3345048623229435904`
*   **Monitored Model:** `transak-i1-train-model` (Version 36)
*   **Monitoring Type:** This is a **Model Monitor** configured directly on a model in the Vertex AI Model Registry, not a `ModelDeploymentMonitoringJob` attached to a live endpoint. 
*   **Description:** There are 2 objectives:
    *   **Data Drift:** It is designed for monitoring drift against input data. It is configured to compare distribution of input features between:
        *   **Base:** Data split "train" from the pipeline train that produced model with alias "production" in model registry
        *   **Current Input:** Result of the batch prediction from 202508 pipeline predict run. In production monitoring, the monitoring should be run on last month  input data or take month as parameter. 
    * **Prediction Drift:** Throws error because unidentified yet problem in schema of predictions csv files by last and current prediction runs. It has to be skipped in new Monitoring. We can do this in new iteration.
    * **Training data source:** gs://af-finanzen-mlops/pipelines/transak-i1-train/819397114258/transak-i1-train-20250831130933/data-splits-op_4986344605592059904/train_data.csv 
    * **Model schema:** 
      {
        "featureFields": [
          {
            "name": "type",
            "dataType": "categorical",
            "repeated": false
          },
          {
            "name": "description",
            "dataType": "categorical",
            "repeated": false
          }
        ],
        "predictionFields": [
          {
            "name": "i1_true_label_id",
            "dataType": "integer",
            "repeated": false
          }
        ],
        "groundTruthFields": []
      }

### Monitored Features & Drift Configuration

| Feature       | Type        | Metric      | Alert Threshold |
|---------------|-------------|-------------|-----------------|
| `description` | Categorical | L-Infinity  | 0.3             |
| `type`        | Categorical | L-Infinity  | 0.3             |

---

## 2. CLI Interaction (`gcloud`)

An attempt was made to inspect the model monitor using the `gcloud` command-line tool.

*   **Finding:** No working command was found in the installed SDK version (`539.0.0`) to describe the `modelMonitors` resource directly.
*   **Commands Attempted:**
    *   `gcloud ai model-monitors describe ...` (Invalid command)
    *   `gcloud beta ai model-monitors describe ...` (Invalid command)
    *   `gcloud vertex ai model-monitors describe ...` (Invalid command)
    *   `gcloud ai model-monitoring-jobs describe ...` (Incorrect resource type, returned NOT_FOUND)
*   **Conclusion:** This specific resource type appears to be accessible only via the Google Cloud Console UI or direct API calls at this time, as CLI support is not apparent.

---

## 3. Monitoring Run Analysis

A specific test run was investigated to understand the output structure and results.

*   **Run Name:** `test run monitoring`
*   **Run Time:** Sep 11, 2025, 1:16:02 PM
*   **Monitoring Job ID:** `957859345746362368`
*   **Output Directory:** `gs://af-finanzen-mlops/monitoring/transak_i1/model_monitoring/3345048623229435904`

### Run Results

The contents of the output directory were inspected, specifically the `anomalies.json` file, which summarizes the drift calculations.

**File Content: `anomalies.json`**
```json
{
  "baseline": {
    "feature": [
      {
        "name": "description",
        "type": "BYTES",
        "driftComparator": { "infinityNorm": { "threshold": 0.3 } }
      },
      {
        "name": "type",
        "type": "BYTES",
        "driftComparator": { "infinityNorm": { "threshold": 0.3 } }
      }
    ]
  },
  "driftSkewInfo": [
    {
      "path": { "step": [ "description" ] },
      "driftMeasurements": [ { "type": "L_INFTY", "value": 0.281059, "threshold": 0.3 } ]
    },
    {
      "path": { "step": [ "type" ] },
      "driftMeasurements": [ { "type": "L_INFTY", "value": 0.18768, "threshold": 0.3 } ]
    }
  ]
}
```

### Analysis Conclusion

| Feature       | Calculated Drift | Alert Threshold | Drift Detected? |
|---------------|------------------|-----------------|-----------------|
| `description` | 0.281059         | 0.3             | **No**          |
| `type`        | 0.18768          | 0.3             | **No**          |

The calculated drift for both monitored features was below the configured alert threshold of `0.3`. Therefore, **no drift was detected** in this run.

---

## 4. Next Steps for Production
*   **Design production monitoring:** We need to discuss several steps foccusing only on DataDrift monitoring, because it worked in static onetime run. We need to design:
    *   **What:** to use as Monitoring configuration?
        *   Terraform
        *   Manual configuration in GCP Wen console
        *   Some Python program executed locally
        *   Requirement: configuration should be saved somewhere in a file and should be possible for automatic deployment, but for now GitHub Actions are out of scope, but we will have them available in next iterations.  
    *   **How:** to integrate the monitoring in the current setup so it is all automatic. We need for each integration 3 possible solutions with theirs pros and cons. There are 2 integration we need to think about:
        *   How to call monitoring from pipeline predict
        *   how to call train pipeline from monitoring
    *   **Alerting:** How to do alering - we need 3 solutions with their pros and cons. Requirements: email alert to Artur if one of number over threshold and train pipeline executed.
