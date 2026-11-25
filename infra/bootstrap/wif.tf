resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"

  depends_on = [google_project_service.enabled]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "camdenrogers/pcfb"

  attribute_condition = "assertion.repository_id == '${var.github_repository_id}' && assertion.repository_owner_id == '${var.github_owner_id}'"

  # pull_request_target also runs on refs/heads/main, so "deploy" needs an explicit event allowlist.
  attribute_mapping = {
    "google.subject"    = "assertion.sub"
    "attribute.ci_role" = "assertion.ref == 'refs/heads/main' && assertion.event_name in ['push', 'workflow_dispatch'] ? 'deploy' : (assertion.event_name == 'pull_request' ? 'plan' : 'none')"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

locals {
  ci_principal_prefix = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.ci_role"
}

resource "google_service_account_iam_member" "planner_wif" {
  service_account_id = google_service_account.ci_planner.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "${local.ci_principal_prefix}/plan"
}

resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.ci_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "${local.ci_principal_prefix}/deploy"
}
