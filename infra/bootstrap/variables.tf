variable "project_id" {
  type    = string
  default = "pcfb-platform"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "billing_account" {
  description = "Billing account ID for the budget. Pass with TF_VAR_billing_account."
  type        = string
}

variable "github_repository_id" {
  description = "Numeric ID of camdenrogers/pcfb. Unlike the name, it can't be re-registered by someone else."
  type        = string
  default     = "1470980475"
}

variable "github_owner_id" {
  type    = string
  default = "15388985"
}
