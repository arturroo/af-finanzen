variable "project_id" {
    default = "af-finanzen"
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
        "revolut" = {
            description = "Revolut transactions"
            dataset_id = "banks"
            external_data_configuration = {
                autodetect  = false
                schema      = "bq-schemas/banks.revolut.json"
                source_uris = [
                    "gs://af-finanzen-banks/revolut/m=202303/account-statement_2023-05-01_2023-06-21_en-gb_f79d3c.csv",
                ]

                csv_options = {
                    skip_leading_rows = 1
                }
                hive_partitioning_options = {
                    source_uri_prefix = "gs://af-finanzen-banks/revolut/"
                }

            }
        }
    }
}
