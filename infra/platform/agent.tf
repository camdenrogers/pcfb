resource "google_compute_instance_template" "agent" {
  name_prefix  = "pcfb-agent-"
  machine_type = "e2-small"
  tags         = ["k3s-node"]
  labels       = local.labels

  disk {
    boot         = true
    source_image = var.node_image
    disk_type    = "pd-standard"
    disk_size_gb = 20
    labels       = local.labels
  }

  network_interface {
    subnetwork = google_compute_subnetwork.nodes.id

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
    email  = data.google_service_account.node["agent"].email
    scopes = ["cloud-platform"]
  }

  shielded_instance_config {
    enable_secure_boot = true
  }

  metadata = {
    enable-oslogin         = "TRUE"
    block-project-ssh-keys = "TRUE"
  }

  metadata_startup_script = local.startup_script["agent"]

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_instance_group_manager" "agent" {
  name               = "pcfb-agent"
  base_instance_name = "pcfb-agent"
  zone               = var.zone
  target_size        = 1

  version {
    instance_template = google_compute_instance_template.agent.self_link_unique
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
    google_compute_instance_group_manager.server,
  ]
}
