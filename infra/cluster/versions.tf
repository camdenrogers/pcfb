terraform {
  required_version = ">= 1.11.0"

  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "3.3.0"
    }
  }
}

# Needs scripts/tunnel.sh running. Applied locally, so CI holds no cluster credentials.
provider "helm" {
  kubernetes = {
    config_path = pathexpand(var.kubeconfig)
  }
}
