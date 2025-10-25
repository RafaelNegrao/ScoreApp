use rusqlite::{Connection, Result as SqlResult, OptionalExtension};
use serde::Serialize;
use std::path::PathBuf;
use std::sync::Mutex;
use once_cell::sync::Lazy;

/// Estrutura para permissões do usuário
#[derive(Debug, Serialize, Clone)]
pub struct UserPermissions {
    pub otif: String,
    pub nil: String,
    pub pickup: String,
    pub package: String,
}

/// Estrutura para score de um fornecedor
#[derive(Debug, Serialize, Clone)]
pub struct SupplierScore {
    pub record_id: Option<i32>,
    pub supplier_id: String,
    pub month: i32,
    pub year: i32,
    pub otif_score: Option<String>,
    pub nil_score: Option<String>,
    pub pickup_score: Option<String>,
    pub package_score: Option<String>,
    pub total_score: Option<String>,
    pub comment: Option<String>,
}

/// Estrutura para registro de score histórico
#[derive(Debug, Serialize, Clone)]
pub struct ScoreRecord {
    pub supplier_id: String,
    pub year: String,
    pub month: i32,
    pub otif: Option<f64>,
    pub nil: Option<f64>,
    pub quality_pickup: Option<f64>,
    pub quality_package: Option<f64>,
    pub total_score: Option<f64>,
}

/// Estrutura para critério de avaliação
#[derive(Debug, Serialize, serde::Deserialize, Clone)]
pub struct Criteria {
    pub criteria_id: i32,
    pub criteria_target_id: Option<i32>,
    pub criteria_name: String,
    pub criteria_weight: f64,
    pub criteria_target: f64,
}

/// Estrutura para atualização de critério
#[derive(Debug, serde::Deserialize)]
#[allow(dead_code)]
pub struct CriteriaUpdate {
    pub criteria_id: i32,
    pub criteria_target_id: Option<i32>,
    pub criteria_weight: f64,
    pub criteria_target: f64,
}

/// Estrutura para dados do fornecedor
#[derive(Debug, Serialize, Clone)]
pub struct Supplier {
    pub supplier_id: String,
    pub supplier_po: Option<String>,
    #[serde(rename = "vendor_name")]
    pub supplier_name: String,
    pub bu: Option<String>,
    pub supplier_email: Option<String>,
    pub supplier_status: Option<String>,
    pub planner: Option<String>,
    pub country: Option<String>,
    pub supplier_category: Option<String>,
    pub continuity: Option<String>,
    pub sourcing: Option<String>,
    pub sqie: Option<String>,
    pub ssid: Option<String>,
    pub otif_target: Option<String>,
    pub nil_target: Option<String>,
    pub pickup_target: Option<String>,
    pub package_target: Option<String>,
    pub otif_score: Option<String>,
    pub nil_score: Option<String>,
    pub pickup_score: Option<String>,
    pub package_score: Option<String>,
    pub total_score: Option<String>,
}

/// Estrutura para atualização de fornecedor
#[derive(Debug, serde::Deserialize)]
pub struct SupplierUpdate {
    pub supplier_id: String,
    pub supplier_name: String,
    pub supplier_po: Option<String>,
    pub bu: Option<String>,
    pub supplier_email: Option<String>,
    pub supplier_status: Option<String>,
    pub planner: Option<String>,
    pub country: Option<String>,
    pub supplier_category: Option<String>,
    pub continuity: Option<String>,
    pub sourcing: Option<String>,
    pub sqie: Option<String>,
    pub ssid: Option<String>,
}

// Mapeamento interno: os nomes reais no banco são diferentes
// id -> record_id
// otif -> otif_score
// nil -> nil_score
// quality_pickup -> pickup_score
// quality_package -> package_score
// comment -> comments
// month/year são TEXT no banco

/// Estrutura para informações do usuário
#[derive(Debug, Serialize, Clone)]
pub struct UserInfo {
    pub user_id: i32,
    pub user_name: String,
    pub user_wwid: String,
    pub user_privilege: String,
    pub permissions: UserPermissions,
}

/// Estrutura para resposta de login
#[derive(Debug, Serialize)]
pub struct LoginResponse {
    pub success: bool,
    pub message: String,
    pub user: Option<UserInfo>,
}

/// Conexão global do banco de dados (singleton)
static DB_CONNECTION: Lazy<Mutex<Option<Connection>>> = Lazy::new(|| Mutex::new(None));

/// Gerenciador centralizado de banco de dados
pub struct DatabaseManager;

impl DatabaseManager {
    /// Obtém o caminho do banco de dados
    fn get_database_path() -> PathBuf {
        if cfg!(debug_assertions) {
            // Modo desenvolvimento
            let mut path = std::env::current_dir()
                .expect("Failed to get current directory");
            if path.ends_with("src-tauri") {
                path.pop();
            }
            path.push("database");
            path.push("database.db");
            println!("🔍 [DEBUG] Caminho do banco: {:?}", path);
            path
        } else {
            // Modo produção - database.db na mesma pasta do executável
            let mut path = std::env::current_exe()
                .expect("Failed to get executable path");
            path.pop();
            path.push("database.db");
            println!("🔍 [PROD] Caminho do banco: {:?}", path);
            path
        }
    }

    /// Inicializa a conexão com o banco de dados
    pub fn initialize() -> Result<(), String> {
        let db_path = Self::get_database_path();
        
        println!("📂 Verificando banco de dados em: {:?}", db_path);
        
        // Criar diretório database se não existir
        if let Some(parent) = db_path.parent() {
            if !parent.exists() {
                println!("📁 Criando diretório: {:?}", parent);
                std::fs::create_dir_all(parent)
                    .map_err(|e| format!("❌ Erro ao criar diretório: {}", e))?;
            }
        }
        
        let is_new_db = !db_path.exists();
        if is_new_db {
            println!("⚠️  Banco de dados não encontrado. Criando novo banco...");
        } else {
            println!("✅ Banco de dados encontrado!");
        }
        
        match Connection::open(&db_path) {
            Ok(conn) => {
                println!("✅ Conexão estabelecida com sucesso!");
                let mut db = DB_CONNECTION.lock().unwrap();
                *db = Some(conn);
                
                // Se é um banco novo, criar estrutura
                if is_new_db {
                    drop(db); // Libera o lock antes de chamar outras funções
                    Self::create_initial_structure()?;
                }
                
                println!("✅ Banco de dados pronto para uso!");
                
                Ok(())
            }
            Err(e) => {
                let error_msg = format!("❌ Erro ao conectar ao banco: {}", e);
                println!("{}", error_msg);
                Err(error_msg)
            }
        }
    }

    /// Cria a estrutura inicial do banco de dados
    fn create_initial_structure() -> Result<(), String> {
        println!("🏗️  Criando estrutura inicial do banco de dados...");
        
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        // Criar tabela de usuários
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                user_email TEXT UNIQUE NOT NULL,
                user_password TEXT NOT NULL,
                user_role TEXT,
                user_status TEXT DEFAULT 'active',
                user_permissions_otif TEXT,
                user_permissions_nil TEXT,
                user_permissions_pickup TEXT,
                user_permissions_package TEXT
            )",
            [],
        ).map_err(|e| format!("Erro ao criar tabela users: {}", e))?;
        
        // Criar tabela de fornecedores
        conn.execute(
            "CREATE TABLE IF NOT EXISTS supplier_database_table (
                supplier_id TEXT PRIMARY KEY,
                vendor_name TEXT NOT NULL,
                supplier_po TEXT,
                bu TEXT,
                supplier_email TEXT,
                supplier_status TEXT,
                planner TEXT,
                country TEXT,
                supplier_category TEXT,
                continuity TEXT,
                sourcing TEXT,
                sqie TEXT,
                ssid TEXT
            )",
            [],
        ).map_err(|e| format!("Erro ao criar tabela supplier_database_table: {}", e))?;
        
        // Criar tabela de scores
        conn.execute(
            "CREATE TABLE IF NOT EXISTS supplier_score (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id TEXT NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                otif_score TEXT,
                nil_score TEXT,
                pickup_score TEXT,
                package_score TEXT,
                total_score TEXT,
                comments TEXT,
                FOREIGN KEY (supplier_id) REFERENCES supplier_database_table(supplier_id)
            )",
            [],
        ).map_err(|e| format!("Erro ao criar tabela supplier_score: {}", e))?;
        
        // Criar tabela de critérios
        conn.execute(
            "CREATE TABLE IF NOT EXISTS criteria (
                criteria_id INTEGER PRIMARY KEY AUTOINCREMENT,
                criteria_target_id INTEGER,
                criteria_name TEXT NOT NULL,
                criteria_weight REAL NOT NULL,
                criteria_target REAL NOT NULL
            )",
            [],
        ).map_err(|e| format!("Erro ao criar tabela criteria: {}", e))?;
        
        // Criar usuário administrador padrão
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, user_name, user_email, user_password, user_role, user_permissions_otif, user_permissions_nil, user_permissions_pickup, user_permissions_package)
             VALUES ('admin', 'Administrador', 'admin@scoreapp.com', 'admin', 'admin', 'edit', 'edit', 'edit', 'edit')",
            [],
        ).map_err(|e| format!("Erro ao criar usuário admin: {}", e))?;
        
        // Criar critérios padrão
        let default_criteria = vec![
            ("OTIF", 25.0, 95.0),
            ("NIL", 25.0, 95.0),
            ("Pickup", 25.0, 95.0),
            ("Package", 25.0, 95.0),
        ];
        
        for (name, weight, target) in default_criteria {
            conn.execute(
                "INSERT OR IGNORE INTO criteria (criteria_name, criteria_weight, criteria_target)
                 VALUES (?1, ?2, ?3)",
                rusqlite::params![name, weight, target],
            ).map_err(|e| format!("Erro ao criar critério {}: {}", name, e))?;
        }
        
        println!("✅ Estrutura inicial criada com sucesso!");
        Ok(())
    }

    /// Obtém uma referência à conexão do banco
    fn get_connection() -> Result<std::sync::MutexGuard<'static, Option<Connection>>, String> {
        Ok(DB_CONNECTION.lock().unwrap())
    }

    /// Verifica se uma coluna existe na tabela de fornecedores
    fn supplier_table_has_column(conn: &Connection, column_name: &str) -> Result<bool, String> {
        let mut stmt = conn
            .prepare("PRAGMA table_info(supplier_database_table)")
            .map_err(|e| format!("Erro ao inspecionar estrutura da tabela de fornecedores: {}", e))?;

        let mut rows = stmt
            .query([])
            .map_err(|e| format!("Erro ao consultar estrutura da tabela de fornecedores: {}", e))?;

        while let Some(row) = rows
            .next()
            .map_err(|e| format!("Erro ao iterar colunas da tabela de fornecedores: {}", e))?
        {
            let existing_column: String = row
                .get(1)
                .map_err(|e| format!("Erro ao ler nome da coluna da tabela de fornecedores: {}", e))?;

            if existing_column.eq_ignore_ascii_case(column_name) {
                return Ok(true);
            }
        }

        Ok(false)
    }

    /// Valida as credenciais de login
    pub fn validate_login(username: String, password: String) -> Result<LoginResponse, String> {
        println!("\n🔐 Iniciando validação de login...");
        println!("👤 Usuário: {}", username);
        
        // Garante que a conexão está inicializada
        let mut conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            println!("⚠️ Conexão não inicializada, inicializando agora...");
            drop(conn_guard); // Libera o lock antes de inicializar
            Self::initialize()?;
            conn_guard = Self::get_connection()?;
        }

        let conn = conn_guard.as_ref().unwrap();

        // Verificar se a coluna user_status existe, caso contrário, criá-la
        let column_exists = conn.query_row(
            "SELECT COUNT(*) FROM pragma_table_info('users_table') WHERE name='user_status'",
            [],
            |row| row.get::<_, i32>(0)
        ).unwrap_or(0) > 0;

        if !column_exists {
            println!("⚠️ Coluna user_status não existe, criando...");
            if let Err(e) = conn.execute(
                "ALTER TABLE users_table ADD COLUMN user_status TEXT DEFAULT 'Active'",
                []
            ) {
                println!("❌ Erro ao criar coluna user_status: {}", e);
            } else {
                println!("✅ Coluna user_status criada com sucesso");
            }
        }

        println!("🔍 Buscando usuário no banco de dados...");

        // Prepara a query
        let mut stmt = match conn.prepare(
            "SELECT user_id, user_name, user_wwid, user_password, user_privilege, user_status, otif, nil, pickup, package
             FROM users_table 
             WHERE user_wwid = ?1"
        ) {
            Ok(stmt) => {
                println!("✅ Query preparada com sucesso");
                stmt
            }
            Err(e) => {
                let error_msg = format!("❌ Erro ao preparar query: {}", e);
                println!("{}", error_msg);
                return Err(error_msg);
            }
        };

        // Executa a query
        let user_result = stmt.query_row([&username], |row| {
            Ok((
                row.get::<_, i32>(0)?,      // user_id
                row.get::<_, String>(1)?,    // user_name
                row.get::<_, String>(2)?,    // user_wwid
                row.get::<_, String>(3)?,    // user_password
                row.get::<_, String>(4)?,    // user_privilege
                row.get::<_, String>(5)?,    // user_status
                row.get::<_, String>(6)?,    // otif
                row.get::<_, String>(7)?,    // nil
                row.get::<_, String>(8)?,    // pickup
                row.get::<_, String>(9)?,    // package
            ))
        });

        match user_result {
            Ok((user_id, user_name, user_wwid, stored_password, user_privilege, user_status, otif, nil, pickup, package)) => {
                println!("✅ Usuário encontrado: {} (ID: {}, Status: {})", user_name, user_id, user_status);
                
                // Verifica o status do usuário antes de validar senha
                if user_status == "Pendent" {
                    println!("⏳ Usuário com status Pendent - aguardando autorização");
                    return Ok(LoginResponse {
                        success: false,
                        message: "Aguardando autorização do Admin".to_string(),
                        user: None,
                    });
                }
                
                if user_status == "Inactive" {
                    println!("🚫 Usuário com status Inactive");
                    return Ok(LoginResponse {
                        success: false,
                        message: "Usuário inativo. Entre em contato com o administrador.".to_string(),
                        user: None,
                    });
                }
                
                println!("🔑 Validando senha...");
                
                // Valida a senha
                if stored_password == password {
                    println!("✅ Senha correta! Login bem-sucedido!");
                    
                    // Atualiza is_online para 1
                    if let Err(e) = conn.execute(
                        "UPDATE users_table SET is_online = 1 WHERE user_id = ?1",
                        [user_id]
                    ) {
                        println!("⚠️ Erro ao atualizar status online: {}", e);
                    } else {
                        println!("✅ Status online atualizado para user_id: {}", user_id);
                    }
                    
                    Ok(LoginResponse {
                        success: true,
                        message: "Login realizado com sucesso!".to_string(),
                        user: Some(UserInfo {
                            user_id,
                            user_name,
                            user_wwid,
                            user_privilege,
                            permissions: UserPermissions {
                                otif,
                                nil,
                                pickup,
                                package,
                            },
                        }),
                    })
                } else {
                    println!("❌ Senha incorreta!");
                    Ok(LoginResponse {
                        success: false,
                        message: "Senha incorreta!".to_string(),
                        user: None,
                    })
                }
            }
            Err(e) => {
                println!("❌ Usuário não encontrado: {}", e);
                Ok(LoginResponse {
                    success: false,
                    message: "Usuário não encontrado!".to_string(),
                    user: None,
                })
            }
        }
    }

    /// Lista todos os usuários (para debug)
    pub fn list_all_users() -> Result<Vec<(String, String)>, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let mut stmt = conn
            .prepare("SELECT user_wwid, user_name FROM users_table")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let users = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                ))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<SqlResult<Vec<_>>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        Ok(users)
    }

    /// Obtém o total de fornecedores
    pub fn get_total_suppliers() -> Result<i64, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let count: i64 = conn
            .query_row("SELECT COUNT(*) FROM supplier_database_table", [], |row| row.get(0))
            .map_err(|e| format!("Erro ao contar fornecedores: {}", e))?;

        Ok(count)
    }

    /// Obtém o total de avaliações
    pub fn get_total_evaluations() -> Result<i64, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let count: i64 = conn
            .query_row("SELECT COUNT(*) FROM supplier_score_records_table", [], |row| row.get(0))
            .map_err(|e| format!("Erro ao contar avaliações: {}", e))?;

        Ok(count)
    }

    /// Obtém a média de score
    pub fn get_average_score() -> Result<f64, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let avg: Result<f64, rusqlite::Error> = conn.query_row(
            "SELECT AVG(CAST(total_score AS REAL)) FROM supplier_score_records_table WHERE total_score IS NOT NULL AND total_score != ''",
            [],
            |row| row.get(0)
        );

        Ok(avg.unwrap_or(0.0))
    }

    /// Obtém o total de usuários
    pub fn get_total_users() -> Result<i64, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let count: i64 = conn
            .query_row("SELECT COUNT(*) FROM users_table", [], |row| row.get(0))
            .map_err(|e| format!("Erro ao contar usuários: {}", e))?;

        Ok(count)
    }

    /// Busca fornecedores por query de pesquisa (legado - retorna JSON)
    pub fn search_suppliers_legacy(query: String) -> Result<Vec<serde_json::Value>, String> {
        println!("🔍 Buscando fornecedores com query: '{}'", query);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            println!("❌ Conexão não inicializada");
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let search_query = format!("%{}%", query);
        println!("🔍 Query SQL preparada: LIKE '{}'", search_query);
        
        // Conta total de fornecedores
        let count: i64 = conn
            .query_row("SELECT COUNT(*) FROM supplier_database_table", [], |row| row.get(0))
            .unwrap_or(0);
        println!("📊 Total de fornecedores na tabela: {}", count);
        
        // Testa a query diretamente
        let test_count: i64 = conn
            .query_row(
                     "SELECT COUNT(*) FROM supplier_database_table 
                      WHERE LOWER(COALESCE(vendor_name, '')) LIKE LOWER(?1) 
                          OR LOWER(COALESCE(CAST(supplier_po AS TEXT), '')) LIKE LOWER(?1) 
                          OR LOWER(COALESCE(bu, '')) LIKE LOWER(?1)",
                [&search_query],
                |row| row.get(0)
            )
            .unwrap_or(0);
        println!("🔍 Registros que correspondem à busca: {}", test_count);
        
        let mut stmt = conn
            .prepare(
                "SELECT ROWID, vendor_name, COALESCE(CAST(supplier_po AS TEXT), '') AS supplier_po, bu 
                 FROM supplier_database_table 
                 WHERE LOWER(COALESCE(vendor_name, '')) LIKE LOWER(?1) 
                    OR LOWER(COALESCE(CAST(supplier_po AS TEXT), '')) LIKE LOWER(?1) 
                    OR LOWER(COALESCE(bu, '')) LIKE LOWER(?1)
                 LIMIT 50"
            )
            .map_err(|e| {
                println!("❌ Erro ao preparar query: {}", e);
                format!("Erro ao preparar query: {}", e)
            })?;

        let suppliers_iter = stmt
            .query_map([&search_query], |row| {
                let rowid = row.get::<_, i64>(0)?;
                let vendor_name = row.get::<_, Option<String>>(1)?;
                
                // Após CAST, supplier_po já vem como TEXT
                let supplier_po_str = row.get::<_, String>(2).unwrap_or_default();
                
                let bu = row.get::<_, Option<String>>(3)?;
                
                println!("📋 Fornecedor encontrado: ROWID={}, Nome={}, PO={}, BU={}", 
                    rowid,
                    vendor_name.as_deref().unwrap_or("NULL"),
                    &supplier_po_str,
                    bu.as_deref().unwrap_or("NULL")
                );
                
                Ok(serde_json::json!({
                    "supplier_id": rowid.to_string(),
                    "vendor_name": vendor_name.unwrap_or_else(|| "".to_string()),
                    "supplier_po": supplier_po_str,
                    "business_unit": bu.unwrap_or_else(|| "".to_string()),
                    "supplier_status": "active",
                }))
            })
            .map_err(|e| {
                println!("❌ Erro ao executar query: {}", e);
                format!("Erro ao executar query: {}", e)
            })?;

        let suppliers: Vec<serde_json::Value> = suppliers_iter
            .enumerate()
            .filter_map(|(idx, r)| {
                match r {
                    Ok(supplier) => Some(supplier),
                    Err(e) => {
                        println!("❌ Erro ao processar fornecedor #{}: {}", idx, e);
                        None
                    }
                }
            })
            .collect();

        println!("✅ Encontrados {} fornecedores", suppliers.len());
        Ok(suppliers)
    }

    /// Obtém todos os usuários do sistema
    pub fn get_all_users() -> Result<Vec<serde_json::Value>, String> {
        println!("🔍 Buscando todos os usuários...");
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            println!("❌ Conexão não inicializada");
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        // Primeiro, vamos verificar se a tabela existe e tem dados
        let count: Result<i64, _> = conn.query_row("SELECT COUNT(*) FROM users_table", [], |row| row.get(0));
        match count {
            Ok(c) => println!("📊 Total de registros na tabela users_table: {}", c),
            Err(e) => {
                println!("❌ Erro ao contar usuários: {}", e);
                return Err(format!("Erro ao acessar tabela: {}", e));
            }
        }

        let mut stmt = conn
            .prepare("SELECT user_id, user_name, user_wwid, user_privilege, user_status, otif, nil, pickup, package FROM users_table")
            .map_err(|e| {
                println!("❌ Erro ao preparar query: {}", e);
                format!("Erro ao preparar query: {}", e)
            })?;

        let users: Vec<serde_json::Value> = stmt
            .query_map([], |row| {
                let user_id: i32 = row.get(0)?;
                
                // user_name pode ser NULL, então usamos Option
                let user_name: String = row.get::<_, Option<String>>(1)?.unwrap_or_default();
                let user_wwid: String = row.get::<_, Option<String>>(2)?.unwrap_or_default();
                let user_privilege: String = row.get::<_, Option<String>>(3)?.unwrap_or_default();
                let user_status: String = row.get::<_, Option<String>>(4)?.unwrap_or_else(|| "Active".to_string());
                
                // otif, nil, pickup, package podem ser TEXT ou INTEGER
                let otif: i32 = row.get::<_, Option<String>>(5)?
                    .and_then(|s| s.parse::<i32>().ok())
                    .or_else(|| row.get::<_, Option<i32>>(5).ok().flatten())
                    .unwrap_or(0);
                    
                let nil: i32 = row.get::<_, Option<String>>(6)?
                    .and_then(|s| s.parse::<i32>().ok())
                    .or_else(|| row.get::<_, Option<i32>>(6).ok().flatten())
                    .unwrap_or(0);
                    
                let pickup: i32 = row.get::<_, Option<String>>(7)?
                    .and_then(|s| s.parse::<i32>().ok())
                    .or_else(|| row.get::<_, Option<i32>>(7).ok().flatten())
                    .unwrap_or(0);
                    
                let package: i32 = row.get::<_, Option<String>>(8)?
                    .and_then(|s| s.parse::<i32>().ok())
                    .or_else(|| row.get::<_, Option<i32>>(8).ok().flatten())
                    .unwrap_or(0);

                println!("📋 Usuário encontrado: ID={}, Nome={}, WWID={}, Status={}", user_id, user_name, user_wwid, user_status);

                Ok(serde_json::json!({
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_wwid": user_wwid,
                    "user_privilege": user_privilege,
                    "user_status": user_status,
                    "otif": otif,
                    "nil": nil,
                    "pickup": pickup,
                    "package": package,
                }))
            })
            .map_err(|e| {
                println!("❌ Erro ao executar query: {}", e);
                format!("Erro ao executar query: {}", e)
            })?
            .enumerate()
            .filter_map(|(idx, r)| {
                match r {
                    Ok(user) => Some(user),
                    Err(e) => {
                        println!("❌ Erro ao processar usuário #{}: {}", idx, e);
                        None
                    }
                }
            })
            .collect();

        println!("✅ Total de usuários encontrados: {}", users.len());
        Ok(users)
    }

    /// Cria um novo usuário
    pub fn create_user(
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
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        // Verifica se WWID já existe
        let wwid_exists: Result<i32, _> = conn.query_row(
            "SELECT COUNT(*) FROM users_table WHERE user_wwid = ?1",
            [&wwid],
            |row| row.get(0)
        );

        if let Ok(count) = wwid_exists {
            if count > 0 {
                return Err("WWID já cadastrado no sistema".to_string());
            }
        }

        conn.execute(
            "INSERT INTO users_table (user_name, user_wwid, user_privilege, user_status, user_password, otif, nil, pickup, package) 
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            [&name, &wwid, &privilege, &status, &password, &otif.to_string(), &nil.to_string(), &pickup.to_string(), &package.to_string()],
        )
        .map_err(|e| format!("Erro ao criar usuário: {}", e))?;

        Ok(conn.last_insert_rowid())
    }

    /// Verifica se um WWID já existe no banco
    pub fn check_wwid_exists(wwid: String) -> Result<bool, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let count: Result<i32, _> = conn.query_row(
            "SELECT COUNT(*) FROM users_table WHERE user_wwid = ?1",
            [&wwid],
            |row| row.get(0)
        );

        match count {
            Ok(c) => Ok(c > 0),
            Err(e) => Err(format!("Erro ao verificar WWID: {}", e))
        }
    }

    /// Atualiza um usuário existente
    pub fn update_user(
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
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        if let Some(pwd) = password {
            // Atualizar com nova senha
            conn.execute(
                "UPDATE users_table SET user_name = ?1, user_wwid = ?2, user_privilege = ?3, user_status = ?4, user_password = ?5, 
                 otif = ?6, nil = ?7, pickup = ?8, package = ?9 WHERE user_id = ?10",
                [&name, &wwid, &privilege, &status, &pwd, &otif.to_string(), &nil.to_string(), &pickup.to_string(), &package.to_string(), &user_id.to_string()],
            )
        } else {
            // Atualizar sem mudar a senha
            conn.execute(
                "UPDATE users_table SET user_name = ?1, user_wwid = ?2, user_privilege = ?3, user_status = ?4, 
                 otif = ?5, nil = ?6, pickup = ?7, package = ?8 WHERE user_id = ?9",
                [&name, &wwid, &privilege, &status, &otif.to_string(), &nil.to_string(), &pickup.to_string(), &package.to_string(), &user_id.to_string()],
            )
        }
        .map_err(|e| format!("Erro ao atualizar usuário: {}", e))?;

        Ok(())
    }

    /// Exclui um usuário
    pub fn delete_user(user_id: i32) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        conn.execute(
            "DELETE FROM users_table WHERE user_id = ?1",
            [&user_id],
        )
        .map_err(|e| format!("Erro ao excluir usuário: {}", e))?;

        Ok(())
    }

    /// Busca a senha de um usuário
    pub fn get_user_password(user_id: i32) -> Result<String, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let password: String = conn
            .query_row(
                "SELECT user_password FROM users_table WHERE user_id = ?1",
                [&user_id],
                |row| row.get(0),
            )
            .map_err(|e| format!("Erro ao buscar senha: {}", e))?;

        Ok(password)
    }

    /// Conta usuários pendentes
    pub fn count_pending_users() -> Result<i32, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let count: i32 = conn
            .query_row(
                "SELECT COUNT(*) FROM users_table WHERE user_status = 'Pendent'",
                [],
                |row| row.get(0),
            )
            .map_err(|e| format!("Erro ao contar usuários pendentes: {}", e))?;

        Ok(count)
    }

    /// Busca usuários pendentes
    pub fn get_pending_users() -> Result<Vec<serde_json::Value>, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let mut stmt = conn
            .prepare("SELECT user_id, user_name, user_wwid FROM users_table WHERE user_status = 'Pendent' ORDER BY user_id DESC")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let users: Vec<serde_json::Value> = stmt
            .query_map([], |row| {
                Ok(serde_json::json!({
                    "user_id": row.get::<_, i32>(0)?,
                    "user_name": row.get::<_, String>(1)?,
                    "user_wwid": row.get::<_, String>(2)?,
                }))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .filter_map(|r| r.ok())
            .collect();

        Ok(users)
    }

    /// Aprova ou rejeita um usuário pendente
    pub fn update_user_status(user_id: i32, status: String) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        conn.execute(
            "UPDATE users_table SET user_status = ?1 WHERE user_id = ?2",
            [&status, &user_id.to_string()],
        )
        .map_err(|e| format!("Erro ao atualizar status: {}", e))?;

        Ok(())
    }

    /// Busca os scores de fornecedores específicos para um mês/ano
    pub fn get_supplier_scores(supplier_ids: Vec<String>, month: i32, year: i32) -> Result<Vec<SupplierScore>, String> {
        println!("\n🔍 Buscando scores - Mês: {}, Ano: {}, IDs: {:?}", month, year, supplier_ids);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        // Debug: Mostra todos os registros da tabela
        println!("\n📋 DEBUG - Listando TODOS os registros da tabela:");
        if let Ok(mut stmt) = conn.prepare("SELECT supplier_id, month, year, otif_score FROM supplier_score_records_table LIMIT 10") {
            if let Ok(rows) = stmt.query_map([], |row| {
                Ok(format!("supplier_id: '{}', month: {}, year: {}, otif: {:?}",
                    row.get::<_, String>(0).unwrap_or_default(),
                    row.get::<_, String>(1).unwrap_or_default(),
                    row.get::<_, String>(2).unwrap_or_default(),
                    row.get::<_, Option<String>>(3).unwrap_or(None)
                ))
            }) {
                for (i, row) in rows.enumerate() {
                    if let Ok(info) = row {
                        println!("  [{}] {}", i + 1, info);
                    }
                }
            }
        }
        println!("📋 FIM DEBUG\n");
        
        let mut scores = Vec::new();

        for supplier_id in supplier_ids {
            println!("🔎 Buscando score para supplier_id: '{}' (tipo: String)", supplier_id);
            
            // Nomes reais das colunas no banco:
            // id, supplier_id, month (TEXT), year (TEXT), otif (REAL), nil (REAL), 
            // quality_pickup (TEXT), quality_package (TEXT), total_score (TEXT), comment (TEXT)
            let query = "SELECT id, supplier_id, month, year, otif, nil, quality_pickup, quality_package, total_score, comment 
                         FROM supplier_score_records_table 
                         WHERE lower(trim(supplier_id)) = lower(trim(?1)) AND month = ?2 AND year = ?3";
            
            println!("🔍 Query: {} com params: ['{}', '{}', '{}']", query, supplier_id, month, year);
            
            let score = conn.query_row(
                query,
                rusqlite::params![&supplier_id, month.to_string(), year.to_string()],
                |row| {
                    let record_id: Option<i32> = row.get(0).ok();
                    let sid: String = row.get(1)?;
                    
                    // month e year são TEXT no banco
                    let m: i32 = row.get::<_, String>(2)?.parse().unwrap_or(0);
                    let y: i32 = row.get::<_, String>(3)?.parse().unwrap_or(0);
                    
                    // otif e nil são REAL, mas vamos pegar como String
                    let otif: Option<String> = match row.get::<_, f64>(4) {
                        Ok(v) => Some(v.to_string()),
                        Err(_) => row.get::<_, Option<String>>(4)?,
                    };
                    
                    let nil: Option<String> = match row.get::<_, f64>(5) {
                        Ok(v) => Some(v.to_string()),
                        Err(_) => row.get::<_, Option<String>>(5)?,
                    };
                    
                    // quality_pickup e quality_package são TEXT
                    let pickup: Option<String> = row.get(6).ok();
                    let package: Option<String> = row.get(7).ok();
                    let total: Option<String> = row.get(8).ok();
                    let comment: Option<String> = row.get(9).ok();
                    
                    println!("✅ Score encontrado - ID: {}, OTIF: {:?}, NIL: {:?}, Pickup: {:?}, Package: {:?}, Total: {:?}, Comment: {:?}", 
                             sid, otif, nil, pickup, package, total, comment);
                    
                    Ok(SupplierScore {
                        record_id,
                        supplier_id: sid,
                        month: m,
                        year: y,
                        otif_score: otif,
                        nil_score: nil,
                        pickup_score: pickup,
                        package_score: package,
                        total_score: total,
                        comment,
                    })
                },
            );

            match score {
                Ok(s) => {
                    println!("✅ Score carregado para {}", supplier_id);
                    scores.push(s);
                },
                Err(e) => {
                    println!("⚠️ Score não encontrado para {} - Erro: {}", supplier_id, e);
                    // Se não encontrar, retorna um score vazio para este fornecedor
                    scores.push(SupplierScore {
                        record_id: None,
                        supplier_id: supplier_id.clone(),
                        month,
                        year,
                        otif_score: None,
                        nil_score: None,
                        pickup_score: None,
                        package_score: None,
                        total_score: None,
                        comment: None,
                    });
                }
            }
        }

        println!("📊 Total de scores retornados: {}", scores.len());
        Ok(scores)
    }

    /// Busca todos os registros de score de um fornecedor específico
    pub fn get_supplier_score_records(supplier_id: String) -> Result<Vec<ScoreRecord>, String> {
        println!("\n🔍 Buscando registros de score para supplier_id: '{}'", supplier_id);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        let query = "SELECT supplier_id, month, year, otif, nil, quality_pickup, quality_package, total_score
                     FROM supplier_score_records_table 
                     WHERE lower(trim(supplier_id)) = lower(trim(?1))
                     ORDER BY year, month";
        
        let mut stmt = conn.prepare(query)
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let records = stmt.query_map([&supplier_id], |row| {
            let supplier_id_val: String = row.get(0)?;
            let month_str: String = row.get(1)?;
            let year: String = row.get(2)?;
            
            // Função helper para tentar ler como f64 ou String
            let get_score = |idx: usize| -> Option<f64> {
                // Tenta primeiro como f64
                if let Ok(val) = row.get::<_, Option<f64>>(idx) {
                    return val;
                }
                // Se falhar, tenta como String e converte
                if let Ok(Some(val)) = row.get::<_, Option<String>>(idx) {
                    return val.parse::<f64>().ok();
                }
                None
            };
            
            let otif = get_score(3);
            let nil = get_score(4);
            let quality_pickup = get_score(5);
            let quality_package = get_score(6);
            let total_score = get_score(7);
            
            // Converte month para número
            let month_num: i32 = month_str.parse().unwrap_or(1);
            
            Ok(ScoreRecord {
                supplier_id: supplier_id_val,
                year,
                month: month_num,
                otif,
                nil,
                quality_pickup,
                quality_package,
                total_score,
            })
        })
        .map_err(|e| format!("Erro ao executar query: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        println!("✅ {} registros encontrados para supplier_id: '{}'", records.len(), supplier_id);
        for record in &records {
            println!("   📊 Year: {}, Month: {}, OTIF: {:?}, NIL: {:?}, Pickup: {:?}, Package: {:?}", 
                record.year, record.month, record.otif, record.nil, record.quality_pickup, record.quality_package);
        }
        Ok(records)
    }

    /// Salva ou atualiza o score de um fornecedor
    pub fn save_supplier_score(
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
    ) -> Result<String, String> {
        println!("\n💾 ========================================");
        println!("💾 SAVE_SUPPLIER_SCORE CHAMADO!");
        println!("💾 supplier_id: '{}'", supplier_id);
        println!("💾 supplier_name: '{}'", supplier_name);
        println!("💾 month: {}, year: {}", month, year);
        println!("💾 otif_score: {:?}", otif_score);
        println!("💾 nil_score: {:?}", nil_score);
        println!("💾 pickup_score: {:?}", pickup_score);
        println!("💾 package_score: {:?}", package_score);
        println!("💾 total_score: {:?}", total_score);
        println!("💾 comments: {:?}", comments);
        println!("💾 user_name: '{}'", user_name);
        println!("💾 ========================================\n");
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        // Usa o total_score que veio do frontend (já calculado)
        let total_score_value = total_score.unwrap_or_else(|| "0".to_string());
        println!("📊 Total score a salvar: {}", total_score_value);
        
        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
        
        // Detecta se é geração automática de nota cheia
        let is_auto_generated = comments.as_ref()
            .map(|c| c.contains("auto-generated") || c.contains("Maximum score"))
            .unwrap_or(false);
        
        // Verifica se já existe um registro
        let exists = conn.query_row(
            "SELECT id FROM supplier_score_records_table WHERE lower(trim(supplier_id)) = lower(trim(?1)) AND month = ?2 AND year = ?3",
            rusqlite::params![&supplier_id, month.to_string(), year.to_string()],
            |row| row.get::<_, i32>(0)
        );
        
        match exists {
            Ok(id) => {
                // Se for geração automática e já existe registro, apenas ignora
                if is_auto_generated {
                    println!("⏭️  Registro já existe (id: {}), ignorando geração automática", id);
                    return Ok("Registro já existe, ignorado".to_string());
                }
                
                // Caso contrário, atualiza o registro existente
                println!("📝 Atualizando registro existente (id: {})", id);
                conn.execute(
                    "UPDATE supplier_score_records_table 
                     SET otif = ?1, nil = ?2, quality_pickup = ?3, quality_package = ?4, 
                         total_score = ?5, comment = ?6, change_date = ?7, changed_by = ?8
                     WHERE id = ?9",
                    rusqlite::params![
                        otif_score.as_ref().and_then(|s| s.parse::<f64>().ok()),
                        nil_score.as_ref().and_then(|s| s.parse::<f64>().ok()),
                        pickup_score,
                        package_score,
                        total_score_value,
                        comments,
                        now,
                        user_name,
                        id
                    ],
                ).map_err(|e| format!("Erro ao atualizar: {}", e))?;
                
                println!("✅ Score atualizado com sucesso!");
                Ok("Score atualizado com sucesso".to_string())
            }
            Err(_) => {
                // Insere novo registro
                println!("➕ Criando novo registro");
                conn.execute(
                    "INSERT INTO supplier_score_records_table 
                     (supplier_id, supplier_name, month, year, otif, nil, quality_pickup, quality_package, 
                      total_score, comment, register_date, registered_by, change_date, changed_by)
                     VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)",
                    rusqlite::params![
                        supplier_id,
                        supplier_name,
                        month.to_string(),
                        year.to_string(),
                        otif_score.as_ref().and_then(|s| s.parse::<f64>().ok()),
                        nil_score.as_ref().and_then(|s| s.parse::<f64>().ok()),
                        pickup_score,
                        package_score,
                        total_score_value,
                        comments,
                        now.clone(),
                        user_name.clone(),
                        now,
                        user_name
                    ],
                ).map_err(|e| format!("Erro ao inserir: {}", e))?;
                
                println!("✅ Score criado com sucesso!");
                                Ok("Score criado com sucesso".to_string())
            }
        }
    }

    /// Busca todos os critérios de avaliação
    pub fn get_criteria() -> Result<Vec<Criteria>, String> {
        println!("\n🔍 Buscando critérios de avaliação...");

        let conn_guard = Self::get_connection()?;

        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        // Busca TODOS os 5 registros
        let mut stmt = conn
            .prepare(
                "SELECT criteria_id, criteria_category, value
                 FROM criteria_table
                 ORDER BY criteria_id"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let criteria_iter = stmt
            .query_map([], |row| {
                let criteria_id = row.get::<_, i32>(0)?;
                let criteria_category = row.get::<_, String>(1)?;
                let value_str = row.get::<_, String>(2)?;
                let value = value_str.parse::<f64>().unwrap_or(0.0);

                println!("  📊 ID {}: '{}' = {}", criteria_id, criteria_category, value);

                // Determina se é target ou weight pelo nome da categoria
                let is_target = criteria_category.to_lowercase().contains("target");

                Ok(Criteria {
                    criteria_id,
                    criteria_target_id: if is_target { None } else { None }, // Não precisa de target_id
                    criteria_name: criteria_category,
                    criteria_weight: if is_target { 0.0 } else { value },
                    criteria_target: if is_target { value } else { 0.0 },
                })
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?;

        let result: Vec<Criteria> = criteria_iter
            .filter_map(|r| r.ok())
            .collect();

        println!("✅ Encontrados {} critérios", result.len());
        Ok(result)
    }

    /// Busca o valor do target configurado nos critérios
    pub fn get_target() -> Result<f64, String> {
        println!("\n🎯 Buscando target configurado...");

        let conn_guard = Self::get_connection()?;

        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        // Busca o registro com "Target" no nome
        let target = conn.query_row(
            "SELECT value FROM criteria_table 
             WHERE LOWER(criteria_category) LIKE '%target%'
             LIMIT 1",
            [],
            |row| {
                let value_str: String = row.get(0)?;
                Ok(value_str.parse::<f64>().unwrap_or(8.7))
            }
        )
        .unwrap_or(8.7);

        println!("✅ Target encontrado: {}", target);
        Ok(target)
    }

    /// Busca fornecedores por nome ou ID
    pub fn search_suppliers(query: String) -> Result<Vec<Supplier>, String> {
        println!("\n🔍 ========================================");
        println!("🔍 SEARCH_SUPPLIERS CHAMADO!");
        println!("🔍 Query recebida: '{}'", query);
        println!("🔍 Tamanho da query: {}", query.len());
        println!("🔍 ========================================\n");
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            println!("❌ Conexão não inicializada");
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        // DEBUG: Mostra estrutura da tabela apenas na primeira busca
        static FIRST_RUN: std::sync::Once = std::sync::Once::new();
        FIRST_RUN.call_once(|| {
            println!("\n📋 === ESTRUTURA DA TABELA supplier_database_table ===");
            if let Ok(mut stmt) = conn.prepare("PRAGMA table_info(supplier_database_table)") {
                if let Ok(columns) = stmt.query_map([], |row| {
                    let name: String = row.get(1)?;
                    let col_type: String = row.get(2)?;
                    Ok((name, col_type))
                }) {
                    for col in columns.filter_map(|c| c.ok()) {
                        println!("   📌 {} ({})", col.0, col.1);
                    }
                }
            }
            println!("=================================================\n");
        });
        
        let search_pattern = format!("%{}%", query);
        println!("🔍 Padrão de busca: {}", search_pattern);
        
        // Primeiro, testa se há registros na tabela
        let total_count: i64 = conn
            .query_row("SELECT COUNT(*) FROM supplier_database_table", [], |row| row.get(0))
            .unwrap_or(0);
        println!("📊 Total de registros na tabela: {}", total_count);
        
        // Testa quantos correspondem à busca
        let match_count: i64 = conn
            .query_row(
                         "SELECT COUNT(*) FROM supplier_database_table 
                          WHERE LOWER(COALESCE(CAST(supplier_po AS TEXT), '')) LIKE LOWER(?1) 
                              OR LOWER(COALESCE(vendor_name, '')) LIKE LOWER(?1)
                              OR LOWER(COALESCE(bu, '')) LIKE LOWER(?1)",
                [&search_pattern],
                |row| row.get(0)
            )
            .unwrap_or(0);
        println!("🔍 Registros que correspondem à busca: {}", match_count);
        
        let mut stmt = conn
            .prepare(
                     "SELECT DISTINCT 
                          COALESCE(CAST(supplier_id AS TEXT), '') as supplier_id,
                          COALESCE(CAST(supplier_po AS TEXT), '') as supplier_po, 
                          COALESCE(vendor_name, '') as vendor_name,
                          bu,
                          supplier_email,
                          supplier_status,
                          planner,
                          country,
                          supplier_category,
                          continuity,
                          sourcing,
                          sqie,
                          ssid
                 FROM supplier_database_table 
                          WHERE LOWER(COALESCE(CAST(supplier_po AS TEXT), '')) LIKE LOWER(?1) 
                              OR LOWER(COALESCE(vendor_name, '')) LIKE LOWER(?1)
                              OR LOWER(COALESCE(bu, '')) LIKE LOWER(?1)
                 ORDER BY vendor_name
                 LIMIT 50"
            )
            .map_err(|e| {
                println!("❌ Erro ao preparar statement: {}", e);
                format!("Erro ao preparar query: {}", e)
            })?;

        println!("📝 Statement preparado com sucesso");

        let suppliers_result = stmt
            .query_map([&search_pattern], |row| {
                // Lê os campos na ordem do SELECT
                let supplier_id_value: String = row.get(0)?;
                let supplier_po_value: String = row.get(1)?;
                let vendor_name_value: String = row.get(2)?;
                let bu: Option<String> = row.get(3).ok();
                let supplier_email: Option<String> = row.get(4).ok();
                let supplier_status: Option<String> = row.get(5).ok();
                let planner: Option<String> = row.get(6).ok();
                let country: Option<String> = row.get(7).ok();
                let supplier_category: Option<String> = row.get(8).ok();
                let continuity: Option<String> = row.get(9).ok();
                let sourcing: Option<String> = row.get(10).ok();
                let sqie: Option<String> = row.get(11).ok();
                let ssid: Option<String> = row.get(12).ok();
                
                Ok(Supplier {
                    supplier_id: supplier_id_value,
                    supplier_po: Some(supplier_po_value),
                    supplier_name: vendor_name_value,
                    bu,
                    supplier_email,
                    supplier_status,
                    planner,
                    country,
                    supplier_category,
                    continuity,
                    sourcing,
                    sqie,
                    ssid,
                    otif_target: None,
                    nil_target: None,
                    pickup_target: None,
                    package_target: None,
                    otif_score: None,
                    nil_score: None,
                    pickup_score: None,
                    package_score: None,
                    total_score: None,
                })
            })
            .map_err(|e| {
                println!("❌ Erro ao executar query_map: {}", e);
                format!("Erro ao executar query: {}", e)
            })?;

        println!("🔄 Processando resultados...");
        
        let mut suppliers = Vec::new();
        for (idx, result) in suppliers_result.enumerate() {
            println!("🔄 Processando resultado #{}", idx + 1);
            match result {
                Ok(supplier) => {
                    println!("✅ Fornecedor {}: ID='{}', PO={:?}, Nome='{}'", 
                        idx + 1, 
                        supplier.supplier_id, 
                        supplier.supplier_po,
                        supplier.supplier_name
                    );
                    if !supplier.supplier_name.is_empty() {
                        suppliers.push(supplier);
                    } else {
                        println!("⚠️ Fornecedor {} tem nome vazio, ignorando", idx + 1);
                    }
                }
                Err(e) => {
                    println!("❌ Erro ao processar fornecedor {}: {}", idx + 1, e);
                }
            }
        }

        println!("\n✅ ========================================");
        println!("✅ Total de fornecedores retornados: {}", suppliers.len());
        println!("✅ ========================================\n");
        Ok(suppliers)
    }

    /// Obtém todos os fornecedores por status (Active ou Active + Inactive)
    pub fn get_all_suppliers_by_status(include_inactive: bool) -> Result<Vec<Supplier>, String> {
        println!("\n🔍 ========================================");
        println!("🔍 GET_ALL_SUPPLIERS_BY_STATUS CHAMADO!");
        println!("🔍 Include Inactive: {}", include_inactive);
        println!("🔍 ========================================\n");
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            println!("❌ Conexão não inicializada");
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        let query = if include_inactive {
            "SELECT DISTINCT 
                COALESCE(CAST(supplier_id AS TEXT), '') as supplier_id,
                COALESCE(CAST(supplier_po AS TEXT), '') as supplier_po, 
                COALESCE(vendor_name, '') as vendor_name,
                bu,
                supplier_email,
                supplier_status,
                planner,
                country,
                supplier_category,
                continuity,
                sourcing,
                sqie,
                ssid
            FROM supplier_database_table 
            WHERE LOWER(COALESCE(supplier_status, '')) IN ('active', 'inactive')
            ORDER BY vendor_name"
        } else {
            "SELECT DISTINCT 
                COALESCE(CAST(supplier_id AS TEXT), '') as supplier_id,
                COALESCE(CAST(supplier_po AS TEXT), '') as supplier_po, 
                COALESCE(vendor_name, '') as vendor_name,
                bu,
                supplier_email,
                supplier_status,
                planner,
                country,
                supplier_category,
                continuity,
                sourcing,
                sqie,
                ssid
            FROM supplier_database_table 
            WHERE LOWER(COALESCE(supplier_status, '')) = 'active'
            ORDER BY vendor_name"
        };
        
        println!("📝 Executando query...");
        
        let mut stmt = conn
            .prepare(query)
            .map_err(|e| {
                println!("❌ Erro ao preparar statement: {}", e);
                format!("Erro ao preparar query: {}", e)
            })?;

        let suppliers_result = stmt
            .query_map([], |row| {
                let supplier_id_value: String = row.get(0)?;
                let supplier_po_value: String = row.get(1)?;
                let vendor_name_value: String = row.get(2)?;
                let bu: Option<String> = row.get(3).ok();
                let supplier_email: Option<String> = row.get(4).ok();
                let supplier_status: Option<String> = row.get(5).ok();
                let planner: Option<String> = row.get(6).ok();
                let country: Option<String> = row.get(7).ok();
                let supplier_category: Option<String> = row.get(8).ok();
                let continuity: Option<String> = row.get(9).ok();
                let sourcing: Option<String> = row.get(10).ok();
                let sqie: Option<String> = row.get(11).ok();
                let ssid: Option<String> = row.get(12).ok();
                
                Ok(Supplier {
                    supplier_id: supplier_id_value,
                    supplier_po: Some(supplier_po_value),
                    supplier_name: vendor_name_value,
                    bu,
                    supplier_email,
                    supplier_status,
                    planner,
                    country,
                    supplier_category,
                    continuity,
                    sourcing,
                    sqie,
                    ssid,
                    otif_target: None,
                    nil_target: None,
                    pickup_target: None,
                    package_target: None,
                    otif_score: None,
                    nil_score: None,
                    pickup_score: None,
                    package_score: None,
                    total_score: None,
                })
            })
            .map_err(|e| {
                println!("❌ Erro ao executar query_map: {}", e);
                format!("Erro ao executar query: {}", e)
            })?;

        let mut suppliers = Vec::new();
        for result in suppliers_result {
            if let Ok(supplier) = result {
                if !supplier.supplier_name.is_empty() {
                    suppliers.push(supplier);
                }
            }
        }

        println!("\n✅ ========================================");
        println!("✅ Total de fornecedores retornados: {}", suppliers.len());
        println!("✅ ========================================\n");
        Ok(suppliers)
    }

    /// Obtém dados completos de um fornecedor
    pub fn get_supplier(supplier_id: String) -> Result<Option<Supplier>, String> {
        println!("\n📋 Buscando fornecedor: {}", supplier_id);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn
            .prepare(
                "SELECT DISTINCT 
                    COALESCE(CAST(supplier_id AS TEXT), '') as supplier_id,
                    COALESCE(CAST(supplier_po AS TEXT), '') as supplier_po, 
                    COALESCE(vendor_name, '') as vendor_name,
                    bu,
                    supplier_email,
                    supplier_status,
                    planner,
                    country,
                    supplier_category,
                    continuity,
                    sourcing,
                    sqie,
                    ssid
                 FROM supplier_database_table 
                 WHERE COALESCE(CAST(supplier_po AS TEXT), '') = ?1
                 LIMIT 1"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let mut rows = stmt
            .query_map([&supplier_id], |row| {
                let supplier_id_value: String = row.get(0)?;
                let supplier_po_value: String = row.get(1)?;
                let vendor_name_value: String = row.get(2)?;
                let bu: Option<String> = row.get(3).ok();
                let supplier_email: Option<String> = row.get(4).ok();
                let supplier_status: Option<String> = row.get(5).ok();
                let planner: Option<String> = row.get(6).ok();
                let country: Option<String> = row.get(7).ok();
                let supplier_category: Option<String> = row.get(8).ok();
                let continuity: Option<String> = row.get(9).ok();
                let sourcing: Option<String> = row.get(10).ok();
                let sqie: Option<String> = row.get(11).ok();
                let ssid: Option<String> = row.get(12).ok();
                
                Ok(Supplier {
                    supplier_id: supplier_id_value,
                    supplier_po: Some(supplier_po_value),
                    supplier_name: vendor_name_value,
                    bu,
                    supplier_email,
                    supplier_status,
                    planner,
                    country,
                    supplier_category,
                    continuity,
                    sourcing,
                    sqie,
                    ssid,
                    otif_target: None,
                    nil_target: None,
                    pickup_target: None,
                    package_target: None,
                    otif_score: None,
                    nil_score: None,
                    pickup_score: None,
                    package_score: None,
                    total_score: None,
                })
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?;

        let result = rows.next().transpose().map_err(|e| format!("Erro ao obter resultado: {}", e))?;
        Ok(result)
    }

    /// Atualiza dados do fornecedor
    pub fn update_supplier(supplier: SupplierUpdate) -> Result<(), String> {
        println!("\n💾 Atualizando fornecedor: {}", supplier.supplier_id);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        let has_vendor_name = Self::supplier_table_has_column(conn, "vendor_name")?;
        let has_supplier_name = Self::supplier_table_has_column(conn, "supplier_name")?;

        let mut set_clauses: Vec<String> = Vec::new();

        if has_vendor_name {
            set_clauses.push("vendor_name = :supplier_name".to_string());
        }

        if has_supplier_name {
            set_clauses.push("supplier_name = :supplier_name".to_string());
        }

        set_clauses.extend([
            "supplier_po = :supplier_po",
            "bu = :bu",
            "supplier_email = :supplier_email",
            "supplier_status = :supplier_status",
            "planner = :planner",
            "country = :country",
            "supplier_category = :supplier_category",
            "continuity = :continuity",
            "sourcing = :sourcing",
            "sqie = :sqie",
            "ssid = :ssid",
        ]
        .iter()
        .map(|s| s.to_string()));

        let sql = format!(
            "UPDATE supplier_database_table SET {} WHERE COALESCE(CAST(supplier_id AS TEXT), '') = :supplier_id",
            set_clauses.join(", ")
        );
        
        // Atualiza todos os campos do fornecedor
        let rows_affected = conn
            .execute(
                &sql,
                rusqlite::named_params! {
                    ":supplier_id": &supplier.supplier_id,
                    ":supplier_name": &supplier.supplier_name,
                    ":supplier_po": &supplier.supplier_po,
                    ":bu": &supplier.bu,
                    ":supplier_email": &supplier.supplier_email,
                    ":supplier_status": &supplier.supplier_status,
                    ":planner": &supplier.planner,
                    ":country": &supplier.country,
                    ":supplier_category": &supplier.supplier_category,
                    ":continuity": &supplier.continuity,
                    ":sourcing": &supplier.sourcing,
                    ":sqie": &supplier.sqie,
                    ":ssid": &supplier.ssid,
                }
            )
            .map_err(|e| format!("Erro ao atualizar fornecedor: {}", e))?;

        println!("✅ {} registros atualizados", rows_affected);
        Ok(())
    }

    /// Cria um novo fornecedor
    pub fn create_supplier(supplier: SupplierUpdate) -> Result<(), String> {
        println!("\n💾 Criando novo fornecedor: {}", supplier.supplier_name);
        println!("📋 Dados do fornecedor:");
        println!("  - ID: {}", supplier.supplier_id);
        println!("  - Nome: {}", supplier.supplier_name);
        println!("  - PO: {:?}", supplier.supplier_po);
        println!("  - País: {:?}", supplier.country);
        
        println!("🔌 Obtendo conexão com banco de dados...");
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            println!("❌ Conexão não inicializada");
            return Err("Conexão não inicializada".to_string());
        }
        println!("✅ Conexão obtida com sucesso");

        let conn = conn_guard.as_ref().unwrap();
        
        println!("📝 Executando INSERT...");
        
        // IMPORTANTE: 
        // - supplier_id é INTEGER PRIMARY KEY (auto-incremento, não incluir no INSERT)
        // - supplier_name, bu, supplier_category, supplier_email são NOT NULL (obrigatórios)
        // - supplier_po é INTEGER (não TEXT)
        // - vendor_name e supplier_name são colunas diferentes (ambas existem)
        
        // Validar campos obrigatórios
        let supplier_name_val = if supplier.supplier_name.trim().is_empty() {
            return Err("Nome do fornecedor é obrigatório".to_string());
        } else {
            &supplier.supplier_name
        };
        
        let bu_val = supplier.bu.as_ref()
            .and_then(|s| if s.trim().is_empty() { None } else { Some(s.as_str()) })
            .unwrap_or("N/A");
            
        let category_val = supplier.supplier_category.as_ref()
            .and_then(|s| if s.trim().is_empty() { None } else { Some(s.as_str()) })
            .unwrap_or("N/A");
            
        let email_val = supplier.supplier_email.as_ref()
            .and_then(|s| if s.trim().is_empty() { None } else { Some(s.as_str()) })
            .unwrap_or("");
        
        // Converter supplier_po para INTEGER (se vazio, usa NULL)
        let po_val: Option<i32> = supplier.supplier_po.as_ref()
            .and_then(|s| s.trim().parse::<i32>().ok());
        
        println!("  ✓ Nome: {}", supplier_name_val);
        println!("  ✓ BU: {}", bu_val);
        println!("  ✓ Categoria: {}", category_val);
        println!("  ✓ Email: {}", email_val);
        println!("  ✓ PO: {:?}", po_val);
        
        let result = conn
            .execute(
                "INSERT INTO supplier_database_table (
                    vendor_name,
                    supplier_name,
                    bu,
                    supplier_category,
                    supplier_email,
                    supplier_po,
                    supplier_status,
                    planner,
                    country,
                    continuity,
                    sourcing,
                    sqie,
                    ssid
                ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)",
                rusqlite::params![
                    supplier_name_val,     // vendor_name
                    supplier_name_val,     // supplier_name
                    bu_val,                // bu (NOT NULL)
                    category_val,          // supplier_category (NOT NULL)
                    email_val,             // supplier_email (NOT NULL)
                    po_val,                // supplier_po (INTEGER)
                    supplier.supplier_status.as_deref().unwrap_or(""),
                    supplier.planner.as_deref().unwrap_or(""),
                    supplier.country.as_deref().unwrap_or(""),
                    supplier.continuity.as_deref().unwrap_or(""),
                    supplier.sourcing.as_deref().unwrap_or(""),
                    supplier.sqie.as_deref().unwrap_or(""),
                    supplier.ssid.as_deref().unwrap_or(""),
                ]
            )
        .map_err(|e| {
            println!("❌ Erro ao executar INSERT: {}", e);
            format!("Erro ao criar fornecedor: {}", e)
        })?;

        println!("✅ INSERT executado. Linhas afetadas: {}", result);
        println!("✅ Fornecedor criado com sucesso");
        Ok(())
    }

    /// Verifica se um PO já existe (exceto para o fornecedor atual)
    pub fn check_po_exists(po: &str, current_supplier_id: &str) -> Result<Option<Supplier>, String> {
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn
            .prepare(
                "SELECT 
                    COALESCE(CAST(supplier_id AS TEXT), '') as supplier_id,
                    supplier_po,
                    vendor_name,
                    bu,
                    supplier_email,
                    supplier_status,
                    planner,
                    country,
                    supplier_category,
                    continuity,
                    sourcing,
                    sqie,
                    ssid
                FROM supplier_database_table
                WHERE supplier_po = ?1 AND COALESCE(CAST(supplier_id AS TEXT), '') != ?2
                LIMIT 1"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let result = stmt
            .query_row(rusqlite::params![po, current_supplier_id], |row| {
                Ok(Supplier {
                    supplier_id: row.get(0)?,
                    supplier_po: row.get(1)?,
                    supplier_name: row.get(2)?,
                    bu: row.get(3)?,
                    supplier_email: row.get(4)?,
                    supplier_status: row.get(5)?,
                    planner: row.get(6)?,
                    country: row.get(7)?,
                    supplier_category: row.get(8)?,
                    continuity: row.get(9)?,
                    sourcing: row.get(10)?,
                    sqie: row.get(11)?,
                    ssid: row.get(12)?,
                    otif_target: None,
                    nil_target: None,
                    pickup_target: None,
                    package_target: None,
                    otif_score: None,
                    nil_score: None,
                    pickup_score: None,
                    package_score: None,
                    total_score: None,
                })
            })
            .optional()
            .map_err(|e| format!("Erro ao verificar PO: {}", e))?;

        Ok(result)
    }

    /// Verifica o schema da tabela supplier_database_table
    pub fn check_table_schema() -> Result<(), String> {
        println!("\n🔍 Verificando schema da tabela supplier_database_table...");
        
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn
            .prepare("SELECT sql FROM sqlite_master WHERE type='table' AND name='supplier_database_table'")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let schema: String = stmt.query_row([], |row| row.get(0))
            .map_err(|e| format!("Erro ao obter schema: {}", e))?;
        
        println!("📋 Schema atual da tabela:");
        println!("{}", schema);
        
        Ok(())
    }

    /// Debug detalhado da estrutura da tabela supplier_database_table
    pub fn debug_supplier_table() -> Result<String, String> {
        println!("\n🔍 [DEBUG] Analisando tabela supplier_database_table...");
        
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut result = String::new();
        
        // 1. Pega o schema da tabela
        result.push_str("=== SCHEMA DA TABELA ===\n");
        let mut stmt = conn
            .prepare("SELECT sql FROM sqlite_master WHERE type='table' AND name='supplier_database_table'")
            .map_err(|e| format!("Erro ao obter schema: {}", e))?;
        
        let schema: String = stmt.query_row([], |row| row.get(0))
            .map_err(|e| format!("Erro ao ler schema: {}", e))?;
        result.push_str(&format!("{}\n\n", schema));
        
        // 2. Pega informações detalhadas de cada coluna
        result.push_str("=== COLUNAS (PRAGMA table_info) ===\n");
        let mut stmt = conn
            .prepare("PRAGMA table_info(supplier_database_table)")
            .map_err(|e| format!("Erro ao obter colunas: {}", e))?;
        
        let mut rows = stmt.query([])
            .map_err(|e| format!("Erro ao executar PRAGMA: {}", e))?;
        
        while let Some(row) = rows.next().map_err(|e| format!("Erro ao iterar: {}", e))? {
            let cid: i32 = row.get(0).unwrap_or(-1);
            let name: String = row.get(1).unwrap_or_else(|_| "?".to_string());
            let col_type: String = row.get(2).unwrap_or_else(|_| "?".to_string());
            let notnull: i32 = row.get(3).unwrap_or(0);
            let dflt_value: Option<String> = row.get(4).ok();
            let pk: i32 = row.get(5).unwrap_or(0);
            
            result.push_str(&format!(
                "  [{}] {} | Tipo: {} | NOT NULL: {} | Default: {:?} | PK: {}\n",
                cid, name, col_type, notnull, dflt_value, pk
            ));
        }
        
        // 3. Conta quantos registros tem na tabela
        result.push_str("\n=== ESTATÍSTICAS ===\n");
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM supplier_database_table",
            [],
            |row| row.get(0)
        ).unwrap_or(0);
        result.push_str(&format!("Total de registros: {}\n", count));
        
        println!("{}", result);
        Ok(result)
    }

    /// Atualiza os critérios de avaliação
    pub fn update_criteria(criteria: Vec<Criteria>) -> Result<(), String> {
        println!("\n💾 Atualizando critérios...");
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        // Processa cada critério
        for c in criteria {
            let is_target = c.criteria_name.to_lowercase().contains("target");
            
            // Usa criteria_target se for target, criteria_weight se for weight
            let value_to_save = if is_target {
                c.criteria_target
            } else {
                c.criteria_weight
            };
            
            let value_str = value_to_save.to_string();
            
            conn.execute(
                "UPDATE criteria_table SET value = ?1 WHERE criteria_id = ?2",
                rusqlite::params![value_str, c.criteria_id],
            )
            .map_err(|e| format!("Erro ao atualizar ID {}: {}", c.criteria_id, e))?;
            
            if is_target {
                println!("✅ Target (ID {}) atualizado para: {}", c.criteria_id, value_to_save);
            } else {
                println!("✅ Weight (ID {}) atualizado para: {}", c.criteria_id, value_to_save);
            }
        }

        println!("✅ Critérios atualizados com sucesso!");
        Ok(())
    }

    /// Busca lista de planners
    pub fn get_planners() -> Result<Vec<String>, String> {
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn.prepare("SELECT DISTINCT name FROM planner_table WHERE name IS NOT NULL ORDER BY name")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let names = stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<String>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(names)
    }

    /// Busca lista de continuity
    pub fn get_continuity_options() -> Result<Vec<String>, String> {
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn.prepare("SELECT DISTINCT name FROM continuity_table WHERE name IS NOT NULL ORDER BY name")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let names = stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<String>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(names)
    }

    /// Busca lista de sourcing
    pub fn get_sourcing_options() -> Result<Vec<String>, String> {
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn.prepare("SELECT DISTINCT name FROM sourcing_table WHERE name IS NOT NULL ORDER BY name")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let names = stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<String>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(names)
    }

    /// Busca lista de SQIE
    pub fn get_sqie_options() -> Result<Vec<String>, String> {
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn.prepare("SELECT DISTINCT name FROM sqie_table WHERE name IS NOT NULL ORDER BY name")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let names = stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<String>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(names)
    }

    /// Busca lista de Business Units
    pub fn get_business_units() -> Result<Vec<String>, String> {
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn.prepare("SELECT DISTINCT bu FROM business_unit_table WHERE bu IS NOT NULL ORDER BY bu")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let names = stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<String>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(names)
    }

    /// Busca lista de Categorias
    pub fn get_categories() -> Result<Vec<String>, String> {
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn.prepare("SELECT DISTINCT category FROM categories_table WHERE category IS NOT NULL ORDER BY category")
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let names = stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<String>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(names)
    }

    // ========== LISTS MANAGEMENT ==========

    /// Obter todos os itens de uma tabela com 3 campos (name, alias, email)
    pub fn get_list_items_three_fields(table_name: &str) -> Result<Vec<ListItemThreeFields>, String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("SELECT name, alias, email FROM {}", table_name);
        
        let mut stmt = conn.prepare(&query)
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let items = stmt.query_map([], |row| {
            Ok(ListItemThreeFields {
                name: row.get(0)?,
                alias: row.get(1)?,
                email: row.get(2)?,
            })
        })
        .map_err(|e| format!("Erro ao executar query: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(items)
    }

    /// Adicionar item em tabela com 3 campos
    pub fn add_list_item_three_fields(table_name: &str, item: ListItemThreeFields) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("INSERT INTO {} (name, alias, email) VALUES (?1, ?2, ?3)", table_name);
        
        conn.execute(&query, rusqlite::params![item.name, item.alias, item.email])
            .map_err(|e| format!("Erro ao inserir item: {}", e))?;
        
        Ok(())
    }

    /// Atualizar item em tabela com 3 campos
    pub fn update_list_item_three_fields(table_name: &str, old_name: &str, item: ListItemThreeFields) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("UPDATE {} SET name = ?1, alias = ?2, email = ?3 WHERE name = ?4", table_name);
        
        conn.execute(&query, rusqlite::params![item.name, item.alias, item.email, old_name])
            .map_err(|e| format!("Erro ao atualizar item: {}", e))?;
        
        Ok(())
    }

    /// Deletar item em tabela com 3 campos
    pub fn delete_list_item_three_fields(table_name: &str, name: &str) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("DELETE FROM {} WHERE name = ?1", table_name);
        
        conn.execute(&query, rusqlite::params![name])
            .map_err(|e| format!("Erro ao deletar item: {}", e))?;
        
        Ok(())
    }

    /// Obter todos os itens de uma tabela com 1 campo (name)
    pub fn get_list_items_single_field(table_name: &str, field_name: &str) -> Result<Vec<ListItemSingleField>, String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("SELECT {} FROM {}", field_name, table_name);
        
        let mut stmt = conn.prepare(&query)
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let items = stmt.query_map([], |row| {
            Ok(ListItemSingleField {
                name: row.get(0)?,
            })
        })
        .map_err(|e| format!("Erro ao executar query: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        Ok(items)
    }

    /// Adicionar item em tabela com 1 campo
    pub fn add_list_item_single_field(table_name: &str, field_name: &str, name: String) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("INSERT INTO {} ({}) VALUES (?1)", table_name, field_name);
        
        conn.execute(&query, rusqlite::params![name])
            .map_err(|e| format!("Erro ao inserir item: {}", e))?;
        
        Ok(())
    }

    /// Atualizar item em tabela com 1 campo
    pub fn update_list_item_single_field(table_name: &str, field_name: &str, old_name: &str, new_name: String) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("UPDATE {} SET {} = ?1 WHERE {} = ?2", table_name, field_name, field_name);
        
        conn.execute(&query, rusqlite::params![new_name, old_name])
            .map_err(|e| format!("Erro ao atualizar item: {}", e))?;
        
        Ok(())
    }

    /// Deletar item em tabela com 1 campo
    pub fn delete_list_item_single_field(table_name: &str, field_name: &str, name: &str) -> Result<(), String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let query = format!("DELETE FROM {} WHERE {} = ?1", table_name, field_name);
        
        conn.execute(&query, rusqlite::params![name])
            .map_err(|e| format!("Erro ao deletar item: {}", e))?;
        
        Ok(())
    }

    /// Conta o número de usuários online (is_online = 1)
    pub fn get_online_users_count() -> Result<i32, String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let count: i32 = conn.query_row(
            "SELECT COUNT(*) FROM users_table WHERE is_online = 1",
            [],
            |row| row.get(0)
        )
        .map_err(|e| format!("Erro ao contar usuários online: {}", e))?;
        
        Ok(count)
    }

    /// Atualiza o status online de um usuário
    pub fn set_user_online_status(user_id: i32, is_online: bool) -> Result<(), String> {
        println!("🔄 set_user_online_status - user_id: {}, is_online: {}", user_id, is_online);
        
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let online_value = if is_online { 1 } else { 0 };
        
        let rows_affected = conn.execute(
            "UPDATE users_table SET is_online = ?1 WHERE user_id = ?2",
            rusqlite::params![online_value, user_id]
        )
        .map_err(|e| format!("Erro ao atualizar status online: {}", e))?;
        
        println!("✅ set_user_online_status concluído - {} linha(s) afetada(s)", rows_affected);
        
        Ok(())
    }

    /// Reseta todos os usuários para offline (is_online = 0)
    /// Deve ser chamado ao iniciar a aplicação
    pub fn reset_all_users_offline() -> Result<(), String> {
        println!("🔄 reset_all_users_offline - Iniciando...");
        
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let rows_affected = conn.execute(
            "UPDATE users_table SET is_online = 0",
            []
        )
        .map_err(|e| format!("Erro ao resetar status online dos usuários: {}", e))?;
        
        println!("✅ reset_all_users_offline concluído - {} usuário(s) atualizado(s)", rows_affected);
        Ok(())
    }

    /// Busca scores pendentes de avaliação para um usuário baseado em suas permissões
    pub fn get_pending_scores(user_id: i32) -> Result<Vec<serde_json::Value>, String> {
        println!("\n� ========================================");
        println!("🔔 GET_PENDING_SCORES");
        println!("🔔 user_id: {}", user_id);
        println!("🔔 ========================================\n");

        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;

        // PERMISSÕES DO USUÁRIO (podem estar como TEXT ou INTEGER no SQLite)
        let permissions = conn.query_row(
            "SELECT CAST(otif AS INTEGER), CAST(nil AS INTEGER), CAST(pickup AS INTEGER), CAST(package AS INTEGER) FROM users_table WHERE user_id = ?1",
            [user_id],
            |row| {
                Ok((
                    row.get::<_, i32>(0)?, // otif
                    row.get::<_, i32>(1)?, // nil
                    row.get::<_, i32>(2)?, // pickup
                    row.get::<_, i32>(3)?, // package
                ))
            }
        ).map_err(|e| format!("Erro ao buscar permissões do usuário: {}", e))?;

        println!("👤 Permissões do usuário (1=pode editar, 0=não pode):");
        println!("   OTIF: {} (pode editar: {})", permissions.0, permissions.0 == 1);
        println!("   NIL: {} (pode editar: {})", permissions.1, permissions.1 == 1);
        println!("   Pickup: {} (pode editar: {})", permissions.2, permissions.2 == 1);
        println!("   Package: {} (pode editar: {})", permissions.3, permissions.3 == 1);

        let can_edit_otif = permissions.0 == 1;
        let can_edit_nil = permissions.1 == 1;
        let can_edit_pickup = permissions.2 == 1;
        let can_edit_package = permissions.3 == 1;

        if !can_edit_otif && !can_edit_nil && !can_edit_pickup && !can_edit_package {
            println!("❌ Usuário sem permissões de edição - retornando vazio");
            return Ok(Vec::new());
        }

        println!("\n📊 Buscando registros com campos NULL ou vazios...\n");

        // Busca registros com qualquer campo pendente (NULL ou vazio)
        let query = "
            SELECT 
                r.id,
                r.supplier_id,
                COALESCE(r.supplier_name, s.vendor_name, '') AS supplier_name,
                r.month,
                r.year,
                CASE WHEN r.otif IS NULL THEN NULL ELSE CAST(r.otif AS TEXT) END AS otif_value,
                CASE WHEN r.nil IS NULL THEN NULL ELSE CAST(r.nil AS TEXT) END AS nil_value,
                CASE WHEN r.quality_pickup IS NULL THEN NULL ELSE r.quality_pickup END AS pickup_value,
                CASE WHEN r.quality_package IS NULL THEN NULL ELSE r.quality_package END AS package_value
            FROM supplier_score_records_table r
            LEFT JOIN supplier_database_table s ON s.supplier_id = r.supplier_id
            WHERE (
                r.otif IS NULL OR CAST(r.otif AS TEXT) = '' OR
                r.nil IS NULL OR CAST(r.nil AS TEXT) = '' OR
                r.quality_pickup IS NULL OR r.quality_pickup = '' OR
                r.quality_package IS NULL OR r.quality_package = ''
            )
            ORDER BY r.year DESC, r.month DESC, supplier_name
            LIMIT 150
        ";

        let mut stmt = conn
            .prepare(query)
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let rows = stmt
            .query_map([], |row| {
                let record_id: i32 = row.get(0)?;
                let supplier_id: String = row.get(1)?;
                let supplier_name: String = row.get(2)?;
                let month: String = row.get(3)?;
                let year: String = row.get(4)?;

                let otif_value: Option<String> = row.get(5).ok();
                let nil_value: Option<String> = row.get(6).ok();
                let pickup_value: Option<String> = row.get(7).ok();
                let package_value: Option<String> = row.get(8).ok();

                let otif_empty = otif_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);
                let nil_empty = nil_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);
                let pickup_empty = pickup_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);
                let package_empty = package_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);

                // LOG DETALHADO DE CADA REGISTRO
                println!("📦 Registro ID: {} | Supplier: {} | {}/{}", record_id, supplier_name, month, year);
                println!("   OTIF: {:?} (empty: {}) | NIL: {:?} (empty: {})", otif_value, otif_empty, nil_value, nil_empty);
                println!("   Pickup: {:?} (empty: {}) | Package: {:?} (empty: {})", pickup_value, pickup_empty, package_value, package_empty);

                let mut pending_for_user: Vec<&str> = Vec::new();
                if can_edit_otif && otif_empty {
                    pending_for_user.push("OTIF");
                }
                if can_edit_nil && nil_empty {
                    pending_for_user.push("NIL");
                }
                if can_edit_pickup && pickup_empty {
                    pending_for_user.push("Pickup");
                }
                if can_edit_package && package_empty {
                    pending_for_user.push("Package");
                }

                if pending_for_user.is_empty() {
                    println!("   ⚠️ Nenhum campo que o usuário pode preencher - IGNORADO\n");
                    return Ok(None);
                }

                println!("   ✅ Campos que o usuário pode preencher: {:?}\n", pending_for_user);

                Ok(Some(serde_json::json!({
                    "record_id": record_id,
                    "supplier_id": supplier_id,
                    "supplier_name": supplier_name,
                    "month": month,
                    "year": year,
                    "pending_fields": pending_for_user,
                })))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?;

        let mut results = Vec::new();
        for row_result in rows {
            match row_result {
                Ok(Some(value)) => results.push(value),
                Ok(None) => {},
                Err(e) => return Err(format!("Erro ao processar registro pendente: {}", e)),
            }
        }

        println!("🔔 ========================================");
        println!("🔔 TOTAL DE NOTIFICAÇÕES: {}", results.len());
        println!("🔔 ========================================\n");

        Ok(results)
    }

    /// Salva um score individual usando o ID do registro
    pub fn save_individual_score(
        record_id: i32,  // Mudei para usar o ID direto
        score_type: String,  // "otif", "nil", "pickup", "package"
        score_value: String,
        user_name: String,
    ) -> Result<String, String> {
        println!("\n💾 Salvando score individual...");
        println!("  Record ID: {}", record_id);
        println!("  Tipo: {}, Valor: {}", score_type, score_value);
        
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;

        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        // Determina qual coluna atualizar
        let column_name = match score_type.as_str() {
            "otif" => "otif",
            "nil" => "nil",
            "pickup" => "quality_pickup",
            "package" => "quality_package",
            _ => return Err(format!("Tipo de score inválido: {}", score_type)),
        };

        // Atualiza apenas a coluna específica usando o ID
        let query = format!(
            "UPDATE supplier_score_records_table 
             SET {} = ?1, change_date = ?2, changed_by = ?3
             WHERE id = ?4",
            column_name
        );

        let rows_affected = if score_type == "otif" || score_type == "nil" {
            // OTIF e NIL são REAL
            let score_numeric = score_value.parse::<f64>()
                .map_err(|_| format!("Valor inválido para {}: {}", score_type, score_value))?;
            
            conn.execute(
                &query,
                rusqlite::params![score_numeric, now, user_name, record_id],
            )
        } else {
            // Pickup e Package são TEXT
            conn.execute(
                &query,
                rusqlite::params![score_value, now, user_name, record_id],
            )
        }.map_err(|e| format!("Erro ao atualizar score: {}", e))?;

        if rows_affected > 0 {
            println!("✅ Score atualizado com sucesso!");
            
            // Busca supplier_id, month, year do registro para recalcular total
            let (supplier_id, month, year): (String, String, String) = conn.query_row(
                "SELECT supplier_id, month, year FROM supplier_score_records_table WHERE id = ?1",
                [record_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?))
            ).map_err(|e| format!("Erro ao buscar dados do registro: {}", e))?;
            
            // Recalcula o total_score
            Self::recalculate_total_score_with_conn(conn, &supplier_id, &month, &year)?;
            
            Ok(format!("Score {} atualizado com sucesso", score_type))
        } else {
            Err("Nenhum registro foi atualizado".to_string())
        }
    }

    /// Recalcula o total_score de um registro (com conexão externa)
    fn recalculate_total_score_with_conn(
        conn: &rusqlite::Connection,
        supplier_id: &str, 
        month: &str, 
        year: &str
    ) -> Result<(), String> {

        // Busca os scores atuais
        let (otif, nil, pickup, package) = conn.query_row(
            "SELECT otif, nil, quality_pickup, quality_package 
             FROM supplier_score_records_table 
             WHERE supplier_id = ?1 AND month = ?2 AND year = ?3",
            rusqlite::params![supplier_id, month, year],
            |row| {
                Ok((
                    row.get::<_, Option<f64>>(0)?,
                    row.get::<_, Option<f64>>(1)?,
                    row.get::<_, Option<String>>(2)?,
                    row.get::<_, Option<String>>(3)?,
                ))
            }
        ).map_err(|e| format!("Erro ao buscar scores: {}", e))?;

        // Busca os pesos dos critérios
        let mut weights = std::collections::HashMap::new();
        weights.insert("otif", 25.0);
        weights.insert("nil", 25.0);
        weights.insert("pickup", 25.0);
        weights.insert("package", 25.0);

        // Calcula total
        let mut total = 0.0;
        let mut count = 0.0;

        if let Some(v) = otif {
            total += v * (weights["otif"] / 100.0);
            count += weights["otif"] / 100.0;
        }
        if let Some(v) = nil {
            total += v * (weights["nil"] / 100.0);
            count += weights["nil"] / 100.0;
        }
        if let Some(v) = pickup.and_then(|s| s.parse::<f64>().ok()) {
            total += v * (weights["pickup"] / 100.0);
            count += weights["pickup"] / 100.0;
        }
        if let Some(v) = package.and_then(|s| s.parse::<f64>().ok()) {
            total += v * (weights["package"] / 100.0);
            count += weights["package"] / 100.0;
        }

        let total_score = if count > 0.0 {
            format!("{:.2}", total / count)
        } else {
            "0.00".to_string()
        };

        // Atualiza o total_score
        conn.execute(
            "UPDATE supplier_score_records_table 
             SET total_score = ?1 
             WHERE supplier_id = ?2 AND month = ?3 AND year = ?4",
            rusqlite::params![total_score, supplier_id, month, year],
        ).map_err(|e| format!("Erro ao atualizar total_score: {}", e))?;

        println!("✅ Total score recalculado: {}", total_score);
        Ok(())
    }

    /// Função de teste para consultar um registro específico (DEBUG)
    pub fn debug_get_record(record_id: i32) -> Result<String, String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;

        let result = conn.query_row(
            "SELECT id, supplier_id, supplier_name, month, year, otif, nil, quality_pickup, quality_package, total_score 
             FROM supplier_score_records_table 
             WHERE id = ?1",
            [record_id],
            |row| {
                Ok(format!(
                    "ID: {}\nSupplier ID: {}\nSupplier Name: {}\nMonth: {}\nYear: {}\nOTIF: {:?}\nNIL: {:?}\nQuality Pickup: {:?}\nQuality Package: {:?}\nTotal Score: {:?}",
                    row.get::<_, i32>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, Option<f64>>(5)?,
                    row.get::<_, Option<f64>>(6)?,
                    row.get::<_, Option<String>>(7)?,
                    row.get::<_, Option<String>>(8)?,
                    row.get::<_, Option<String>>(9)?
                ))
            }
        ).map_err(|e| format!("Erro ao buscar registro: {}", e))?;

        Ok(result)
    }

    /// Busca os responsáveis (SQIE, Planner, Continuity, Sourcing) de um fornecedor com JOIN
    pub fn get_supplier_responsibles(supplier_id: &str) -> Result<SupplierResponsibles, String> {
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;

        let result = conn.query_row(
            "SELECT 
                s.sqie, sq.name as sqie_name, sq.email as sqie_email,
                s.planner, p.name as planner_name, p.email as planner_email,
                s.continuity, c.name as continuity_name, c.email as continuity_email,
                s.sourcing, so.name as sourcing_name, so.email as sourcing_email
             FROM supplier_database_table s
             LEFT JOIN sqie_list_table sq ON s.sqie = sq.alias
             LEFT JOIN planner_list_table p ON s.planner = p.alias
             LEFT JOIN continuity_list_table c ON s.continuity = c.alias
             LEFT JOIN sourcing_list_table so ON s.sourcing = so.alias
             WHERE s.supplier_id = ?1",
            [supplier_id],
            |row| {
                Ok(SupplierResponsibles {
                    sqie: ResponsibleInfo {
                        alias: row.get(0)?,
                        name: row.get(1)?,
                        email: row.get(2)?,
                    },
                    planner: ResponsibleInfo {
                        alias: row.get(3)?,
                        name: row.get(4)?,
                        email: row.get(5)?,
                    },
                    continuity: ResponsibleInfo {
                        alias: row.get(6)?,
                        name: row.get(7)?,
                        email: row.get(8)?,
                    },
                    sourcing: ResponsibleInfo {
                        alias: row.get(9)?,
                        name: row.get(10)?,
                        email: row.get(11)?,
                    },
                })
            }
        ).optional()
        .map_err(|e| format!("Erro ao buscar responsáveis: {}", e))?
        .ok_or_else(|| "Fornecedor não encontrado".to_string())?;

        Ok(result)
    }
}

/// Estrutura para informações de um responsável
#[derive(Debug, Serialize, Clone)]
pub struct ResponsibleInfo {
    pub alias: Option<String>,
    pub name: Option<String>,
    pub email: Option<String>,
}

/// Estrutura para todos os responsáveis de um fornecedor
#[derive(Debug, Serialize, Clone)]
pub struct SupplierResponsibles {
    pub sqie: ResponsibleInfo,
    pub planner: ResponsibleInfo,
    pub continuity: ResponsibleInfo,
    pub sourcing: ResponsibleInfo,
}

/// Estrutura para itens de lista com 3 campos
#[derive(Debug, Serialize, serde::Deserialize, Clone)]
pub struct ListItemThreeFields {
    pub name: String,
    pub alias: String,
    pub email: String,
}

/// Estrutura para itens de lista com 1 campo
#[derive(Debug, Serialize, serde::Deserialize, Clone)]
pub struct ListItemSingleField {
    pub name: String,
}

/// Estrutura para fornecedores em risco
#[derive(Debug, Serialize, Clone)]
pub struct RiskSupplier {
    pub supplier_id: String,
    pub ssid: Option<String>,
    pub vendor_name: String,
    pub bu: Option<String>,
    pub po: Option<String>,
    pub avg_score: f64,
    pub q1: Option<f64>,
    pub q2: Option<f64>,
    pub q3: Option<f64>,
    pub q4: Option<f64>,
}

impl DatabaseManager {
    /// Busca fornecedores em risco (abaixo da meta) com scores por trimestre
    pub fn get_suppliers_at_risk(year: i32, target: f64) -> Result<Vec<RiskSupplier>, String> {
        println!("\n🔍 Buscando fornecedores em risco - Ano: {}, Meta: {}", year, target);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        let year_str = year.to_string();
        
        // Query com JOIN entre supplier_database_table e supplier_score_records_table
        let query = format!(
            "SELECT 
                CAST(sup.supplier_id AS TEXT) AS supplier_id,
                sup.ssid,
                sup.vendor_name,
                sup.bu,
                CAST(sup.supplier_po AS TEXT) AS supplier_po,
                AVG(CASE WHEN score.month IN ('1','2','3') THEN CAST(score.total_score AS REAL) END) as q1,
                AVG(CASE WHEN score.month IN ('4','5','6') THEN CAST(score.total_score AS REAL) END) as q2,
                AVG(CASE WHEN score.month IN ('7','8','9') THEN CAST(score.total_score AS REAL) END) as q3,
                AVG(CASE WHEN score.month IN ('10','11','12') THEN CAST(score.total_score AS REAL) END) as q4,
                AVG(CAST(score.total_score AS REAL)) as avg_score
            FROM supplier_database_table sup
            INNER JOIN supplier_score_records_table score 
                ON sup.supplier_id = score.supplier_id
            WHERE score.year = '{}' 
                AND score.total_score IS NOT NULL 
                AND score.total_score != ''
            GROUP BY sup.supplier_id, sup.ssid, sup.vendor_name, sup.bu, sup.supplier_po
            HAVING avg_score < {}
            ORDER BY avg_score ASC",
            year_str, target
        );
        
        println!("📋 Query SQL:\n{}", query);
        
        let mut stmt = conn.prepare(&query)
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;
        
        let suppliers = stmt.query_map([], |row| {
            let supplier_id: String = row.get(0)?;
            let ssid: Option<String> = row.get(1)?;
            let vendor_name: String = row.get(2)?;
            let bu: Option<String> = row.get(3)?;
            let po: Option<String> = row.get(4)?;
            let q1: Option<f64> = row.get(5)?;
            let q2: Option<f64> = row.get(6)?;
            let q3: Option<f64> = row.get(7)?;
            let q4: Option<f64> = row.get(8)?;
            let avg_score: f64 = row.get(9)?;
            
            println!("  📊 {} - {} | Média: {:.2} | Q1: {:?} | Q2: {:?} | Q3: {:?} | Q4: {:?}", 
                     supplier_id, vendor_name, avg_score, q1, q2, q3, q4);
            
            Ok(RiskSupplier {
                supplier_id,
                ssid,
                vendor_name,
                bu,
                po,
                q1,
                q2,
                q3,
                q4,
                avg_score,
            })
        })
        .map_err(|e| format!("Erro ao executar query: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;
        
        println!("✅ Encontrados {} fornecedores em risco (abaixo de {})", suppliers.len(), target);
        
        Ok(suppliers)
    }
}
