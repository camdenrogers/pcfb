output "registry" {
  value = "${google_artifact_registry_repository.images.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "zone" {
  value = var.zone
}

output "neon" {
  description = "Inputs for scripts/sync-secrets.sh. Contains no credentials."
  value = {
    for env, p in neon_project.this : env => {
      project_id = p.id
      branch_id  = p.branch.id
      host       = p.primary_compute.host
      role       = p.database_user
      database   = p.database_name
    }
  }
}

output "tunnel" {
  value = {
    account_id = var.cloudflare_account_id
    tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.main.id
  }
}
