variable "project_id" {
  type    = string
  default = "pcfb-platform"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

# Pinned rather than an image family, so a new Debian release can't replace VMs on an unrelated apply.
variable "node_image" {
  type    = string
  default = "projects/debian-cloud/global/images/debian-13-trixie-v20261116"
}

variable "k3s_version" {
  type    = string
  default = "v1.37.2+k3s1"
}

variable "k3s_sha256" {
  description = "SHA-256 of the amd64 k3s binary for k3s_version."
  type        = string
  default     = "265b3ee6a3198ef14033c63ef46cbb32370d83795199fb6d1b01f21575eddbda"
}

variable "domain" {
  type    = string
  default = "probablycollegefootball.com"
}

variable "cloudflare_account_id" {
  type    = string
  default = "dfcda9769fc858da77ba57cd920bd74d"
}

variable "cloudflare_zone_id" {
  type    = string
  default = "694402affe6f3d219f230259a2aa5c0c"
}

variable "neon_org_id" {
  type    = string
  default = "org-cold-thunder-68765830"
}

variable "public_envs" {
  description = "Environments that get a tunnel route and DNS record."
  type        = set(string)
  default     = ["test"]
}
