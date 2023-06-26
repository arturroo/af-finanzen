variable "project_id" {
    default = ""
}


variable "dataset_names" {
    description = "BQ Datasets"
    default = {
        "revolut" = {
            # project     = "af-finanzen"
            description = "Revolut transactions"
            #location    = "europe-west6"
            #delete_contents_on_destroy  = false
            #default_table_expiration_ms = null
        }
    }
}
