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
