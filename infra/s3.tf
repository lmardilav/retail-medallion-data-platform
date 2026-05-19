resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-bronze"
}

resource "aws_s3_bucket" "silver" {
  bucket = "${var.project_name}-silver"
}

resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-gold"
}