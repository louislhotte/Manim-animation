terraform {
  backend "s3" {
    bucket       = "acme-tfstate"
    key          = "prod.tfstate"
    region       = "eu-west-3"
    use_lockfile = true
  }
}
