resource "gitlab_group" "default" {
  name             = var.group_name
  path             = var.group_path
  parent_id        = var.parent_id
  visibility_level = var.visibility_level
  description      = "A group ${var.group_name}"
}
