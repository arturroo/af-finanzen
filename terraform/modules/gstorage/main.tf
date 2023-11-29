# AF20231125

resource "google_storage_bucket" "bucket" {
    for_each        = var.buckets
    default_event_based_hold = try(each.value["default_event_based_hold"], false)
    force_destroy   = try(each.value["force_destroy"], false)
    labels          = try(each.value["labels"], {})
    location        = try(each.value["location"], "europe-west6")
    name            = "${var.project_id}-${each.key}"
    project         = var.project_id
    public_access_prevention = "enforced"
    requester_pays  = try(each.value["requester_pays"], false)
    storage_class   = try(each.value["storage_class"], "STANDARD")
    uniform_bucket_level_access = try(each.value["uniform_bucket_level_access"], true)

    versioning {
          enabled = try(each.value["versioning"], true)
    }
}

resource "google_storage_notification" "notification" {
  for_each       = var.gs_notifications
  bucket         = "${var.project_id}-${each.value["bucket"]}"
  object_name_prefix = each.value["object_name_prefix"]
  payload_format = "JSON_API_V1"
  topic          = each.value["topic"]
  event_types    = ["OBJECT_FINALIZE"]

  # custom_attributes = {
  #   new-attribute = "new-attribute-value"
  # }
  # depends_on = [google_pubsub_topic_iam_binding.binding]
}

// Enable notifications by giving the correct IAM permission to the unique service account.


#
# // End enabling notifications
#
# resource "google_pubsub_topic" "topic" {
#   name = "default_topic"
# }