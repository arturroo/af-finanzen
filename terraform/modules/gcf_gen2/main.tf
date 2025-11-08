# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "gcf_source" {
  for_each    = var.cf_names
  type        = "zip"
  source_dir  = "${path.module}/../../../cloud_functions/${each.key}/"
  output_path = "${path.module}/zips/${each.key}.zip"
}

# Add source code zip to the Cloud Function's bucket
resource "google_storage_bucket_object" "zip" {
  for_each     = var.cf_names
  source       = data.archive_file.gcf_source[each.key].output_path
  content_type = "application/zip"
  name         = "${each.key}-${data.archive_file.gcf_source[each.key].output_md5}.zip"
  bucket       = var.gcf_bucket
  depends_on = [
    data.archive_file.gcf_source
  ]
}

# Create the Gen2 Cloud function triggered by Pub/Sub
resource "google_cloudfunctions2_function" "cf_pubsub_gen2" {
  for_each = { for k, v in var.cf_names : k => v if v.trigger_type == "pubsub" }

  name        = try(each.value["name"], each.key)
  project     = var.project_id
  location    = try(each.value["region"], "europe-west6")
  description = try(each.value["description"], "Cloud-function Gen2 ${each.key} in project ${var.project_id}")

  build_config {
    runtime     = try(each.value["runtime"], "python312")
    entry_point = try(each.value["entry_point"], "main")
    source {
      storage_source {
        bucket = var.gcf_bucket
        object = google_storage_bucket_object.zip[each.key].name
      }
    }
  }

  service_config {
    max_instance_count = try(each.value["max_instances"], 5)
    min_instance_count = try(each.value["min_instances"], 0)
    available_memory   = try(each.value["memory"], "256Mi")
    timeout_seconds    = try(each.value["timeout"], 60)
    environment_variables = merge(
      try(each.value["env"], {})
    )
  }

  event_trigger {
    trigger_region = try(each.value["region"], "europe-west6")
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = "projects/${var.project_id}/topics/ps-${replace(each.key, "cf-", "")}"
    retry_policy   = "RETRY_POLICY_RETRY"
  }
}
