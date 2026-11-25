output "state_bucket" {
  value = google_storage_bucket.tfstate.name
}

output "wif_provider" {
  value = google_iam_workload_identity_pool_provider.github.name
}

output "ci_planner_email" {
  value = google_service_account.ci_planner.email
}

output "ci_deployer_email" {
  value = google_service_account.ci_deployer.email
}

output "node_service_accounts" {
  value = { for k, sa in google_service_account.node : k => sa.email }
}
