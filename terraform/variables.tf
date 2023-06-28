variable "project_id" {
    default = ""
}

variable "sa_json_google" {
    type = string
    sensitive = true
}

variable "buckets" {
    description = "Google Storage buckets"
    default = {
        "banks" = {
        }
    }
}


variable "datasets" {
    description = "BigQuery Datasets"
    default = {
        "banks" = {
            description = "Raw data from banks"
        }
    }
}

variable "internal_tables" {
    description = "BigQuery internal tables"
    default = {
        # "revolut" = {
        #     description = "Revolut transactions"
        #     dataset_id = "banks"
        #     schema = "bq-schemas/banks.revolut.json"
        # }
    }
}

variable "external_tables" {
    description = "BigQuery external tables"
    default = {
        # "ubs" = {
        #     description = "UBS transactions"
        #     dataset_id = "banks"
        #     schema = "bq-schemas/banks.ubs.json"
        # }
    }
}
