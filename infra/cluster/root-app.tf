resource "helm_release" "root_app" {
  name       = "root-app"
  namespace  = helm_release.argocd.namespace
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argocd-apps"
  version    = "2.0.10"

  values = [yamlencode({
    applications = {
      root = {
        namespace        = "argocd"
        additionalLabels = local.labels
        project          = "default"
        source = {
          repoURL        = var.repo_url
          targetRevision = "main"
          path           = "deploy/argocd/apps"
        }
        destination = {
          server    = "https://kubernetes.default.svc"
          namespace = "argocd"
        }
        syncPolicy = {
          automated = { prune = true, selfHeal = true }
        }
      }
    }
  })]
}
