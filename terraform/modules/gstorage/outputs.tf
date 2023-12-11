output "gcf_bucket" {
  value = google_storage_bucket.bucket["gcf"].name
}