# Artur Fejklowicz 2024-06-28
resource "google_bigquery_dataset" "dataset" {
    for_each    = var.dataset_names
    project     = var.project_id
    # dataset_id  = try(each.value.name, each.key)
    dataset_id  = each.key
    description = try(each.value["description"], null)
    location    = try(each.value["location"], "europe-west6")
    delete_contents_on_destroy  = try(each.value["delete_contents_on_destroy"], false)
    default_table_expiration_ms = try(each.value["default_table_expiration_ms"], null)
}

resource "google_bigquery_table" "table" {
    for_each    = var.table_names
    project     = var.project_id
    dataset_id  = try(each.value["dataset_id"], null)
    # table_id    = try(each.value.name, each.key)
    table_id    = each.key
    description = try(each.value["description"], null)
    location    = try(each.value["location"], "europe-west6")
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
            field = time_partitioning.value["field"]
            range {
                start       = range_partitioning.value["range"]["start"]
                end         = range_partitioning.value["range"]["end"]
                interval    = range_partitioning.value["range"]["interval"]
            }

        }
    }

    depends_on = [google_bigquery_dataset.dataset]
}
