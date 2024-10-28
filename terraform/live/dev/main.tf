provider "aws" {
  region = var.region_name
  profile = "default"
}

locals {
  app_name           = "aoss-qa-${var.env_suffix}"
  opensearch_index   = "opensearch-index-${local.app_name}"
  availability_zones = {1: "${var.region_name}a", 2: "${var.region_name}b", 3: "${var.region_name}c"}
  vpc_cidr_block     = "10.0.0.0/22"
}

module "lambda_bedrock" {
  source = "../../modules/lambda"
  image_uri                  = var.bedrock_image_uri
  app_name                   = local.app_name
  env_name                   = var.env_suffix
  security_group_ids         = [module.vpc.main_vpc_security_group_id]
  subnet_ids                 = module.vpc.main_vpc_subnet_ids
  env_vars = {
      AOSS_URL = module.opensearch.opensearch_endpoint
      AOSS_PORT = 443
      INDEX_NAME = local.opensearch_index
      BEDROCK_ENDPOINT = "https://bedrock-runtime.${var.region_name}.amazonaws.com"
    }
  function_name = "bedrock"
  policy_actions = [
    "bedrock:*",
    "ec2:CreateNetworkInterface",
    "ec2:DescribeNetworkInterfaces",
    "ec2:DescribeSubnets",
    "ec2:DeleteNetworkInterface",
    "ec2:AssignPrivateIpAddresses",
    "ec2:UnassignPrivateIpAddresses",
    "ec2:DescribeSecurityGroups",
    "ec2:DescribeSubnets",
    "ec2:DescribeVpcs",
  ]
}

module "lambda_opensearch" {
  source = "../../modules/lambda"

  image_uri                  = var.opensearch_image_uri
  app_name                   = local.app_name
  env_name                   = var.env_suffix
  security_group_ids         = [module.vpc.main_vpc_security_group_id]
  subnet_ids                 = module.vpc.main_vpc_subnet_ids
  env_vars = {
      AOSS_URL = module.opensearch.opensearch_endpoint
      AOSS_PORT = 443
      INDEX_NAME = local.opensearch_index
      BEDROCK_ENDPOINT = "https://bedrock-runtime.${var.region_name}.amazonaws.com"
      S3_BUCKET = "${local.app_name}-data-bucket"
    }
  function_name = "opensearch"
  policy_actions = [
    "bedrock:*",
    "elasticsearch:*",
    "s3:GetObject",
    "ec2:CreateNetworkInterface",
    "ec2:DescribeNetworkInterfaces",
    "ec2:DescribeSubnets",
    "ec2:DeleteNetworkInterface",
    "ec2:AssignPrivateIpAddresses",
    "ec2:UnassignPrivateIpAddresses",
    "ec2:DescribeSecurityGroups",
    "ec2:DescribeSubnets",
    "ec2:DescribeVpcs",
  ]
}

module "opensearch" {
  source             = "../../modules/opensearch"
  app_name           = local.app_name
  engine_version     = "OpenSearch_2.13"
  instance_type      = "t3.small.search"
  instance_count     = 1
  security_group_ids = [module.vpc.main_vpc_security_group_id]
  subnet_ids         = module.vpc.main_vpc_subnet_ids
  vpc_id             = module.vpc.main_vpc_id
}

module "vpc" {
  source             = "../../modules/vpc"
  app_name           = local.app_name
  availability_zones = local.availability_zones
  vpc_cidr_block     = local.vpc_cidr_block
  region_name        = var.region_name
}

module "ecs" {
  source = "../../modules/ecs"
  app_name = local.app_name
  environment = var.env_suffix
  security_group_id = module.vpc.main_vpc_security_group_id
  subnets = module.vpc.main_vpc_subnet_ids
  desired_instance_count = 1
  docker_image_url = var.ecs_opensearch_image_uri
  opensearch_url = module.opensearch.opensearch_endpoint
  opensearch_index = local.opensearch_index
  bedrock_endpoint = "https://bedrock-runtime.${var.region_name}.amazonaws.com"
  region_name = var.region_name
  opensearch_port = 443
  s3_bucket = "${local.app_name}-data-bucket"
}