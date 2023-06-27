terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.51.0"
    }
  }
  backend "gcs" {
    bucket  = "af-terraform-states"
    prefix  = "af-finanzen"
  }
}

provider "google" {
  credentials = file(var.sa_json_google)
  project = "af-finanzen"
  region  = "europe-west6"
  zone    = "europe-west6b"
}

