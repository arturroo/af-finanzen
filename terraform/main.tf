# default_table_expiration_mslocals {
#     datasets    = { for key, value in var.dataset_names : key => value if contains(value.stages, [var.stage]), var.stage)}
# 
# }
# 


resource "google_bigquery_dataset" "dataset" {
    for_each    = var.dataset_names
    project     = var.project_id
    dataset_id  = try(each.value.name, each.key)
    description = try(each.value["description"], null)
    location    = try(each.value["location"], "europe-west6")
    delete_contents_on_destroy  = try(each.value["delete_contents_on_destroy"], false)
    default_table_expiration_ms = try(each.value["default_table_expiration_ms"], null)
}
