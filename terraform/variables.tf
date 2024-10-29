variable "project_id" {
    default = ""
}   

variable "sa_json_google" {
    type = string
    sensitive = true
}

variable "gsheet_id" {
    type = string
    sensitive = true
}

variable "buckets" {
    description = "Google Storage buckets"
    default = {
        "banks" = {
        }
        "gcf" = {
        }

    }
}

variable "gs_notifications" {
    description = "Google Storage Notifications"
    default = {
        "ubs" = {
            bucket = "banks"
            object_name_prefix = "ubs/raw"
            topic = "ps-transform-csv"
        }
    }
}

variable "datasets" {
    description = "BigQuery Datasets"
    default = {
        "banks" = {
            description = "Raw data from banks"
            max_time_travel_hours = 168
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
        "predictions" = {
            description = "Transak predictions. Models made by Artur Fejklowicz"
            dataset_id = "banks"
            schema = "bq-schemas/banks.predictions.json"
        }
    }
}

variable "external_tables" {
    description = "BigQuery external tables"
    default = {
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
                    quote               = "\""
                    skip_leading_rows   = 1
                }
                hive_partitioning_options = {
                    # 2023-ß7-02
                    # Error: googleapi: Error 400: Field amount has type parameters, but it is not allowed in external table., invalid
                    # because this field is financial data: type Numeric (Decimal) with precision and scale
                    # mode = "CUSTOM"
                    # source_uri_prefix = "gs://af-finanzen-banks/revolut/{account:String}/{month:String}"
                    # 2023-07-02
                    # In this case Schema from JSON file is respected but without parameters.
                    # So the column amount is Numeric but without scale and precision parameters
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
                    quote               = "\""
                    encoding            = "ISO-8859-1"
                    field_delimiter     = ";"
                    skip_leading_rows   = 1
                }
                hive_partitioning_options = {
                    mode = "CUSTOM"
                    source_uri_prefix = "gs://af-finanzen-banks/ubs/{Monat:String}"
                }

            }
        }
        # TODO Schama, Credentials
        # "revolut_mapping" = {
        #     description = "Transaction description to budget account mapping "
        #     dataset_id = "banks"
        #     external_data_configuration = {
        #         autodetect  = true
        #         source_format = "GOOGLE_SHEETS"
        #         source_uris = [
        #             "https://docs.google.com/spreadsheets/d/{gsheet_id}",
        #         ]
        #         google_sheets_options = {
        #             range = "revolut_mapping!G:K"
        #             skip_leading_rows = 1
        #         }
        #     }
        # }
        # "ubs_mapping" = {
        #     description = "Transaction description to budget account mapping"
        #     dataset_id = "banks"
        #     external_data_configuration = {
        #         autodetect  = true
        #         source_format = "GOOGLE_SHEETS"
        #         source_uris = [
        #             "https://docs.google.com/spreadsheets/d/{gsheet_id}",
        #         ]
        #         google_sheets_options = {
        #             range = "ubs_mapping!G:L"
        #             skip_leading_rows = 1
        #         }
        #     }
        # }
    }
}

variable "views" {
    description = "BigQuery external tables"
    default = {
        "ubs_v" = {
            description = "UBS transactions with datetime transformations"
            dataset_id = "banks"
            query_file = "bq-views/banks.ubs_v.sql"
        }
        "revolut_v" = {
            description = "Revolut transactions unique description indicator first_started"
            dataset_id = "banks"
            query_file = "bq-views/banks.revolut_v.sql"
        }
    }
}

variable "topics" {
    description = "PubSub Topics"
    default = {
        "ps-transform-csv" = {
            labels = {
                "publisher" = "gs"
            }
        }
    }
}

variable "subscriptions" {
    description = "PubSub Subscriptions"
    default = {
        "ps-transform-csv-sub-gcf" = {
            topic = "ps-transform-csv"
        }
        "ps-transform-csv-sub-debug" = {
            topic = "ps-transform-csv"
        }
    }
}

variable "bindings" {
  default = {
      "gs--ps-transform-csv" = {
          topic = "ps-transform-csv"
      }
  }
}

variable "cf_names" {
    description = "Google Cloud Functions"
    default = {
        "cf-transform-csv" = {
            labels = {
                "publisher" = "gs"
            }
            trigger_type = "pubsub"
        }
        "cf-predict-lr" = {
            labels = {
                # "publisher" = "gs"
            }
            trigger_type = "http"
        }
    }
}

