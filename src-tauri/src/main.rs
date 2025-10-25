// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod db_manager;

use db_manager::{DatabaseManager, LoginResponse, SupplierScore, ScoreRecord, Criteria, Supplier, SupplierUpdate, ListItemThreeFields, ListItemSingleField, SupplierResponsibles, RiskSupplier};

/// Comando Tauri para validar login
#[tauri::command]
fn validate_login(username: String, password: String) -> Result<LoginResponse, String> {
    DatabaseManager::validate_login(username, password)
}

/// Comando Tauri para listar usuários (debug)
#[tauri::command]
fn list_users() -> Result<Vec<(String, String)>, String> {
    DatabaseManager::list_all_users()
}

/// Comando Tauri para obter total de fornecedores
#[tauri::command]
fn get_total_suppliers() -> Result<i64, String> {
    DatabaseManager::get_total_suppliers()
}

/// Comando Tauri para obter total de avaliações
#[tauri::command]
fn get_total_evaluations() -> Result<i64, String> {
    DatabaseManager::get_total_evaluations()
}

/// Comando Tauri para obter média de score
#[tauri::command]
fn get_average_score() -> Result<f64, String> {
    DatabaseManager::get_average_score()
}

/// Comando Tauri para obter total de usuários
#[tauri::command]
fn get_total_users() -> Result<i64, String> {
    DatabaseManager::get_total_users()
}

/// Comando Tauri para buscar fornecedores (legado - retorna JSON)
#[tauri::command]
fn search_suppliers_legacy(query: String) -> Result<Vec<serde_json::Value>, String> {
    DatabaseManager::search_suppliers_legacy(query)
}

/// Comando Tauri para buscar fornecedores (usado pela aba Score)
#[tauri::command]
fn search_suppliers(query: String) -> Result<Vec<Supplier>, String> {
    DatabaseManager::search_suppliers(query)
}

/// Comando Tauri para buscar fornecedores (novo - retorna Supplier struct)
#[tauri::command]
fn search_suppliers_data(query: String) -> Result<Vec<Supplier>, String> {
    DatabaseManager::search_suppliers(query)
}

/// Comando Tauri para obter todos os fornecedores por status
#[tauri::command]
fn get_all_suppliers_by_status(include_inactive: bool) -> Result<Vec<Supplier>, String> {
    DatabaseManager::get_all_suppliers_by_status(include_inactive)
}

/// Comando Tauri para obter dados de um fornecedor
#[tauri::command]
fn get_supplier_data(supplier_id: String) -> Result<Option<Supplier>, String> {
    DatabaseManager::get_supplier(supplier_id)
}

/// Comando Tauri para atualizar dados de fornecedor
#[tauri::command]
fn update_supplier_data(supplier: SupplierUpdate) -> Result<(), String> {
    DatabaseManager::update_supplier(supplier)
}

/// Comando Tauri para criar um novo fornecedor
#[tauri::command]
fn create_supplier(supplier: SupplierUpdate) -> Result<(), String> {
    println!("\n🎯 [TAURI COMMAND] create_supplier chamado");
    println!("📦 Dados recebidos: {:?}", supplier);
    let result = DatabaseManager::create_supplier(supplier);
    match &result {
        Ok(_) => println!("✅ [TAURI COMMAND] Fornecedor criado com sucesso"),
        Err(e) => println!("❌ [TAURI COMMAND] Erro: {}", e),
    }
    result
}

/// Comando Tauri para verificar se um PO já existe
#[tauri::command]
fn check_po_exists(po: String, current_supplier_id: String) -> Result<Option<Supplier>, String> {
    DatabaseManager::check_po_exists(&po, &current_supplier_id)
}

/// Comando Tauri para verificar o schema da tabela
#[tauri::command]
fn check_table_schema() -> Result<(), String> {
    DatabaseManager::check_table_schema()
}

/// Comando Tauri para debug da tabela
#[tauri::command]
fn debug_table() -> Result<String, String> {
    DatabaseManager::debug_supplier_table()
}

/// Comando Tauri para obter todos os usuários
#[tauri::command]
fn get_all_users() -> Result<Vec<serde_json::Value>, String> {
    DatabaseManager::get_all_users()
}

/// Comando Tauri para criar usuário
#[tauri::command]
fn create_user(
    name: String,
    wwid: String,
    privilege: String,
    status: String,
    password: String,
    otif: i32,
    nil: i32,
    pickup: i32,
    package: i32,
) -> Result<i64, String> {
    DatabaseManager::create_user(name, wwid, privilege, status, password, otif, nil, pickup, package)
}

/// Comando Tauri para verificar se WWID já existe
#[tauri::command]
fn check_wwid_exists(wwid: String) -> Result<bool, String> {
    DatabaseManager::check_wwid_exists(wwid)
}

/// Comando Tauri para atualizar usuário
#[tauri::command]
fn update_user(
    user_id: i32,
    name: String,
    wwid: String,
    privilege: String,
    status: String,
    password: Option<String>,
    otif: i32,
    nil: i32,
    pickup: i32,
    package: i32,
) -> Result<(), String> {
    DatabaseManager::update_user(user_id, name, wwid, privilege, status, password, otif, nil, pickup, package)
}

/// Comando Tauri para excluir usuário
#[tauri::command]
fn delete_user(user_id: i32) -> Result<(), String> {
    DatabaseManager::delete_user(user_id)
}

/// Comando Tauri para buscar senha de usuário
#[tauri::command]
fn get_user_password(user_id: i32) -> Result<String, String> {
    DatabaseManager::get_user_password(user_id)
}

/// Comando Tauri para contar usuários pendentes
#[tauri::command]
fn count_pending_users() -> Result<i32, String> {
    DatabaseManager::count_pending_users()
}

/// Comando Tauri para buscar usuários pendentes
#[tauri::command]
fn get_pending_users() -> Result<Vec<serde_json::Value>, String> {
    DatabaseManager::get_pending_users()
}

/// Comando Tauri para atualizar status de usuário
#[tauri::command]
fn update_user_status(user_id: i32, status: String) -> Result<(), String> {
    DatabaseManager::update_user_status(user_id, status)
}

/// Comando Tauri para buscar scores de fornecedores
#[tauri::command]
fn get_supplier_scores(supplier_ids: Vec<String>, month: i32, year: i32) -> Result<Vec<SupplierScore>, String> {
    DatabaseManager::get_supplier_scores(supplier_ids, month, year)
}

/// Comando Tauri para buscar todos os registros de score de um fornecedor
#[tauri::command]
fn get_supplier_score_records(supplier_id: String) -> Result<Vec<ScoreRecord>, String> {
    DatabaseManager::get_supplier_score_records(supplier_id)
}

/// Comando Tauri para salvar score de fornecedor
#[tauri::command]
fn save_supplier_score(
    supplier_id: String,
    supplier_name: String,
    month: i32,
    year: i32,
    otif_score: Option<String>,
    nil_score: Option<String>,
    pickup_score: Option<String>,
    package_score: Option<String>,
    total_score: Option<String>,
    comments: Option<String>,
    user_name: String,
    user_wwid: String,
) -> Result<String, String> {
    DatabaseManager::save_supplier_score(
        supplier_id,
        supplier_name,
        month,
        year,
        otif_score,
        nil_score,
        pickup_score,
        package_score,
        total_score,
        comments,
        user_name,
        user_wwid,
    )
}

/// Comando Tauri para buscar critérios de avaliação
#[tauri::command]
fn get_criteria() -> Result<Vec<Criteria>, String> {
    DatabaseManager::get_criteria()
}

/// Comando Tauri para buscar o valor do target
#[tauri::command]
fn get_target() -> Result<f64, String> {
    DatabaseManager::get_target()
}

/// Comando Tauri para atualizar critérios de avaliação
#[tauri::command]
fn update_criteria(criteria: Vec<Criteria>) -> Result<(), String> {
    DatabaseManager::update_criteria(criteria)
}

/// Comando Tauri para buscar lista de planners
#[tauri::command]
fn get_planners() -> Result<Vec<String>, String> {
    DatabaseManager::get_planners()
}

/// Comando Tauri para buscar opções de continuity
#[tauri::command]
fn get_continuity_options() -> Result<Vec<String>, String> {
    DatabaseManager::get_continuity_options()
}

/// Comando Tauri para buscar opções de sourcing
#[tauri::command]
fn get_sourcing_options() -> Result<Vec<String>, String> {
    DatabaseManager::get_sourcing_options()
}

/// Comando Tauri para buscar opções de SQIE
#[tauri::command]
fn get_sqie_options() -> Result<Vec<String>, String> {
    DatabaseManager::get_sqie_options()
}

/// Comando Tauri para buscar business units
#[tauri::command]
fn get_business_units() -> Result<Vec<String>, String> {
    DatabaseManager::get_business_units()
}

/// Comando Tauri para buscar categorias
#[tauri::command]
fn get_categories() -> Result<Vec<String>, String> {
    DatabaseManager::get_categories()
}

/// Comando Tauri para buscar fornecedores em risco
#[tauri::command]
fn get_suppliers_at_risk(year: i32, target: f64) -> Result<Vec<RiskSupplier>, String> {
    DatabaseManager::get_suppliers_at_risk(year, target)
}

// ========== LISTS MANAGEMENT COMMANDS ==========

/// Comando para obter itens de SQIE
#[tauri::command]
fn get_sqie_list() -> Result<Vec<ListItemThreeFields>, String> {
    DatabaseManager::get_list_items_three_fields("sqie_table")
}

/// Comando para adicionar item em SQIE
#[tauri::command]
fn add_sqie_item(item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::add_list_item_three_fields("sqie_table", item)
}

/// Comando para atualizar item em SQIE
#[tauri::command]
fn update_sqie_item(old_name: String, item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::update_list_item_three_fields("sqie_table", &old_name, item)
}

/// Comando para deletar item em SQIE
#[tauri::command]
fn delete_sqie_item(name: String) -> Result<(), String> {
    DatabaseManager::delete_list_item_three_fields("sqie_table", &name)
}

/// Comando para obter itens de Continuity
#[tauri::command]
fn get_continuity_list() -> Result<Vec<ListItemThreeFields>, String> {
    DatabaseManager::get_list_items_three_fields("continuity_table")
}

/// Comando para adicionar item em Continuity
#[tauri::command]
fn add_continuity_item(item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::add_list_item_three_fields("continuity_table", item)
}

/// Comando para atualizar item em Continuity
#[tauri::command]
fn update_continuity_item(old_name: String, item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::update_list_item_three_fields("continuity_table", &old_name, item)
}

/// Comando para deletar item em Continuity
#[tauri::command]
fn delete_continuity_item(name: String) -> Result<(), String> {
    DatabaseManager::delete_list_item_three_fields("continuity_table", &name)
}

/// Comando para obter itens de Planner
#[tauri::command]
fn get_planner_list() -> Result<Vec<ListItemThreeFields>, String> {
    DatabaseManager::get_list_items_three_fields("planner_table")
}

/// Comando para adicionar item em Planner
#[tauri::command]
fn add_planner_item(item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::add_list_item_three_fields("planner_table", item)
}

/// Comando para atualizar item em Planner
#[tauri::command]
fn update_planner_item(old_name: String, item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::update_list_item_three_fields("planner_table", &old_name, item)
}

/// Comando para deletar item em Planner
#[tauri::command]
fn delete_planner_item(name: String) -> Result<(), String> {
    DatabaseManager::delete_list_item_three_fields("planner_table", &name)
}

/// Comando para obter itens de Sourcing
#[tauri::command]
fn get_sourcing_list() -> Result<Vec<ListItemThreeFields>, String> {
    DatabaseManager::get_list_items_three_fields("sourcing_table")
}

/// Comando para adicionar item em Sourcing
#[tauri::command]
fn add_sourcing_item(item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::add_list_item_three_fields("sourcing_table", item)
}

/// Comando para atualizar item em Sourcing
#[tauri::command]
fn update_sourcing_item(old_name: String, item: ListItemThreeFields) -> Result<(), String> {
    DatabaseManager::update_list_item_three_fields("sourcing_table", &old_name, item)
}

/// Comando para deletar item em Sourcing
#[tauri::command]
fn delete_sourcing_item(name: String) -> Result<(), String> {
    DatabaseManager::delete_list_item_three_fields("sourcing_table", &name)
}

/// Comando para obter itens de Business Unit
#[tauri::command]
fn get_bu_list() -> Result<Vec<ListItemSingleField>, String> {
    DatabaseManager::get_list_items_single_field("business_unit_table", "bu")
}

/// Comando para adicionar item em Business Unit
#[tauri::command]
fn add_bu_item(name: String) -> Result<(), String> {
    DatabaseManager::add_list_item_single_field("business_unit_table", "bu", name)
}

/// Comando para atualizar item em Business Unit
#[tauri::command]
fn update_bu_item(old_name: String, new_name: String) -> Result<(), String> {
    DatabaseManager::update_list_item_single_field("business_unit_table", "bu", &old_name, new_name)
}

/// Comando para deletar item em Business Unit
#[tauri::command]
fn delete_bu_item(name: String) -> Result<(), String> {
    DatabaseManager::delete_list_item_single_field("business_unit_table", "bu", &name)
}

/// Comando para obter itens de Category
#[tauri::command]
fn get_category_list() -> Result<Vec<ListItemSingleField>, String> {
    DatabaseManager::get_list_items_single_field("categories_table", "category")
}

/// Comando para adicionar item em Category
#[tauri::command]
fn add_category_item(name: String) -> Result<(), String> {
    DatabaseManager::add_list_item_single_field("categories_table", "category", name)
}

/// Comando para atualizar item em Category
#[tauri::command]
fn update_category_item(old_name: String, new_name: String) -> Result<(), String> {
    DatabaseManager::update_list_item_single_field("categories_table", "category", &old_name, new_name)
}

/// Comando para deletar item em Category
#[tauri::command]
fn delete_category_item(name: String) -> Result<(), String> {
    DatabaseManager::delete_list_item_single_field("categories_table", "category", &name)
}

/// Comando para obter contagem de usuários online
#[tauri::command]
fn get_online_users_count() -> Result<i32, String> {
    DatabaseManager::get_online_users_count()
}

/// Comando para atualizar status online de um usuário
#[tauri::command]
fn set_user_online_status(user_id: i32, is_online: bool) -> Result<(), String> {
    DatabaseManager::set_user_online_status(user_id, is_online)
}

/// Comando Tauri para resetar todos os usuários para offline
#[tauri::command]
fn reset_all_users_offline() -> Result<(), String> {
    DatabaseManager::reset_all_users_offline()
}

/// Comando para buscar scores pendentes de avaliação
#[tauri::command]
fn get_pending_scores(user_id: i32) -> Result<Vec<serde_json::Value>, String> {
    DatabaseManager::get_pending_scores(user_id)
}

/// Comando para salvar score individual
#[tauri::command]
fn save_individual_score(
    record_id: i32,
    score_type: String,
    score_value: String,
    user_name: String,
) -> Result<String, String> {
    DatabaseManager::save_individual_score(record_id, score_type, score_value, user_name)
}

/// Comando de debug para consultar registro
#[tauri::command]
fn debug_get_record(record_id: i32) -> Result<String, String> {
    DatabaseManager::debug_get_record(record_id)
}

/// Comando para buscar todos os logs
#[tauri::command]
fn get_all_logs() -> Result<Vec<db_manager::LogEntry>, String> {
    DatabaseManager::get_all_logs()
}

/// Comando para registrar log de geração em lote
#[tauri::command]
fn log_bulk_generation(user_name: String, user_wwid: String, month: i32, year: i32, count: i32) -> Result<(), String> {
    DatabaseManager::log_bulk_generation(user_name, user_wwid, month, year, count)
}

/// Comando para buscar logs por usuário
#[tauri::command]
fn get_logs_by_user(user_name: String) -> Result<Vec<db_manager::LogEntry>, String> {
    DatabaseManager::get_logs_by_user(user_name)
}

/// Comando para buscar logs por período
#[tauri::command]
fn get_logs_by_date_range(start_date: String, end_date: String) -> Result<Vec<db_manager::LogEntry>, String> {
    DatabaseManager::get_logs_by_date_range(start_date, end_date)
}

/// Comando para buscar usuários mais ativos
#[tauri::command]
fn get_most_active_users(limit: i32) -> Result<Vec<(String, String, i32)>, String> {
    DatabaseManager::get_most_active_users(limit)
}

fn main() {
    // Inicializa o banco de dados ao iniciar a aplicação
    println!("\n🚀 Iniciando Score App...");
    
    match DatabaseManager::initialize() {
        Ok(_) => {
            println!("✅ Banco de dados inicializado com sucesso!");
            
            // Reseta todos os usuários para offline ao iniciar
            match DatabaseManager::reset_all_users_offline() {
                Ok(_) => println!("✅ Status de usuários resetado para offline"),
                Err(e) => println!("⚠️ Erro ao resetar status dos usuários: {}\n", e),
            }
            println!();
        },
        Err(e) => println!("⚠️ Erro ao inicializar banco: {}\n", e),
    }

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            validate_login, 
            list_users,
            get_total_suppliers,
            get_total_evaluations,
            get_average_score,
            get_total_users,
            search_suppliers_legacy,
            search_suppliers,
            search_suppliers_data,
            get_all_suppliers_by_status,
            get_supplier_data,
            update_supplier_data,
            create_supplier,
            check_po_exists,
            check_table_schema,
            debug_table,
            get_all_users,
            create_user,
            check_wwid_exists,
            update_user,
            delete_user,
            get_user_password,
            count_pending_users,
            get_pending_users,
            update_user_status,
            get_supplier_scores,
            get_supplier_score_records,
            save_supplier_score,
            get_criteria,
            get_target,
            update_criteria,
            get_planners,
            get_continuity_options,
            get_sourcing_options,
            get_sqie_options,
            get_business_units,
            get_categories,
            get_suppliers_at_risk,
            // Logs
            get_all_logs,
            get_logs_by_user,
            get_logs_by_date_range,
            log_bulk_generation,
            get_most_active_users,
            // Lists management
            get_sqie_list,
            add_sqie_item,
            update_sqie_item,
            delete_sqie_item,
            get_continuity_list,
            add_continuity_item,
            update_continuity_item,
            delete_continuity_item,
            get_planner_list,
            add_planner_item,
            update_planner_item,
            delete_planner_item,
            get_sourcing_list,
            add_sourcing_item,
            update_sourcing_item,
            delete_sourcing_item,
            get_bu_list,
            add_bu_item,
            update_bu_item,
            delete_bu_item,
            get_category_list,
            add_category_item,
            update_category_item,
            delete_category_item,
            get_online_users_count,
            set_user_online_status,
            reset_all_users_offline,
            get_pending_scores,
            save_individual_score,
            debug_get_record,
            send_email_via_outlook,
            get_supplier_responsibles,
            delete_all_logs,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// Comando Tauri para deletar todos os logs
#[tauri::command]
fn delete_all_logs() -> Result<(), String> {
    DatabaseManager::delete_all_logs()
}
/// Comando Tauri para buscar responsáveis de um fornecedor
#[tauri::command]
fn get_supplier_responsibles(supplier_id: String) -> Result<SupplierResponsibles, String> {
    DatabaseManager::get_supplier_responsibles(&supplier_id)
}

/// Comando Tauri para enviar email via Outlook
#[tauri::command]
fn send_email_via_outlook(
    to: String,
    subject: String,
    body_html: String,
) -> Result<String, String> {
    use std::process::Command;
    
    // Escapa aspas no HTML para VBS
    let escaped_html = body_html
        .replace("\"", "\"\"")
        .replace("\r\n", "")
        .replace("\n", "");
    
    // Cria arquivo VBS para enviar email via Outlook (mala direta - sem abrir janela)
    let vbs_script = format!(r#"
Set objOutlook = CreateObject("Outlook.Application")
Set objMail = objOutlook.CreateItem(0)

objMail.To = "{}"
objMail.Subject = "{}"
objMail.HTMLBody = "{}"
objMail.Send

Set objMail = Nothing
Set objOutlook = Nothing
"#, to, subject, escaped_html);

    let vbs_path = std::env::temp_dir().join("send_email.vbs");
    std::fs::write(&vbs_path, vbs_script)
        .map_err(|e| format!("Erro ao criar script VBS: {}", e))?;
    
    // Executa o script VBS
    let output = Command::new("cscript")
        .arg("//NoLogo")
        .arg(&vbs_path)
        .output()
        .map_err(|e| format!("Erro ao executar script: {}", e))?;
    
    // Limpa arquivo temporário
    let _ = std::fs::remove_file(vbs_path);
    
    if output.status.success() {
        Ok("Email enviado com sucesso".to_string())
    } else {
        let error = String::from_utf8_lossy(&output.stderr);
        Err(format!("Erro ao enviar email: {}", error))
    }
}
