terraform {
  backend "gcs" {
    bucket = "pcfb-platform-tfstate"
    prefix = "platform"
  }
}
