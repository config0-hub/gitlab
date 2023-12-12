terraform {
  required_version = ">= 1.1.0"
  required_providers {
    gitlab = {
      source  = "gitlabhq/gitlab"
      version = "~> 15.9.0"
    }
  }
}
