# Artur Fejklowicz 2024-06-28
resource "google_storage_bucket" "bucket" {
    for_each        = var.buckets
    project         = var.project_id
    name            = "${var.project_id}-${each.key}"
    location        = try(each.value["location"], "europe-west6")
    force_destroy   = try(each.value["force_destroy"], false)
    storage_class   = try(each.value["storage_class"], "STANDARD")
    uniform_bucket_level_access = try(each.value["uniform_bucket_level_access"], true)
    public_access_prevention = "enforced"
}

resource "google_bigquery_dataset" "dataset" {
    for_each    = var.datasets
    project     = var.project_id
    dataset_id  = each.key
    description = try(each.value["description"], null)
    location    = try(each.value["location"], "europe-west6")
    delete_contents_on_destroy  = try(each.value["delete_contents_on_destroy"], false)
    default_table_expiration_ms = try(each.value["default_table_expiration_ms"], null)
}

resource "google_bigquery_table" "internal_table" {
    for_each    = var.internal_tables
    project     = var.project_id
    dataset_id  = try(each.value["dataset_id"], null)
    # table_id    = try(each.value.name, each.key)
    table_id    = each.key
    description = try(each.value["description"], null)
    clustering  = try(each.value["clustering"], null)
    schema      = file(each.value["schema"])
    deletion_protection  = try(each.value["deletion_protection"], null)

    dynamic "time_partitioning" {
        for_each = try(each.value["time_partitioning"], null) != null ? [each.value["time_partitioning"]] : []
        content {
            type            = time_partitioning.value["type"]
            expiration_ms   = time_partitioning.value["expiration_ms"]
            field           = time_partitioning.value["field"]
            require_partition_filter    = time_partitioning.value["require_partition_filter"]
        }
    }

    dynamic "range_partitioning" {
        for_each = try(each.value["range_partitioning"], null) != null ? [each.value["range_partitioning"]] : []
        content {
            field = range_partitioning.value["field"]
            range {
                start       = range_partitioning.value["range"]["start"]
                end         = range_partitioning.value["range"]["end"]
                interval    = range_partitioning.value["range"]["interval"]
            }

        }
    }

    depends_on = [google_bigquery_dataset.dataset]
}


resource "google_bigquery_table" "external_table" {
    for_each    = var.external_tables
    project     = var.project_id
    dataset_id  = try(each.value["dataset_id"], null)
    table_id    = each.key
    description = try(each.value["description"], null)
    deletion_protection  = try(each.value["deletion_protection"], null)

    external_data_configuration {
        autodetect              = try(each.value["autodetect"], true)
        compression             = try(each.value["compression"], "NONE")
        ignore_unknown_values   = try(each.value["ignore_unknown_values"], false)
        max_bad_records         = try(each.value["max_bad_records"], 0)
        schema                  = try(each.value["schema"], null) != null ? file(each.value["schema"]) : null
        source_format           = try(each.value["source_format"], "CSV")
        source_uris             = each.value["source_uris"]

        dynamic "csv_options" {
            for_each = try(each.value["csv_options"], null) != null ? [each.value["csv_options"]] : []
            content {
                quote               = try(csv_options.value["quote"], "")
                allow_jagged_rows   = try(csv_options.value["allow_jagged_rows"], false)
                encoding            = try(csv_options.value["encoding"], "UTF-8") # The supported values are UTF-8 or ISO-8859-1
                field_delimiter     = try(csv_options.value["field_delimiter"], ",")
                skip_leading_rows   = try(csv_options.value["skip_leading_rows"], 0)
            }
        }

        dynamic "hive_partitioning_options" {
            for_each = try(each.value["hive_partitioning_options"], null) != null ? [each.value["hive_partitioning_options"]] : []
            content {
                mode                        = try(hive_partitioning_options.value["mode"], "AUTO")
                require_partition_filter    = try(hive_partitioning_options.value["require_partition_filter"], false)
                source_uri_prefix           = try(hive_partitioning_options.value["source_uri_prefix"], null)
            }
        }
    }
    depends_on = [google_bigquery_dataset.dataset]
}