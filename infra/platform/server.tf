resource "google_compute_disk" "k3s_state" {
  name   = "pcfb-k3s-state"
  type   = "pd-balanced"
  size   = 15
  labels = local.labels

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_compute_instance_template" "server" {
  name_prefix  = "pcfb-server-"
  machine_type = "e2-medium"
  tags         = ["k3s-node", "k3s-server"]
  labels       = local.labels

  disk {
    boot         = true
    source_image = var.node_image
    disk_type    = "pd-standard"
    disk_size_gb = 20
    labels       = local.labels
  }

  disk {
    source      = google_compute_disk.k3s_state.name
    device_name = "k3s-state"
    boot        = false
    auto_delete = false
    mode        = "READ_WRITE"
  }

  network_interface {
    subnetwork = google_compute_subnetwork.nodes.id
    network_ip = google_compute_address.server.address

    # Egress only; STANDARD tier includes a free monthly egress allowance.
    access_config {
      network_tier = "STANDARD"
    }
  }

  scheduling {
    provisioning_model          = "SPOT"
    preemptible                 = true
    automatic_restart           = false
    on_host_maintenance         = "TERMINATE"
    instance_termination_action = "STOP"
  }

  service_account {
    email  = data.google_service_account.node["server"].email
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot = true
  }

  metadata = {
    enable-oslogin         = "TRUE"
    block-project-ssh-keys = "TRUE"
  }

  metadata_startup_script = local.startup_script["server"]

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_instance_group_manager" "server" {
  name               = "pcfb-server"
  base_instance_name = "pcfb-server"
  zone               = var.zone
  target_size        = 1

  version {
    instance_template = google_compute_instance_template.server.self_link_unique
  }

  update_policy {
    type                  = "PROACTIVE"
    minimal_action        = "REPLACE"
    replacement_method    = "RECREATE"
    max_surge_fixed       = 0
    max_unavailable_fixed = 1
  }

  depends_on = [
    google_secret_manager_secret_iam_member.join_token,
    google_secret_manager_secret_iam_member.node_password,
    google_secret_manager_secret_version.generated,
  ]
}
