output "topics" {
  description = "The created Pub/Sub topics."
  value       = google_pubsub_topic.topic
}
