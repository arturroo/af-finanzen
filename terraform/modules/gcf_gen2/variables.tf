variable "project_id" {
  description = "The ID of the project in which the resource belongs."
}

variable "cf_names" {
    description = "Google Cloud Functions Gen2"
}

variable "gcf_bucket" {
    description = "Name of the GCS bucket for Cloud Functions source code"
}
