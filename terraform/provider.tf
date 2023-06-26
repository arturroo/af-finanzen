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
    credentials = "~/gjk/af-terraform-12e75bbdc87a.json"
  }
}

provider "google" {
  credentials = file("~/gjk/af-finanzen-dfbb2d657482.json")
  project = "af-finanzen"
  region  = "europe-west6"
  zone    = "europe-west6b"
}

