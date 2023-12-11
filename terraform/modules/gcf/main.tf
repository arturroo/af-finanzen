# AF20231209
# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2023, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz"]
# __license__ = "GPLv3"
# __version__ = "1.0.0"
# __maintainer__ = "Artur Fejklowicz"
# __status__ = "Production"

# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "gcf_source" {
  for_each        = var.cf_names
  type        = "zip"
  source_dir  = "${path.module}/../../../cloud_functions/${each.key}/"
  output_path = "${path.module}/zips/${each.key}.zip"
}

# Add source code zip to the Cloud Function's bucket (Cloud_function_bucket)
resource "google_storage_bucket_object" "zip" {
  for_each        = var.cf_names
  source       = data.archive_file.gcf_source[each.key].output_path
  content_type = "application/zip"
  name         = "${each.key}-${data.archive_file.gcf_source[each.key].output_md5}.zip"
  bucket       = var.gcf_bucket
  depends_on = [
    data.archive_file.gcf_source
  ]
}

# Create the Cloud function triggered by a `Finalize` event on the bucket
resource "google_cloudfunctions_function" "cloud_function" {
  for_each        = var.cf_names
  name                  = each.key
  description           = try(each.value["description"], "Cloud-function ${each.key} in project ${var.project_id}")
  runtime               = try(each.value["runtime"], "python312")
  project               = var.project_id
  region                = try(each.value["region"], "europe-west6")
  source_archive_bucket = var.gcf_bucket
  source_archive_object = google_storage_bucket_object.zip[each.key].name
  entry_point           = try(each.value["entry_point"], "main")
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = "projects/${var.project_id}/topics/ps-${replace(each.key, "cf-", "")}"
  }
  depends_on = [
    google_storage_bucket_object.zip
  ]
}