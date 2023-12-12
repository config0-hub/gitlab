resource "gitlab_project" "main" {
  name             = var.project_name
  visibility_level = var.visibility_level
  namespace_id     = var.group_id
}

#output "token" {
#   sensitive = true
#   value     = gitlab_project.main.runners_token
#}
