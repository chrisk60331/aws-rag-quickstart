config {

}

plugin "terraform" {
  enabled = true
}

plugin "aws" {
  enabled = true
}

rule "terraform_required_version" {
  enabled = false
}