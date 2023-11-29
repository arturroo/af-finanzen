# AF20231129

data "google_storage_project_service_account" "gcs_account" {
}

resource "google_pubsub_topic_iam_binding" "binding" {
  for_each = var.bindings
  topic   = each.value["topic"]
  role    = "roles/pubsub.publisher"
  members = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
  project = var.project_id
}