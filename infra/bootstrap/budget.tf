data "google_project" "this" {
  project_id = var.project_id
}

# Kept in bootstrap so CI needs no access to the billing account.
resource "google_billing_budget" "monthly" {
  provider = google.billing

  billing_account = var.billing_account
  display_name    = "pcfb-monthly"

  budget_filter {
    projects        = ["projects/${data.google_project.this.number}"]
    calendar_period = "MONTH"
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "30"
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.9, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }

  depends_on = [google_project_service.enabled]
}
