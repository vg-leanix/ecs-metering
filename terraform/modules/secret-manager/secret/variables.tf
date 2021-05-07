variable "id" {
  description = "Amazon Resource Name (ARN) of the secret."
  type = string

}

variable "credentials" {
  default = {
    host = "demo-eu.leanix.net"
    token = ""
  }

  type = map(string)
}