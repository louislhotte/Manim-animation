variable "servers" {
  type = number
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_security_group" "web" {
  name   = "web"
  vpc_id = aws_vpc.main.id
}

resource "aws_instance" "web" {
  count         = var.servers
  ami           = "ami-0f3a91c2"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public.id

  vpc_security_group_ids = [
    aws_security_group.web.id,
  ]
}

resource "aws_s3_bucket" "assets" {
  bucket_prefix = "acme-assets-"
}
