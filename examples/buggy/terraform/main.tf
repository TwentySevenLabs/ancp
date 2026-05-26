terraform {
  required_version = ">= 1.6"
}

resource "null_resource" "broken" {
  triggers = {
    value = "missing brace"
}
