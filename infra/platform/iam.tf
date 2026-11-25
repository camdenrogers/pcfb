data "google_service_account" "node" {
  for_each   = toset(["server", "agent"])
  account_id = "k3s-${each.value}"
}

resource "google_secret_manager_secret_iam_member" "join_token" {
  for_each = data.google_service_account.node

  secret_id = google_secret_manager_secret.this["k3s-join-token"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = each.value.member
}

resource "google_secret_manager_secret_iam_member" "node_password" {
  for_each = data.google_service_account.node

  secret_id = google_secret_manager_secret.this["k3s-node-password-${each.key}"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = each.value.member
}

resource "google_artifact_registry_repository_iam_member" "node_pull" {
  for_each = data.google_service_account.node

  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.reader"
  member     = each.value.member
}

# External Secrets runs only on the server node and uses its attached account, so no key is needed.
# The CI tokens are left out on purpose.
resource "google_secret_manager_secret_iam_member" "external_secrets" {
  for_each = toset([
    "cfbd-api-key",
    "cloudflare-tunnel-token",
    "admin-token-test",
    "admin-token-prod",
    "database-url-test",
    "database-url-prod",
  ])

  secret_id = google_secret_manager_secret.this[each.value].id
  role      = "roles/secretmanager.secretAccessor"
  member    = data.google_service_account.node["server"].member
}

data "google_service_account" "ci_planner" {
  account_id = "ci-planner"
}

# Provider credentials that plans on pull requests need. The deployer reads them as secretmanager.admin.
resource "google_secret_manager_secret_iam_member" "planner_tokens" {
  for_each = toset(["ci-cloudflare-api-token", "ci-neon-api-key"])

  secret_id = google_secret_manager_secret.this[each.value].id
  role      = "roles/secretmanager.secretAccessor"
  member    = data.google_service_account.ci_planner.member
}
