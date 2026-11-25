resource "google_compute_network" "main" {
  name                    = "pcfb"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "nodes" {
  name          = "pcfb-nodes"
  network       = google_compute_network.main.id
  ip_cidr_range = "10.10.0.0/24"
}

resource "google_compute_address" "server" {
  name         = "pcfb-server-internal"
  address_type = "INTERNAL"
  subnetwork   = google_compute_subnetwork.nodes.id
  address      = "10.10.0.10"
}

# 35.235.240.0/20 is IAP's TCP forwarding range. There are no public ingress rules.
resource "google_compute_firewall" "iap_ssh" {
  name          = "pcfb-iap-ssh"
  network       = google_compute_network.main.id
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["k3s-node"]

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_firewall" "iap_apiserver" {
  name          = "pcfb-iap-apiserver"
  network       = google_compute_network.main.id
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["k3s-server"]

  allow {
    protocol = "tcp"
    ports    = ["6443"]
  }
}

# 6443 API server, 10250 kubelet, 8472 flannel VXLAN.
resource "google_compute_firewall" "node_to_node" {
  name        = "pcfb-node-to-node"
  network     = google_compute_network.main.id
  source_tags = ["k3s-node"]
  target_tags = ["k3s-node"]

  allow {
    protocol = "tcp"
    ports    = ["6443", "10250"]
  }

  allow {
    protocol = "udp"
    ports    = ["8472"]
  }
}
