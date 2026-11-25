# On a from-scratch rebuild, move this file aside for the first apply, then restore it and run
# `terraform init -migrate-state`.
terraform {
  backend "gcs" {
    bucket = "pcfb-platform-tfstate"
    prefix = "bootstrap"
  }
}
