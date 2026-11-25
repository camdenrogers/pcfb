locals {
  startup_common = templatefile("${path.module}/scripts/common.sh.tftpl", {
    project_id          = var.project_id
    registry_host       = "${var.region}-docker.pkg.dev"
    k3s_url             = "https://github.com/k3s-io/k3s/releases/download/${urlencode(var.k3s_version)}/k3s"
    k3s_sha256          = var.k3s_sha256
    credential_provider = file("${path.module}/scripts/gcr-credential-provider.sh")
  })

  startup_script = {
    for role in ["server", "agent"] : role => join("\n", [
      local.startup_common,
      templatefile("${path.module}/scripts/${role}.sh.tftpl", {
        server_ip = google_compute_address.server.address
      }),
    ])
  }
}
