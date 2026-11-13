terraform {
  backend "s3" {
    bucket       = "acme-tfstate"
    key          = "web.tfstate"
    region       = "eu-west-3"
    use_lockfile = true
  }
}
