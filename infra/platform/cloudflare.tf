locals {
  hostnames = {
    test = "test.${var.domain}"
    prod = var.domain
  }
}

# Without a tunnel_secret Cloudflare generates one, so it never enters Terraform state.
resource "cloudflare_zero_trust_tunnel_cloudflared" "main" {
  account_id = var.cloudflare_account_id
  name       = "pcfb"
  config_src = "cloudflare"
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "main" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.main.id

  config = {
    ingress = concat(
      [for env in sort(var.public_envs) : {
        hostname = local.hostnames[env]
        service  = "http://frontend.pcfb-${env}.svc.cluster.local:80"
      }],
      [{ service = "http_status:404" }],
    )
  }
}

resource "cloudflare_dns_record" "app" {
  for_each = var.public_envs

  zone_id = var.cloudflare_zone_id
  name    = local.hostnames[each.value]
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.main.id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
}
