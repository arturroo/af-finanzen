# Projekt Transak - Iteration 1

Artur Fejklowicz


## Automated Revolut transaction classifier with a Wide & Deep Model on Vertex AI Pipelines

This project demonstrates a professional, end-to-end MLOps pipeline for classifying personal Revolut transactions. It uses a custom Two Towers: Wide & Deep model built with TensorFlow/Keras and is orchestrated entirely on Google Cloud using Vertex AI Pipelines with custom container.

## Final Pipeline Architecture

The final pipeline consists of four containerized components that automate the entire process from data ingestion to conditional model registration.

![Final Pipeline Graph](media/Screenshot_2025-07-01_002218.png)

---

## Key Features & Technical Highlights

This project goes beyond a simple training script and implements a full MLOps workflow, showcasing several advanced techniques:

* **Wide & Deep Architecture:** The model combines the "memorization" power of a wide linear model with the "generalization" power of a deep neural network. The wide path uses a `HashedCrossing` of the transaction `type` and `description` to learn specific rules, while the deep path learns complex patterns from a rich set of engineered features.

* **Advanced Feature Engineering:** All preprocessing is handled by custom Keras layers, making the model self-contained and eliminating training-serving skew.
    * **`CyclicalFeature` Layer:** A custom subclassed layer to transform date components (month, day, weekday) into `sin`/`cos` representations, allowing the model to understand cyclical patterns.
    * **`AmountFeatures` Layer:** A custom layer to generate both a `log1p` transformed amount (to handle skewed distributions) and a binary sign feature.
    * **Text & Categorical Embeddings:** Uses `TextVectorization` with n-grams for text descriptions and `StringLookup` for categorical features, both followed by `Embedding` layers to create dense, meaningful representations.

* **Containerized MLOps Pipeline:**
    * The entire workflow is defined as a series of components using the **Kubeflow Pipelines (KFP) SDK**.
    * Each step runs inside a **custom Docker container**, ensuring a reproducible and isolated environment.
    * The pipeline is orchestrated and executed on **Vertex AI Pipelines**, showcasing a modern, serverless approach to MLOps.
    * The pipeline includes **conditional logic** to only register the model if its accuracy on the test set surpasses a predefined threshold.

---

## Results

The final model shows a significant improvement over previous baselines, demonstrating the power of the Wide & Deep architecture and detailed feature engineering.

* **Final Test Accuracy:** 89%
* **Macro Average F1-Score:** 0.76 (a +0.08 improvement, showing much better performance on rare classes)

![Final Confusion Matrix](media/cm.png)

---

## Project Structure

The project is organized into distinct Python packages to ensure a clean separation of concerns, a best practice for production ML systems.

```
├── common/             # Shared utility functions (e.g., df2dataset).
├── tasks/              # Container entrypoint scripts for each pipeline step.
│   ├── data_prep/      # Loads the data and outputs three data sets as artifacts.
│   ├── evaluation/     # Outputs model evaluation. With dirty hack to load Keras model.
│   ├── register/       # Conditional logic to upload the model to Vertex AI Model Registry.
│   └── trainer/        # Core model definition and custom Keras layers.
├── pipeline/           # KFP component launchers and the main pipeline definition.
│   └── components/
├── .gcloudignore       # Instructs gcloud CLI to ignore unnecessary files for builds.
├── Dockerfile          # Instructions to build the custom training & evaluation container.
└── pyproject.toml      # Project dependencies and configuration.
```

---

## How to Run

This project is designed to be run as a Vertex AI Pipeline.

1.  **Set Up Environment:**
    * Ensure the Google Cloud SDK is installed and configured.
    * Create a local Python virtual environment and install dependencies from `pyproject.toml` using `uv pip install .[all]`.

2.  **Build the Container:**
    * From the project root, run the following command to build the custom container and push it to Artifact Registry:
        ```bash
        gcloud builds submit --region="europe-west1" --tag="europe-west6-docker.pkg.dev/af-finanzen/af-finanzen-mlops/transak-i1-train-predict:latest" .
        ```

3.  **Run the Pipeline:**
    * Set the required environment variables in your terminal (`VERTEX_PROJECT_ID`, `VERTEX_REGION`, `VERTEX_BUCKET`, `VERTEX_TENSORBOARD_NAME`).
    * Execute the pipeline script from the project root:
        ```bash
        python -m pipeline.pipeline submit
        ```

