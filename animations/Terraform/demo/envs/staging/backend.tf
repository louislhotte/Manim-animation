terraform {
  backend "s3" {
    bucket       = "acme-tfstate"
    key          = "staging.tfstate"
    region       = "eu-west-3"
    use_lockfile = true
  }
}
