locals {
  labels = { app = "pcfb", env = "shared" }
}

resource "helm_release" "argocd" {
  name             = "argocd"
  namespace        = "argocd"
  create_namespace = true
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "10.20.0"
  timeout          = 900

  values = [yamlencode({
    global         = { additionalLabels = local.labels }
    dex            = { enabled = false }
    notifications  = { enabled = false }
    applicationSet = { replicas = 0 }

    controller = { resources = { requests = { cpu = "50m", memory = "256Mi" }, limits = { memory = "768Mi" } } }
    server     = { resources = { requests = { cpu = "20m", memory = "64Mi" }, limits = { memory = "256Mi" } } }
    repoServer = { resources = { requests = { cpu = "20m", memory = "96Mi" }, limits = { memory = "512Mi" } } }
    redis      = { resources = { requests = { cpu = "10m", memory = "32Mi" }, limits = { memory = "128Mi" } } }
  })]
}
