# AF20231129
# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2023, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz"]
# __license__ = "GPLv3"
# __version__ = "1.0.0"
# __maintainer__ = "Artur Fejklowicz"
# __status__ = "Production"


resource "google_pubsub_topic" "topic" {
  for_each        = var.topics
  name = each.key
  project = var.project_id
  labels = try(each.value["labels"], {})
  # message_retention_duration = "86600s"

  message_storage_policy {
    allowed_persistence_regions = [
      "europe-west6",
    ]
  }
}

resource "google_pubsub_subscription" "subscription" {
  for_each        = var.subscriptions
  name  = "sb-${each.key}"
  topic = each.value["topic"]
  project = var.project_id

  labels = try(each.value["labels"], {})

  # 7d
  message_retention_duration = try(each.value["message_retention_duration"], "604800s")
  retain_acked_messages      = try(each.value["retain_acked_messages"], true)

  ack_deadline_seconds = try(each.value["ack_deadline_seconds"], 20)

  expiration_policy {
    ttl = "604800s"
  }
  retry_policy {
    minimum_backoff = "10s"
  }

  enable_message_ordering    = try(each.value["enable_message_ordering"], false)
}