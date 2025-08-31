# Zero-Touch ML Model Promotion: Building a Fully Automated Champion-Challenger Pipeline on GCP Vertex AI - Key Lessons. 

Moving a machine learning model from a research notebook to a fully automated production pipeline can be a daunting task. In this post, I'll share key insights from building an end-to-end MLOps system on Google Cloud's Vertex AI Pipelines to classify my financial transactions. The secret to success wasn't just about the model, but about deeply understanding how Kubeflow Pipelines (KFP) passes data—or "artifacts"—between steps.

### Our Champion vs. Challenger Pipeline Architecture

First, let's look at the high-level architecture. The training pipeline follows a robust "Champion vs. Challenger" design to ensure that only best model make it to production:

1.  **Data Prep:** It starts by creating a versioned "golden source" dataset in BigQuery and splitting it into train, validation, and test sets.
2.  **Train Challenger:** A new model (the "challenger") is trained on the data.
3.  **Register Challenger:** The challenger is registered in the Vertex AI Model Registry.
4.  **Fetch Champion:** The pipeline fetches the current production model (the "champion").
5.  **Evaluate Both:** Both models run batch predictions on the same test set, and their performance metrics are calculated.
6.  **Decide & Bless:** A dedicated component compares their metrics. If the challenger wins, it gets "blessed" by having the `production` alias assigned to it, officially making it the new champion.

### The Two Flavors of Pipeline Components

In KFP, you build pipelines by connecting components, and I used two types. Understanding the difference is key.

*   **Lightweight Components:** These are the easiest to get started with. They are essentially Python functions that KFP wraps for you. Passing artifacts between them is incredibly intuitive; you just pass the output of an upstream component as an argument to a downstream one, much like a standard Python function call: `downstream_op(input_artifact=upstream_op.outputs['my_artifact'])`.

*   **Custom Container Components:** For more complex steps requiring specific libraries or environments, you package your code in a Docker container. This provides maximum flexibility but introduces a new challenge for passing data.

### The Secret to Passing Artifacts to Custom Containers

You can't pass an artifact object directly to a custom container because it runs as a separate Python process in its own isolated environment. The key is to pass a *reference*.

Here's the workflow I used:
1.  In the pipeline definition, I passed the artifact's `.path` attribute as a command-line argument to my container component.
2.  Behind the scenes, Vertex AI works its magic. It mounts the Google Cloud Storage (GCS) URI associated with that artifact to a local filesystem path inside the running container.
3.  My Python script inside the container can now read the artifact's content from that local path.

This elegant mechanism allows you to seamlessly connect containerized steps. It's important to remember that an artifact can be a **directory with multiple files** (like a TensorFlow SavedModel) or just a **single file** (like a json file with evaluation metrics). This distinction becomes critical when handling outputs and metadata.

With a **folder-based artifact**, you can easily add metadata by simply writing a JSON file inside the artifact's output directory with the name that not corresponds with any artifacts file name. This is great because it allows you to pass rich, structured data to downstream components.
Like here saving registered model resource name to make it available for downstream components.
``` 
    metadata_file_path = Path(candidate_model.path) / "vertex_model_metadata.json"
    with open(metadata_file_path, 'w') as f:
        json.dump({"resourceName": full_resource_name}, f)
    print(f"Saved model metadata with resource name to {metadata_file_path}")
```
However, with a **single-file artifact**, you can't add metadata this way. The container's script must produce a single file that conforms to the artifact's type. The component definition itself has no direct access to what the container returns; to get a simple value out, you have to treat it as the return value of the entire component function, which isn't always ideal. This is why using folder-based artifacts is often a more flexible and powerful approach when you need to pass more than just a single file's content. Artifacts that are files are better to use with metadata as lightweight components like my evaluation metrics here:
```
    print(f"Saving evaluation metrics to {evaluation_metrics.path}")
    with open(evaluation_metrics.path, 'w') as f:
        json.dump(final_evaluation_metrics, f, indent=4)

    print(f"Adding metadata to artifact: max_f1_macro = {max_f1_macro}")
    evaluation_metrics.metadata["max_f1_macro"] = max_f1_macro
```
### The Rules of the Road: Artifact Immutability

KFP enforces some important rules about how you can interact with artifacts:

*   **Inputs are Immutable:** An artifact passed as an *input* to a component is read-only. You cannot change its URI or content within that downstream step.
*   **Outputs are Writable (Once):** You can only define the properties of an *output* artifact within the single component that produces it. A great example from my pipeline is pointing the `VertexModel` output artifact to the GCS URI where my trainer component saved the final `SavedModel` files.

### A Word of Caution on Pipeline Submission

This was a big "gotcha" for me. When you are in your main pipeline file (e.g., `pipeline_train.py`) and are defining the pipeline flow, you have limited access to an artifact's attributes. You can pass the whole artifact object to another component or pass its `.uri` or `.path` as a parameter.

However, if you try to access other attributes like `.metadata` (for example, to get the accuracy from a `ModelEvaluation` artifact) *at the pipeline definition level*, your pipeline will fail on submission. KFP mocks up these objects during compilation, and those deeper attributes aren't available yet.

**The Workaround:** The solution is to add another small, lightweight component. This component takes the evaluation artifact as its full input. Then, *inside* this new component's code, you can freely access `evaluation_artifact.metadata` and use those values to make decisions.

### Conclusion

Building a real MLOps pipeline on Vertex AI is a powerful way to automate your ML workflows. By understanding the nuances of how KFP handles artifacts—especially the differences between lightweight and containerized components and the lifecycle of artifact attributes—you can build robust, scalable, and maintainable systems that truly bring your models to life.
