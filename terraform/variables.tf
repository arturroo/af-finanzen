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
        "revolut" = {
            description = "Revolut transactions"
            dataset_id = "banks"
            external_data_configuration = {
                autodetect  = false
                schema      = "bq-schemas/banks.revolut.json"
                source_uris = [
                    "gs://af-finanzen-banks/revolut/*",
                ]

                csv_options = {
                    skip_leading_rows = 1
                }
                hive_partitioning_options = {
                    source_uri_prefix = "gs://af-finanzen-banks/revolut/"
                }

            }
        }
        "ubs" = {
            description = "UBS transactions"
            dataset_id = "banks"
            external_data_configuration = {
                autodetect  = false
                schema      = "bq-schemas/banks.ubs.json"
                source_uris = [
                    "gs://af-finanzen-banks/ubs/*",
                ]

                csv_options = {
                    encoding = "ISO-8859-1"
                    skip_leading_rows = 1
                }
                hive_partitioning_options = {
                    source_uri_prefix = "gs://af-finanzen-banks/ubs/"
                }

            }
        }
    }
}

