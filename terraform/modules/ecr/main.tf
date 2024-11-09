terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "5.6.2"
    }
  }
}

resource "aws_ecr_repository" "aws_ecr_repository" {
  name = var.repo_name
}

resource "docker_image" "docker_image" {
  name = "${replace(var.proxy_endpoint, "https://", "")}/${var.repo_name}:latest"
  build {
    context = var.build_context
    target  = var.build_target
  }
}

resource "docker_registry_image" "media-handler" {
  name          = docker_image.docker_image.name
  keep_remotely = true
}

output "image_url" {
  value = "${var.proxy_endpoint}/${var.repo_name}:latest"
}