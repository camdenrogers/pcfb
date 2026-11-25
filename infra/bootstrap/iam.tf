resource "google_service_account" "ci_planner" {
  account_id   = "ci-planner"
  display_name = "GitHub Actions: terraform plan on pull requests"

  depends_on = [google_project_service.enabled]
}

resource "google_service_account" "ci_deployer" {
  account_id   = "ci-deployer"
  display_name = "GitHub Actions: image push and terraform apply on main"

  depends_on = [google_project_service.enabled]
}

# Node accounts live here so CI never needs to create service accounts or edit project IAM.
resource "google_service_account" "node" {
  for_each = toset(["server", "agent"])

  account_id   = "k3s-${each.value}"
  display_name = "k3s ${each.value} node"

  depends_on = [google_project_service.enabled]
}

resource "google_project_iam_member" "planner" {
  for_each = toset([
    "roles/viewer",
    "roles/iam.securityReviewer",
  ])

  project = var.project_id
  role    = each.value
  member  = google_service_account.ci_planner.member
}

resource "google_project_iam_member" "deployer" {
  for_each = toset([
    "roles/viewer",
    "roles/artifactregistry.admin",
    "roles/compute.admin",
    "roles/secretmanager.admin",
  ])

  project = var.project_id
  role    = each.value
  member  = google_service_account.ci_deployer.member
}

# Lets the deployer attach these two accounts to VMs, and no others.
resource "google_service_account_iam_member" "deployer_uses_node" {
  for_each = google_service_account.node

  service_account_id = each.value.name
  role               = "roles/iam.serviceAccountUser"
  member             = google_service_account.ci_deployer.member
}

# CI reads and writes only platform state. The bucket-level clause is for object listing.
locals {
  state_bucket_resource    = "projects/_/buckets/${google_storage_bucket.tfstate.name}"
  platform_state_condition = "resource.name == '${local.state_bucket_resource}' || resource.name.startsWith('${local.state_bucket_resource}/objects/platform/')"
}

resource "google_storage_bucket_iam_member" "planner_state" {
  bucket = google_storage_bucket.tfstate.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.ci_planner.member

  condition {
    title      = "platform-state-only"
    expression = local.platform_state_condition
  }
}

resource "google_storage_bucket_iam_member" "deployer_state" {
  bucket = google_storage_bucket.tfstate.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.ci_deployer.member

  condition {
    title      = "platform-state-only"
    expression = local.platform_state_condition
  }
}
