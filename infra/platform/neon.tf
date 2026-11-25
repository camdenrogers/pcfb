resource "neon_project" "this" {
  for_each = toset(["test", "prod"])

  name          = "pcfb-${each.value}"
  org_id        = var.neon_org_id
  region_id     = "aws-us-east-2"
  pg_version    = 16
  database_name = "pcfb"
  database_user = "pcfb"

  # The Free plan's maximum history window.
  history_retention_seconds = 21600

  # Smallest compute, to stretch the Free plan's monthly CU-hours.
  primary_compute = {
    autoscaling_limit_min_cu = 0.25
    autoscaling_limit_max_cu = 0.25
  }

  lifecycle {
    prevent_destroy = true
  }
}
