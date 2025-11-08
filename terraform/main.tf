# Artur Fejklowicz 2024-06-28
# __author__ = "Artur Fejklowicz"
# __copyright__ = "Copyright 2023, The AF Finanzen Project"
# __credits__ = ["Artur Fejklowicz"]
# __license__ = "GPLv3"
# __version__ = "1.0.0"
# __maintainer__ = "Artur Fejklowicz"
# __status__ = "Production"

module "gstorage" {
    source = "./modules/gstorage"
    project_id = var.project_id
    buckets = var.buckets
    gs_notifications = var.gs_notifications
}

module "pubsub" {
    source = "./modules/pubsub"
    project_id = var.project_id
    topics = var.topics
    subscriptions = var.subscriptions
}

module "iam" {
    source = "./modules/iam"
    project_id = var.project_id
    bindings = var.bindings
}

module "gcf" {
    source = "./modules/gcf"
    project_id = var.project_id
    cf_names = { for k, v in var.cf_names : k => v if try(v.gen, 1) == 1 }
    gcf_bucket = module.gstorage.gcf_bucket

    depends_on = [
        module.gstorage,
        module.pubsub
    ]
}

module "gcf_gen2" {
    source = "./modules/gcf_gen2"
    project_id = var.project_id
    cf_names = { for k, v in var.cf_names : k => v if try(v.gen, 1) == 2 }
    gcf_bucket = module.gstorage.gcf_bucket

    depends_on = [
        module.gstorage,
        module.pubsub
    ]
}


resource "google_bigquery_dataset" "dataset" {
    for_each    = var.datasets
    project     = var.project_id
    dataset_id  = each.key
    description = try(each.value["description"], null)
    location    = try(each.value["location"], "europe-west6")
    delete_contents_on_destroy  = try(each.value["delete_contents_on_destroy"], false)
    default_table_expiration_ms = try(each.value["default_table_expiration_ms"], null)
    max_time_travel_hours = try(each.value["max_time_travel_hours"], 168)
}

resource "google_bigquery_table" "internal_table" {
    for_each    = var.internal_tables
    project     = var.project_id
    dataset_id  = try(each.value["dataset_id"], null)
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
        autodetect              = try(each.value["external_data_configuration"]["autodetect"], true)
        compression             = try(each.value["external_data_configuration"]["compression"], "NONE")
        ignore_unknown_values   = try(each.value["external_data_configuration"]["ignore_unknown_values"], false)
        max_bad_records         = try(each.value["external_data_configuration"]["max_bad_records"], 0)
        schema                  = try(each.value["external_data_configuration"]["schema"], null) != null ? file(each.value["external_data_configuration"]["schema"]) : null
        source_format           = try(each.value["external_data_configuration"]["source_format"], "CSV")
        source_uris             = try(each.value["external_data_configuration"]["source_uris"], [])

        dynamic "csv_options" {
            for_each = try(each.value["external_data_configuration"]["csv_options"], null) != null ? [each.value["external_data_configuration"]["csv_options"]] : []
            content {
                quote               = try(csv_options.value["quote"], "")
                allow_jagged_rows   = try(csv_options.value["allow_jagged_rows"], false)
                encoding            = try(csv_options.value["encoding"], "UTF-8") # The supported values are UTF-8 or ISO-8859-1
                field_delimiter     = try(csv_options.value["field_delimiter"], ",")
                skip_leading_rows   = try(csv_options.value["skip_leading_rows"], 0)
            }
        }

        dynamic "hive_partitioning_options" {
            for_each = try(each.value["external_data_configuration"]["hive_partitioning_options"], null) != null ? [each.value["external_data_configuration"]["hive_partitioning_options"]] : []
            content {
                mode                        = try(hive_partitioning_options.value["mode"], "AUTO")
                require_partition_filter    = try(hive_partitioning_options.value["require_partition_filter"], false)
                source_uri_prefix           = try(hive_partitioning_options.value["source_uri_prefix"], null)
            }
        }

        dynamic "google_sheets_options" {
            for_each = try(each.value["external_data_configuration"]["google_sheets_options"], null) != null ? [each.value["external_data_configuration"]["google_sheets_options"]] : []
            content {
                range = try(google_sheets_options.value["range"], null)
                skip_leading_rows = try(google_sheets_options.value["skip_leading_rows"], 0)
            }
        }
    }
    depends_on = [google_bigquery_dataset.dataset]
}


resource "google_bigquery_table" "view" {
    for_each    = var.views
    project     = var.project_id
    dataset_id  = try(each.value["dataset_id"], null)
    table_id    = each.key
    description = try(each.value["description"], null)
    deletion_protection  = try(each.value["deletion_protection"], null)

    view {
        query = templatefile(each.value["query_file"], {project_id = var.project_id})
        use_legacy_sql = try(each.value["use_legacy_sql"], false)
    }
    depends_on = [google_bigquery_dataset.dataset]
}

resource "google_vertex_ai_tensorboard" "default" {
  display_name = "vertex-ai-tensorboard-transak"
  project      = var.project_id
  region       = "europe-west6"
}