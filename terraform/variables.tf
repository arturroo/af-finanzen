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
        "banks" = {}
        "gcf" = {}
        "mlops" = {}
    }
}

variable "gs_notifications" {
    description = "Google Storage Notifications"
    default = {
        "ubs" = {
            bucket = "banks"
            object_name_prefix = "raw/ubs/"
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
        "shops" = {
            description = "Raw data from shops"
            max_time_travel_hours = 168
        }
        "analytics" = {
            description = "Output data for analytics"
            max_time_travel_hours = 168
        }
        "transak" = {
            description = "Transak project data"
            max_time_travel_hours = 168
        }
        "monatsabschluss" = {
            description = "Abrechnungen von Monaten"
            max_time_travel_hours = 168
        }    }
}

variable "internal_tables" {
    description = "BigQuery internal tables"
    default = {
        "revolut" = {
            description = "Revolut transactions internal table with transaction ID and one feature first_started"
            dataset_id = "banks"
            clustering = ["type", "state"]
            schema = "bq-schemas/banks.revolut.json"
            range_partitioning = {
                field = "month"
                range = {
                    start = 201801
                    end = 203801
                    interval = 1
                }
            }
            
        }
        "zak" = {
            description = "ZAK transactions"
            dataset_id = "banks"
            schema = "bq-schemas/banks.zak.json"
        }
        "i0_predictions" = {
            description = "Transak predictions. Iteration 0 of agile plan."
            dataset_id = "transak"
            schema = "bq-schemas/transak.i0_predictions.json"
        }
        "i1_predictions" = {
            description = "Transak predictions. Iteration 1 of agile plan."
            dataset_id = "transak"
            schema = "bq-schemas/transak.i1_predictions.json"
        }
        "i1_models" = {
            description = "Transak models metadata. Iteration 1 of agile plan."
            dataset_id = "transak"
            schema = "bq-schemas/transak.i1_models.json"
        }
        "i1_vectorizers" = {
            description = "Transak vectorizers or embeddings metadata. Iteration 1 of agile plan."
            dataset_id = "transak"
            schema = "bq-schemas/transak.i1_vectorizers.json"
        }
    }
}

variable "external_tables" {
    description = "BigQuery external tables"
    default = {
        "revolut_raw" = {
            description = "Revolut transactions"
            dataset_id = "banks"
            external_data_configuration = {
                autodetect  = false
                schema      = "bq-schemas/banks.revolut_raw.json"
                source_uris = [
                    "gs://af-finanzen-banks/revolut_raw/*",
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
                    source_uri_prefix = "gs://af-finanzen-banks/revolut_raw/"
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
    description = "BigQuery views"
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
        "sankey_v" = {
            description = "Diagram Sankey data"
            dataset_id = "analytics"
            query_file = "bq-views/analytics.sankey_v.sql"
        }
        # AF20250327 Problem with organization and gdrive, see Gemini Chat. Created manually.
        # "revolut_abrechnung_v" = {
        #     description = "Monatsabschluss revolut view"
        #     dataset_id = "monatsabschluss"
        #     query_file = "bq-views/monatsabschluss.revolut_abrechnung_v.sql"
        # }
        "i1_data_revolut_v" = {
            description = "Revolut transactions unique description indicator first_started. Iteration 1 of agile plan."
            dataset_id = "transak"
            query_file = "bq-views/transak.i1_data_revolut_v.sql"
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
        "cf-i0-predict-lr" = {
            labels = {
                # "publisher" = "gs"
            }
            trigger_type = "http"
        }
        "cf-pdfminions" = {
            labels = {
            }
            trigger_type = "http"
        }
        "cf-pdf2bq" = {
            labels = {
            }
            trigger_type = "http"
        }

    }
}

