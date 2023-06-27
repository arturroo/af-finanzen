variable "project_id" {
    default = ""
}

variable "sa_json_google" {
    type = string
    sensitive = true
}

variable "dataset_names" {
    description = "BQ Datasets"
    default = {
        "revolut" = {
            description = "Revolut transactions"
        }
    }
}

variable "table_names" {
    description = "BQ Tables"
    default = {
        "transactions" = {
            description = "Revolut transactions"
            dataset_id = "revolut"
            schema = "bq-schemas/revolut.transactions.json"
        }
    }
}
