locals {
  generated_secrets = {
    k3s-join-token           = "shared"
    k3s-node-password-server = "shared"
    k3s-node-password-agent  = "shared"
  }

  # Values are added by hand or by scripts, never by Terraform.
  external_secrets = {
    cfbd-api-key            = "shared"
    cloudflare-tunnel-token = "shared"
    ci-cloudflare-api-token = "shared"
    ci-neon-api-key         = "shared"
    admin-token-test        = "test"
    admin-token-prod        = "prod"
    database-url-test       = "test"
    database-url-prod       = "prod"
  }
}

resource "google_secret_manager_secret" "this" {
  for_each = merge(local.generated_secrets, local.external_secrets)

  secret_id = each.key
  labels    = { env = each.value }

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

ephemeral "random_password" "generated" {
  for_each = local.generated_secrets

  length  = 48
  special = false
}

# Write-only, so the value reaches neither state nor plan files. Bump the version to rotate.
resource "google_secret_manager_secret_version" "generated" {
  for_each = local.generated_secrets

  secret                 = google_secret_manager_secret.this[each.key].id
  secret_data_wo         = ephemeral.random_password.generated[each.key].result
  secret_data_wo_version = 1
}
