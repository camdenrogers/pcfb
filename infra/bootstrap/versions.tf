terraform {
  required_version = ">= 1.11.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "8.12.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  default_labels = {
    app = "pcfb"
    env = "shared"
  }
}

# The budgets API rejects user credentials that carry no quota project.
provider "google" {
  alias                 = "billing"
  project               = var.project_id
  billing_project       = var.project_id
  user_project_override = true
}
