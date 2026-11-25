terraform {
  required_version = ">= 1.11.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "8.12.0"
    }
    neon = {
      source  = "neondatabase/neon"
      version = "0.19.0-beta.4" # beta: installs only when pinned exactly
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "5.29.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone

  default_labels = local.labels
}

# Credentials come from NEON_API_KEY and CLOUDFLARE_API_TOKEN; scripts/tf.sh sets both.
provider "neon" {}

provider "cloudflare" {}

locals {
  labels = {
    app = "pcfb"
    env = "shared"
  }
}
