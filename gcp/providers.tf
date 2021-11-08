provider "google" {
  project     = var.project
  credentials = file(var.service_account_credentials_file_location)
  region      = var.region
  zone        = var.zone
}

provider "google-beta" {
  project     = var.project
  credentials = file(var.service_account_credentials_file_location)
  region      = var.region
  zone        = var.zone
}