variable "bedrock_image_uri" {
  default = ".dkr.ecr.us-east-1.amazonaws.com/cvos/bedrock:latest"
}

variable "opensearch_image_uri" {
  default = ".dkr.ecr.us-east-1.amazonaws.com/cvos/opensearch:latest"
}

variable "ecs_opensearch_image_uri" {
  default = ".dkr.ecr.us-east-1.amazonaws.com/cvos/ecsopensearch:latest"
}

variable "region_name" {
  default = "us-east-1"
}

variable "env_suffix" {
  description = "suffix to show env tier (nonprod, prod)"
  type        = string
  default = "dev"
}
