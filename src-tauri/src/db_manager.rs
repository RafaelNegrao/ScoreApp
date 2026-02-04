// ...existing code...

impl DatabaseManager {
    /// Deleta todos os registros da tabela de logs
    pub fn delete_all_logs() -> Result<(), String> {
        println!("\n⚠️ Deletando todos os registros da tabela log_table...");
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref().ok_or_else(|| "Conexão não inicializada".to_string())?;
        conn.execute("DELETE FROM log_table", []).map_err(|e| format!("Erro ao deletar logs: {}", e))?;
        println!("✅ Todos os registros da tabela log_table foram excluídos.");
        Ok(())
    }
}
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

/// Estrutura para registro de log
#[derive(Debug, Serialize, Clone)]
pub struct LogEntry {
    pub log_id: i32,
    pub date: String,
    pub time: String,
    pub user: String,
    pub event: String,
    pub wwid: String,
    pub place: String,
    pub supplier: Option<String>,
    pub score_date: Option<String>,
    pub old_value: Option<String>,
    pub new_value: Option<String>,
}

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
                
                // Desabilitar WAL mode para não gerar arquivos .wal e .shm
                // Usa DELETE mode (padrão) que é mais simples
                conn.execute_batch("PRAGMA journal_mode = DELETE;")
                    .map_err(|e| format!("Erro ao configurar journal_mode: {}", e))?;
                println!("📝 Journal mode configurado para DELETE (sem arquivos WAL/SHM)");
                
                let mut db = DB_CONNECTION.lock().unwrap();
                *db = Some(conn);
                
                // Se é um banco novo, criar estrutura
                if is_new_db {
                    drop(db); // Libera o lock antes de chamar outras funções
                    Self::create_initial_structure()?;
                } else {
                    drop(db); // Libera o lock antes de chamar a migração
                    Self::migrate_database()?;
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
            "CREATE TABLE IF NOT EXISTS users_table (
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
        ).map_err(|e| format!("Erro ao criar tabela users_table: {}", e))?;
        
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

        // Criar tabela de overrides de pendência (para permitir salvar vazio)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS pending_scores_override (
                record_id INTEGER NOT NULL,
                score_type TEXT NOT NULL,
                dismissed INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (record_id, score_type)
            )",
            [],
        ).map_err(|e| format!("Erro ao criar tabela pending_scores_override: {}", e))?;
        
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

    /// Migra o banco de dados existente para nova estrutura
    fn migrate_database() -> Result<(), String> {
        println!("🔄 Verificando se é necessário migrar banco de dados...");
        
        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();
        
        // Verificar se a coluna supplier existe na log_table
        let has_supplier_column = Self::log_table_has_column(conn, "supplier")?;
        
        if !has_supplier_column {
            println!("📝 Adicionando coluna 'supplier' na tabela log_table...");
            conn.execute(
                "ALTER TABLE log_table ADD COLUMN supplier TEXT",
                [],
            ).map_err(|e| format!("Erro ao adicionar coluna supplier: {}", e))?;
            println!("✅ Coluna 'supplier' adicionada com sucesso!");
        } else {
            println!("✅ Coluna 'supplier' já existe na log_table");
        }

        // Tabela para controle de pendências salvas como vazio
        conn.execute(
            "CREATE TABLE IF NOT EXISTS pending_scores_override (
                record_id INTEGER NOT NULL,
                score_type TEXT NOT NULL,
                dismissed INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (record_id, score_type)
            )",
            [],
        ).map_err(|e| format!("Erro ao criar tabela pending_scores_override: {}", e))?;
        
        // Verificar se a coluna score_date existe na log_table
        let has_score_date_column = Self::log_table_has_column(conn, "score_date")?;
        
        if !has_score_date_column {
            println!("📝 Adicionando coluna 'score_date' na tabela log_table...");
            conn.execute(
                "ALTER TABLE log_table ADD COLUMN score_date TEXT",
                [],
            ).map_err(|e| format!("Erro ao adicionar coluna score_date: {}", e))?;
            println!("✅ Coluna 'score_date' adicionada com sucesso!");
        } else {
            println!("✅ Coluna 'score_date' já existe na log_table");
        }
        
        Ok(())
    }

    /// Verifica se uma coluna existe na tabela de logs
    fn log_table_has_column(conn: &Connection, column_name: &str) -> Result<bool, String> {
        let mut stmt = conn
            .prepare("PRAGMA table_info(log_table)")
            .map_err(|e| format!("Erro ao inspecionar estrutura da tabela de logs: {}", e))?;

        let mut rows = stmt
            .query([])
            .map_err(|e| format!("Erro ao consultar estrutura da tabela de logs: {}", e))?;

        while let Some(row) = rows
            .next()
            .map_err(|e| format!("Erro ao iterar colunas da tabela de logs: {}", e))?
        {
            let col_name: String = row
                .get(1)
                .map_err(|e| format!("Erro ao ler nome da coluna: {}", e))?;

            if col_name.eq_ignore_ascii_case(column_name) {
                return Ok(true);
            }
        }

        Ok(false)
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
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        let mut scores = Vec::new();

        for supplier_id in supplier_ids {
            
            // Nomes reais das colunas no banco:
            // id, supplier_id, month (TEXT), year (TEXT), otif (REAL), nil (REAL), 
            // quality_pickup (TEXT), quality_package (TEXT), total_score (TEXT), comment (TEXT)
            let query = "SELECT id, supplier_id, month, year, otif, nil, quality_pickup, quality_package, total_score, comment 
                         FROM supplier_score_records_table 
                         WHERE lower(trim(supplier_id)) = lower(trim(?1)) AND month = ?2 AND year = ?3";
            
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
                    scores.push(s);
                },
                Err(_e) => {
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
    /// Função auxiliar para inserir log
    fn insert_log(
        conn: &Connection,
        user: &str,
        event: &str,
        wwid: &str,
        place: &str,
        supplier: Option<&str>,
        score_date: Option<&str>,
        old_value: Option<&str>,
        new_value: Option<&str>,
    ) -> Result<(), String> {
        let now = chrono::Local::now();
        let date = now.format("%Y-%m-%d").to_string();
        let time = now.format("%H:%M:%S").to_string();
        
        println!("📝 Inserindo log: event='{}', wwid='{}', place='{}', supplier={:?}, score_date={:?}", 
            event, wwid, place, supplier, score_date);
        
        conn.execute(
            "INSERT INTO log_table (date, time, user, event, wwid, place, supplier, score_date, old_value, new_value)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
            rusqlite::params![
                date,
                time,
                user,
                event,
                wwid,
                place,
                supplier,
                score_date,
                old_value,
                new_value
            ],
        ).map_err(|e| format!("Erro ao inserir log: {}", e))?;
        
        Ok(())
    }

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
        user_wwid: String,
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
        println!("💾 user_wwid: '{}'", user_wwid);
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
        
        println!("🔍 WWID recebido do frontend: '{}'", user_wwid);
        
        // Verifica se já existe um registro e busca valores antigos para o log
        let existing_data = conn.query_row(
            "SELECT id, otif, nil, quality_pickup, quality_package, comment FROM supplier_score_records_table 
             WHERE lower(trim(supplier_id)) = lower(trim(?1)) AND month = ?2 AND year = ?3",
            rusqlite::params![&supplier_id, month.to_string(), year.to_string()],
            |row| {
                Ok((
                    row.get::<_, i32>(0)?,
                    row.get::<_, Option<f64>>(1)?,
                    row.get::<_, Option<f64>>(2)?,
                    row.get::<_, Option<String>>(3)?,
                    row.get::<_, Option<String>>(4)?,
                    row.get::<_, Option<String>>(5)?,
                ))
            }
        );
        
        let supplier_info = format!("{} ({})", supplier_name, supplier_id);
        let score_date_str = format!("{}/{}", month, year);
        
        match existing_data {
            Ok((id, old_otif, old_nil, old_pickup, old_package, old_comment)) => {
                // Registra logs para cada campo alterado
                if let Some(ref new_otif) = otif_score {
                    let old_val = old_otif.map(|v| v.to_string()).unwrap_or_else(|| "".to_string());
                    // Normaliza comparação: converte ambos para f64 e compara
                    let old_normalized = old_otif.unwrap_or(0.0);
                    let new_normalized = new_otif.parse::<f64>().unwrap_or(0.0);
                    
                    if (old_normalized - new_normalized).abs() > 0.001 {
                        Self::insert_log(
                            conn,
                            &user_name,
                            "Update",
                            &user_wwid,
                            "OTIF",
                            Some(&supplier_info),
                            Some(&score_date_str),
                            if old_val.is_empty() { None } else { Some(&old_val) },
                            Some(new_otif)
                        )?;
                    }
                }
                
                if let Some(ref new_nil) = nil_score {
                    let old_val = old_nil.map(|v| v.to_string()).unwrap_or_else(|| "".to_string());
                    // Normaliza comparação: converte ambos para f64 e compara
                    let old_normalized = old_nil.unwrap_or(0.0);
                    let new_normalized = new_nil.parse::<f64>().unwrap_or(0.0);
                    
                    if (old_normalized - new_normalized).abs() > 0.001 {
                        Self::insert_log(
                            conn,
                            &user_name,
                            "Update",
                            &user_wwid,
                            "NIL",
                            Some(&supplier_info),
                            Some(&score_date_str),
                            if old_val.is_empty() { None } else { Some(&old_val) },
                            Some(new_nil)
                        )?;
                    }
                }
                
                if let Some(ref new_pickup) = pickup_score {
                    let old_val = old_pickup.clone().unwrap_or_else(|| "".to_string());
                    // Normaliza comparação: converte ambos para f64 e compara
                    let old_normalized = old_pickup.as_ref().and_then(|s| s.parse::<f64>().ok()).unwrap_or(0.0);
                    let new_normalized = new_pickup.parse::<f64>().unwrap_or(0.0);
                    
                    if (old_normalized - new_normalized).abs() > 0.001 {
                        Self::insert_log(
                            conn,
                            &user_name,
                            "Update",
                            &user_wwid,
                            "Pickup",
                            Some(&supplier_info),
                            Some(&score_date_str),
                            if old_val.is_empty() { None } else { Some(&old_val) },
                            Some(new_pickup)
                        )?;
                    }
                }
                
                if let Some(ref new_package) = package_score {
                    let old_val = old_package.clone().unwrap_or_else(|| "".to_string());
                    // Normaliza comparação: converte ambos para f64 e compara
                    let old_normalized = old_package.as_ref().and_then(|s| s.parse::<f64>().ok()).unwrap_or(0.0);
                    let new_normalized = new_package.parse::<f64>().unwrap_or(0.0);
                    
                    if (old_normalized - new_normalized).abs() > 0.001 {
                        Self::insert_log(
                            conn,
                            &user_name,
                            "Update",
                            &user_wwid,
                            "Package",
                            Some(&supplier_info),
                            Some(&score_date_str),
                            if old_val.is_empty() { None } else { Some(&old_val) },
                            Some(new_package)
                        )?;
                    }
                }
                
                if let Some(ref new_comment) = comments {
                    let old_val = old_comment.clone().unwrap_or_else(|| "".to_string());
                    if old_val != *new_comment && !new_comment.is_empty() {
                        Self::insert_log(
                            conn,
                            &user_name,
                            "Update",
                            &user_wwid,
                            "Comment",
                            Some(&supplier_info),
                            Some(&score_date_str),
                            if old_val.is_empty() { None } else { Some(&old_val) },
                            Some(new_comment)
                        )?;
                    }
                }
                
                // Atualiza o registro existente - APENAS os campos que foram enviados (não nulos)
                println!("📝 Atualizando registro existente (id: {})", id);
                
                // Se está enviando todas as notas e todas estão vazias, deleta o registro
                let all_scores_sent = otif_score.is_some() && nil_score.is_some() && pickup_score.is_some() && package_score.is_some();
                let all_scores_empty = otif_score.as_ref().map(|s| s.trim().is_empty()).unwrap_or(true) 
                    && nil_score.as_ref().map(|s| s.trim().is_empty()).unwrap_or(true)
                    && pickup_score.as_ref().map(|s| s.trim().is_empty()).unwrap_or(true)
                    && package_score.as_ref().map(|s| s.trim().is_empty()).unwrap_or(true);
                
                if all_scores_sent && all_scores_empty {
                    println!("🗑️ Todas as 4 notas estão vazias - Deletando registro (id: {})", id);
                    
                    // Registra log de deleção
                    Self::insert_log(
                        conn,
                        &user_name,
                        "Delete",
                        &user_wwid,
                        "All Scores",
                        Some(&supplier_info),
                        Some(&score_date_str),
                        Some(&format!("OTIF: {:?}, NIL: {:?}, Pickup: {:?}, Package: {:?}", 
                            old_otif, old_nil, old_pickup, old_package)),
                        None
                    )?;
                    
                    conn.execute(
                        "DELETE FROM supplier_score_records_table WHERE id = ?",
                        rusqlite::params![id]
                    ).map_err(|e| format!("Erro ao deletar registro: {}", e))?;
                    
                    println!("✅ Registro deletado com sucesso!");
                    return Ok("Registro deletado (todas as notas removidas)".to_string());
                }
                
                // Monta a query dinamicamente para atualizar apenas os campos enviados
                let mut updates = Vec::new();
                let mut params: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
                
                if let Some(ref otif) = otif_score {
                    updates.push("otif = ?");
                    let value: Option<f64> = if otif.trim().is_empty() { 
                        None 
                    } else { 
                        otif.parse::<f64>().ok() 
                    };
                    params.push(Box::new(value));
                }
                
                if let Some(ref nil) = nil_score {
                    updates.push("nil = ?");
                    let value: Option<f64> = if nil.trim().is_empty() { 
                        None 
                    } else { 
                        nil.parse::<f64>().ok() 
                    };
                    params.push(Box::new(value));
                }
                
                if let Some(ref pickup) = pickup_score {
                    updates.push("quality_pickup = ?");
                    let value: Option<String> = if pickup.trim().is_empty() { 
                        None 
                    } else { 
                        Some(pickup.clone()) 
                    };
                    params.push(Box::new(value));
                }
                
                if let Some(ref package) = package_score {
                    updates.push("quality_package = ?");
                    let value: Option<String> = if package.trim().is_empty() { 
                        None 
                    } else { 
                        Some(package.clone()) 
                    };
                    params.push(Box::new(value));
                }
                
                if let Some(ref comment) = comments {
                    updates.push("comment = ?");
                    params.push(Box::new(comment.clone()));
                }
                
                // Sempre atualiza total_score, change_date e changed_by
                updates.push("total_score = ?");
                updates.push("change_date = ?");
                updates.push("changed_by = ?");
                params.push(Box::new(total_score_value.clone()));
                params.push(Box::new(now.clone()));
                params.push(Box::new(user_name.clone()));
                
                if updates.is_empty() {
                    println!("⚠️ Nenhum campo para atualizar");
                    return Ok("Nenhuma alteração para salvar".to_string());
                }
                
                let query = format!(
                    "UPDATE supplier_score_records_table SET {} WHERE id = ?",
                    updates.join(", ")
                );
                
                params.push(Box::new(id));
                
                // Converte Vec<Box<dyn ToSql>> para &[&dyn ToSql]
                let param_refs: Vec<&dyn rusqlite::ToSql> = params.iter().map(|p| p.as_ref()).collect();
                
                conn.execute(&query, param_refs.as_slice())
                    .map_err(|e| format!("Erro ao atualizar: {}", e))?;
                
                println!("✅ Score atualizado com sucesso!");
                Ok("Score atualizado com sucesso".to_string())
            }
            Err(_) => {
                // Insere novo registro
                println!("➕ Criando novo registro");
                
                // Registra log de criação
                let new_values = format!(
                    "OTIF: {}, NIL: {}, Pickup: {}, Package: {}",
                    otif_score.as_ref().unwrap_or(&"—".to_string()),
                    nil_score.as_ref().unwrap_or(&"—".to_string()),
                    pickup_score.as_ref().unwrap_or(&"—".to_string()),
                    package_score.as_ref().unwrap_or(&"—".to_string())
                );
                
                Self::insert_log(
                    conn,
                    &user_name,
                    "Create",
                    &user_wwid,
                    "All Scores",
                    Some(&supplier_info),
                    Some(&score_date_str),
                    None,
                    Some(&new_values)
                )?;
                
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
                        otif_score.as_ref().and_then(|s| if s.trim().is_empty() { None } else { s.parse::<f64>().ok() }),
                        nil_score.as_ref().and_then(|s| if s.trim().is_empty() { None } else { s.parse::<f64>().ok() }),
                        pickup_score.as_ref().and_then(|s| if s.trim().is_empty() { None } else { Some(s.clone()) }),
                        package_score.as_ref().and_then(|s| if s.trim().is_empty() { None } else { Some(s.clone()) }),
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
                 WHERE CAST(supplier_id AS TEXT) = ?1
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

        // Atualiza o nome do fornecedor em todos os registros de score relacionados
        let update_score_sql = "UPDATE supplier_score_records_table SET supplier_name = ?1 WHERE supplier_id = ?2";
        let score_rows_affected = conn
            .execute(update_score_sql, rusqlite::params![&supplier.supplier_name, &supplier.supplier_id])
            .map_err(|e| format!("Erro ao atualizar registros de score: {}", e))?;
        println!("✅ {} registros de score atualizados", score_rows_affected);

        println!("✅ {} registros de fornecedor atualizados", rows_affected);
        Ok(())
    }

    /// Exclui um fornecedor e seus registros de score
    pub fn delete_supplier(supplier_id: String) -> Result<(), String> {
        println!("\n🗑️ Excluindo fornecedor: {}", supplier_id);
        let mut conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_mut().unwrap();

        let tx = conn
            .transaction()
            .map_err(|e| format!("Erro ao iniciar transação: {}", e))?;

        tx.execute(
            "DELETE FROM supplier_score_records_table WHERE supplier_id = ?1",
            [&supplier_id],
        )
        .map_err(|e| format!("Erro ao excluir scores do fornecedor: {}", e))?;

        let has_legacy_table: bool = tx
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='supplier_score'",
                [],
                |row| row.get::<_, i32>(0),
            )
            .map_err(|e| format!("Erro ao verificar tabela legacy: {}", e))? > 0;

        if has_legacy_table {
            tx.execute(
                "DELETE FROM supplier_score WHERE supplier_id = ?1",
                [&supplier_id],
            )
            .map_err(|e| format!("Erro ao excluir scores legados do fornecedor: {}", e))?;
        }

        tx.execute(
            "DELETE FROM supplier_database_table WHERE COALESCE(CAST(supplier_id AS TEXT), '') = ?1",
            [&supplier_id],
        )
        .map_err(|e| format!("Erro ao excluir fornecedor: {}", e))?;

        tx.commit()
            .map_err(|e| format!("Erro ao finalizar transação: {}", e))?;

        println!("✅ Fornecedor excluído com sucesso!");
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
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Database connection not initialized".to_string())?;
        
        let online_value = if is_online { 1 } else { 0 };
        
        conn.execute(
            "UPDATE users_table SET is_online = ?1 WHERE user_id = ?2",
            rusqlite::params![online_value, user_id]
        )
        .map_err(|e| format!("Erro ao atualizar status online: {}", e))?;
        
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

        let can_edit_otif = permissions.0 == 1;
        let can_edit_nil = permissions.1 == 1;
        let can_edit_pickup = permissions.2 == 1;
        let can_edit_package = permissions.3 == 1;

        if !can_edit_otif && !can_edit_nil && !can_edit_pickup && !can_edit_package {
            return Ok(Vec::new());
        }

        // Busca registros com qualquer campo pendente (NULL ou vazio)
        // MAS que tenham pelo menos UM campo preenchido (não considera registros com TODAS as notas vazias)
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
                CASE WHEN r.quality_package IS NULL THEN NULL ELSE r.quality_package END AS package_value,
                o_otif.record_id AS otif_dismissed,
                o_nil.record_id AS nil_dismissed,
                o_pickup.record_id AS pickup_dismissed,
                o_package.record_id AS package_dismissed
            FROM supplier_score_records_table r
            LEFT JOIN supplier_database_table s ON s.supplier_id = r.supplier_id
            LEFT JOIN pending_scores_override o_otif ON o_otif.record_id = r.id AND o_otif.score_type = 'otif'
            LEFT JOIN pending_scores_override o_nil ON o_nil.record_id = r.id AND o_nil.score_type = 'nil'
            LEFT JOIN pending_scores_override o_pickup ON o_pickup.record_id = r.id AND o_pickup.score_type = 'pickup'
            LEFT JOIN pending_scores_override o_package ON o_package.record_id = r.id AND o_package.score_type = 'package'
            WHERE (
                r.otif IS NULL OR CAST(r.otif AS TEXT) = '' OR
                r.nil IS NULL OR CAST(r.nil AS TEXT) = '' OR
                r.quality_pickup IS NULL OR r.quality_pickup = '' OR
                r.quality_package IS NULL OR r.quality_package = ''
            )
            AND (
                (r.otif IS NOT NULL AND CAST(r.otif AS TEXT) != '') OR
                (r.nil IS NOT NULL AND CAST(r.nil AS TEXT) != '') OR
                (r.quality_pickup IS NOT NULL AND r.quality_pickup != '') OR
                (r.quality_package IS NOT NULL AND r.quality_package != '')
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

                let otif_dismissed: Option<i32> = row.get(9).ok();
                let nil_dismissed: Option<i32> = row.get(10).ok();
                let pickup_dismissed: Option<i32> = row.get(11).ok();
                let package_dismissed: Option<i32> = row.get(12).ok();

                let otif_empty = otif_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);
                let nil_empty = nil_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);
                let pickup_empty = pickup_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);
                let package_empty = package_value.as_ref().map(|v| v.trim().is_empty()).unwrap_or(true);

                let mut pending_for_user: Vec<&str> = Vec::new();
                if can_edit_otif && otif_empty && otif_dismissed.is_none() {
                    pending_for_user.push("OTIF");
                }
                if can_edit_nil && nil_empty && nil_dismissed.is_none() {
                    pending_for_user.push("NIL");
                }
                if can_edit_pickup && pickup_empty && pickup_dismissed.is_none() {
                    pending_for_user.push("Pickup");
                }
                if can_edit_package && package_empty && package_dismissed.is_none() {
                    pending_for_user.push("Package");
                }

                if pending_for_user.is_empty() {
                    return Ok(None);
                }

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

        let score_value_trimmed = score_value.trim();

        let rows_affected = if score_type == "otif" || score_type == "nil" {
            // OTIF e NIL são REAL (permite vazio -> NULL)
            let score_numeric: Option<f64> = if score_value_trimmed.is_empty() {
                None
            } else {
                Some(
                    score_value_trimmed
                        .parse::<f64>()
                        .map_err(|_| format!("Valor inválido para {}: {}", score_type, score_value))?
                )
            };
            
            conn.execute(
                &query,
                rusqlite::params![score_numeric, now, user_name, record_id],
            )
        } else {
            // Pickup e Package são TEXT (permite vazio -> NULL)
            let score_text: Option<String> = if score_value_trimmed.is_empty() {
                None
            } else {
                Some(score_value.clone())
            };

            conn.execute(
                &query,
                rusqlite::params![score_text, now, user_name, record_id],
            )
        }.map_err(|e| format!("Erro ao atualizar score: {}", e))?;

        // Controle de pendência: se salvou vazio, marca como avaliado; se salvou valor, remove override
        if score_value_trimmed.is_empty() {
            conn.execute(
                "INSERT OR REPLACE INTO pending_scores_override (record_id, score_type, dismissed)
                 VALUES (?1, ?2, 1)",
                rusqlite::params![record_id, score_type],
            ).map_err(|e| format!("Erro ao registrar override de pendência: {}", e))?;
        } else {
            conn.execute(
                "DELETE FROM pending_scores_override WHERE record_id = ?1 AND score_type = ?2",
                rusqlite::params![record_id, score_type],
            ).map_err(|e| format!("Erro ao remover override de pendência: {}", e))?;
        }

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
    pub country: Option<String>,
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
        // Um registro só conta se tiver pelo menos uma das 4 notas preenchidas
        let query = format!(
            "SELECT 
                CAST(sup.supplier_id AS TEXT) AS supplier_id,
                sup.ssid,
                sup.vendor_name,
                sup.bu,
                sup.country,
                CAST(sup.supplier_po AS TEXT) AS supplier_po,
                AVG(CASE WHEN score.month IN ('1','2','3') AND (score.otif IS NOT NULL OR score.nil IS NOT NULL OR score.quality_pickup IS NOT NULL OR score.quality_package IS NOT NULL) THEN CAST(score.total_score AS REAL) END) as q1,
                AVG(CASE WHEN score.month IN ('4','5','6') AND (score.otif IS NOT NULL OR score.nil IS NOT NULL OR score.quality_pickup IS NOT NULL OR score.quality_package IS NOT NULL) THEN CAST(score.total_score AS REAL) END) as q2,
                AVG(CASE WHEN score.month IN ('7','8','9') AND (score.otif IS NOT NULL OR score.nil IS NOT NULL OR score.quality_pickup IS NOT NULL OR score.quality_package IS NOT NULL) THEN CAST(score.total_score AS REAL) END) as q3,
                AVG(CASE WHEN score.month IN ('10','11','12') AND (score.otif IS NOT NULL OR score.nil IS NOT NULL OR score.quality_pickup IS NOT NULL OR score.quality_package IS NOT NULL) THEN CAST(score.total_score AS REAL) END) as q4,
                AVG(CASE WHEN (score.otif IS NOT NULL OR score.nil IS NOT NULL OR score.quality_pickup IS NOT NULL OR score.quality_package IS NOT NULL) THEN CAST(score.total_score AS REAL) END) as avg_score
            FROM supplier_database_table sup
            INNER JOIN supplier_score_records_table score 
                ON sup.supplier_id = score.supplier_id
            WHERE score.year = '{}' 
                AND (score.otif IS NOT NULL OR score.nil IS NOT NULL OR score.quality_pickup IS NOT NULL OR score.quality_package IS NOT NULL)
            GROUP BY sup.supplier_id, sup.ssid, sup.vendor_name, sup.bu, sup.country, sup.supplier_po
            HAVING avg_score < {} AND avg_score IS NOT NULL
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
            let country: Option<String> = row.get(4)?;
            let po: Option<String> = row.get(5)?;
            let q1: Option<f64> = row.get(6)?;
            let q2: Option<f64> = row.get(7)?;
            let q3: Option<f64> = row.get(8)?;
            let q4: Option<f64> = row.get(9)?;
            let avg_score: f64 = row.get(10)?;
            
            println!("  📊 {} - {} | Média: {:.2} | Q1: {:?} | Q2: {:?} | Q3: {:?} | Q4: {:?}", 
                     supplier_id, vendor_name, avg_score, q1, q2, q3, q4);
            
            Ok(RiskSupplier {
                supplier_id,
                ssid,
                vendor_name,
                bu,
                country,
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

    /// Registra log de geração em lote de notas cheias
    pub fn log_bulk_generation(
        user_name: String,
        user_wwid: String,
        month: i32,
        year: i32,
        count: i32,
    ) -> Result<(), String> {
        println!("\n📝 Registrando log de geração em lote...");
        
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;
        
        println!("🔍 WWID recebido: '{}'", user_wwid);
        
        let new_values = format!("{} suppliers - Month: {}/{}", count, month, year);
        let score_date_str = format!("{}/{}", month, year);
        
        Self::insert_log(
            conn,
            &user_name,
            "Create",
            &user_wwid,
            "All Scores",
            Some("ALL"),
            Some(&score_date_str),
            None,
            Some(&new_values)
        )?;
        
        println!("✅ Log de geração em lote registrado");
        Ok(())
    }

    /// Busca todos os logs do sistema
    pub fn get_all_logs() -> Result<Vec<LogEntry>, String> {
        println!("\n📋 Buscando todos os logs...");
        
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;

        let mut stmt = conn
            .prepare(
                "SELECT log_id, date, time, user, event, wwid, place, supplier, score_date, old_value, new_value
                 FROM log_table
                 ORDER BY date DESC, time DESC
                 LIMIT 1000"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let logs = stmt
            .query_map([], |row| {
                Ok(LogEntry {
                    log_id: row.get(0)?,
                    date: row.get(1)?,
                    time: row.get(2)?,
                    user: row.get(3)?,
                    event: row.get(4)?,
                    wwid: row.get(5)?,
                    place: row.get(6)?,
                    supplier: row.get(7)?,
                    score_date: row.get(8)?,
                    old_value: row.get(9)?,
                    new_value: row.get(10)?,
                })
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        println!("✅ {} logs encontrados", logs.len());
        Ok(logs)
    }

    /// Busca logs por usuário
    pub fn get_logs_by_user(user_name: String) -> Result<Vec<LogEntry>, String> {
        println!("\n📋 Buscando logs do usuário: {}", user_name);
        
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;

        let mut stmt = conn
            .prepare(
                "SELECT log_id, date, time, user, event, wwid, place, supplier, score_date, old_value, new_value
                 FROM log_table
                 WHERE user = ?1
                 ORDER BY date DESC, time DESC
                 LIMIT 500"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let logs = stmt
            .query_map([user_name], |row| {
                Ok(LogEntry {
                    log_id: row.get(0)?,
                    date: row.get(1)?,
                    time: row.get(2)?,
                    user: row.get(3)?,
                    event: row.get(4)?,
                    wwid: row.get(5)?,
                    place: row.get(6)?,
                    supplier: row.get(7)?,
                    score_date: row.get(8)?,
                    old_value: row.get(9)?,
                    new_value: row.get(10)?,
                })
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        println!("✅ {} logs encontrados", logs.len());
        Ok(logs)
    }

    /// Busca logs por período
    pub fn get_logs_by_date_range(start_date: String, end_date: String) -> Result<Vec<LogEntry>, String> {
        println!("\n📋 Buscando logs entre {} e {}", start_date, end_date);
        
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref()
            .ok_or_else(|| "Conexão não inicializada".to_string())?;

        let mut stmt = conn
            .prepare(
                "SELECT log_id, date, time, user, event, wwid, place, supplier, score_date, old_value, new_value
                 FROM log_table
                 WHERE date BETWEEN ?1 AND ?2
                 ORDER BY date DESC, time DESC
                 LIMIT 1000"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let logs = stmt
            .query_map([start_date, end_date], |row| {
                Ok(LogEntry {
                    log_id: row.get(0)?,
                    date: row.get(1)?,
                    time: row.get(2)?,
                    user: row.get(3)?,
                    event: row.get(4)?,
                    wwid: row.get(5)?,
                    place: row.get(6)?,
                    supplier: row.get(7)?,
                    score_date: row.get(8)?,
                    old_value: row.get(9)?,
                    new_value: row.get(10)?,
                })
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        println!("✅ {} logs encontrados", logs.len());
        Ok(logs)
    }

    /// Busca usuários com mais atividade (para Super Admin)
    pub fn get_most_active_users(limit: i32) -> Result<Vec<(String, String, i32)>, String> {
        println!("👥 Buscando usuários mais ativos (limit: {})...", limit);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        // Debug: Verificar logs na tabela
        let log_count: i32 = conn.query_row(
            "SELECT COUNT(*) FROM log_table WHERE wwid != 'Unknown' AND wwid != ''",
            [],
            |row| row.get(0)
        ).unwrap_or(0);
        println!("📊 Total de logs com WWID válido: {}", log_count);
        
        // Debug: Verificar usuários na tabela
        let user_count: i32 = conn.query_row(
            "SELECT COUNT(*) FROM users_table",
            [],
            |row| row.get(0)
        ).unwrap_or(0);
        println!("👤 Total de usuários: {}", user_count);
        
        let mut stmt = conn
            .prepare(
                "SELECT u.user_wwid, 
                        u.user_name, 
                        COUNT(l.wwid) as activity_count
                 FROM users_table u
                 LEFT JOIN log_table l ON u.user_wwid = l.wwid
                 WHERE l.wwid IS NOT NULL AND l.wwid != 'Unknown' AND l.wwid != ''
                 GROUP BY u.user_wwid, u.user_name
                 ORDER BY activity_count DESC
                 LIMIT ?1"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let users = stmt
            .query_map([limit], |row| {
                let wwid: String = row.get(0)?;
                let name: String = row.get(1)?;
                let count: i32 = row.get(2)?;
                println!("  📌 WWID: {}, Nome: {}, Atividades: {}", wwid, name, count);
                Ok((wwid, name, count))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        println!("✅ {} usuários mais ativos encontrados", users.len());
        Ok(users)
    }

    /// Busca contribuições dos usuários com data do último input
    pub fn get_user_contributions() -> Result<Vec<(String, String, i32, String)>, String> {
        println!("📊 Buscando contribuições dos usuários...");
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        let mut stmt = conn
            .prepare(
                "SELECT u.user_wwid, 
                        u.user_name, 
                        COUNT(l.wwid) as contribution_count,
                        MAX(l.date || ' ' || l.time) as last_input_date
                 FROM users_table u
                 LEFT JOIN log_table l ON u.user_wwid = l.wwid
                 WHERE l.wwid IS NOT NULL AND l.wwid != 'Unknown' AND l.wwid != ''
                 GROUP BY u.user_wwid, u.user_name
                 ORDER BY contribution_count DESC"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let contributors = stmt
            .query_map([], |row| {
                let wwid: String = row.get(0)?;
                let name: String = row.get(1)?;
                let count: i32 = row.get(2)?;
                let last_date: String = row.get(3).unwrap_or_else(|_| "".to_string());
                Ok((wwid, name, count, last_date))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        println!("✅ {} contribuidores encontrados", contributors.len());
        Ok(contributors)
    }

    /// Busca contribuições dos usuários por mês/ano específico
    pub fn get_user_contributions_by_month(month: i32, year: i32) -> Result<Vec<(String, String, i32, String)>, String> {
        println!("📊 Buscando contribuições dos usuários para {}/{}", month, year);
        
        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();
        
        // Construir padrões de data para o mês/ano especificado
        let date_patterns = vec![
            format!("{:04}-{:02}-%", year, month),  // YYYY-MM-DD
            format!("{:02}/{:02}/{:04}%", month, month, year),  // MM/DD/YYYY or DD/MM/YYYY
        ];
        
        let mut stmt = conn
            .prepare(
                "SELECT u.user_wwid, 
                        u.user_name, 
                        COUNT(l.wwid) as contribution_count,
                        MAX(l.date || ' ' || l.time) as last_input_date
                 FROM users_table u
                 LEFT JOIN log_table l ON u.user_wwid = l.wwid
                                 WHERE l.wwid IS NOT NULL
                                     AND l.wwid != 'Unknown'
                                     AND l.wwid != ''
                                        AND (
                                            u.user_privilege IS NULL
                                            OR replace(replace(replace(lower(trim(u.user_privilege)), ' ', ''), '-', ''), '_', '') != 'superadmin'
                                        )
                                     AND (l.date LIKE ?1 OR l.date LIKE ?2)
                 GROUP BY u.user_wwid, u.user_name
                 HAVING contribution_count > 0
                 ORDER BY contribution_count DESC"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let contributors = stmt
            .query_map([&date_patterns[0], &date_patterns[1]], |row| {
                let wwid: String = row.get(0)?;
                let name: String = row.get(1)?;
                let count: i32 = row.get(2)?;
                let last_date: String = row.get(3).unwrap_or_else(|_| "".to_string());
                Ok((wwid, name, count, last_date))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        println!("✅ {} contribuidores encontrados para {}/{}", contributors.len(), month, year);
        Ok(contributors)
    }

    /// Busca contribuições diárias por usuário (estilo calendário) para um ano
    pub fn get_user_contribution_calendar(year: i32) -> Result<Vec<(String, String, String, i32)>, String> {
        println!("📊 Buscando contribuições diárias dos usuários para {}", year);

        let conn_guard = Self::get_connection()?;

        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        let date_patterns = vec![
            format!("{:04}-%", year),
            format!("%/{}", year),
        ];

        let mut stmt = conn
            .prepare(
                "SELECT u.user_wwid,
                        u.user_name,
                        l.date,
                        COUNT(l.wwid) as contribution_count
                 FROM users_table u
                 LEFT JOIN log_table l ON u.user_wwid = l.wwid
                 WHERE l.wwid IS NOT NULL
                   AND l.wwid != 'Unknown'
                   AND l.wwid != ''
                   AND (l.date LIKE ?1 OR l.date LIKE ?2)
                 GROUP BY u.user_wwid, u.user_name, l.date
                 ORDER BY u.user_name, l.date"
            )
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let rows = stmt
            .query_map([&date_patterns[0], &date_patterns[1]], |row| {
                let wwid: String = row.get(0)?;
                let name: String = row.get(1)?;
                let date: String = row.get(2).unwrap_or_else(|_| "".to_string());
                let count: i32 = row.get(3)?;
                Ok((wwid, name, date, count))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Erro ao coletar resultados: {}", e))?;

        println!("✅ {} registros de contribuição diários encontrados", rows.len());
        Ok(rows)
    }

    /// Exporta formulário de avaliação para Excel
    /// criteria: "otif", "nil", "pickup", "package"
    /// include_score: se true, preenche com notas existentes
    /// month: mês da nota (1-12)
    /// year: ano da nota
    pub fn export_evaluation_form(
        criteria: String,
        include_score: bool,
        month: Option<i32>,
        year: Option<i32>,
    ) -> Result<Vec<u8>, String> {
        println!("\n📤 ========================================");
        println!("📤 EXPORT_EVALUATION_FORM CHAMADO!");
        println!("📤 Critério recebido: {}", criteria);
        println!("📤 Incluir Score: {}", include_score);
        println!("📤 Mês: {:?}, Ano: {:?}", month, year);
        println!("📤 ========================================\n");

        let trimmed_criteria = criteria.trim().to_string();
        let criteria_key = trimmed_criteria.to_lowercase();
        let criteria_label = criteria_key.to_uppercase();
        println!("📤 Critério normalizado: {}", criteria_key);

        // Validação: se include_score é true, mês e ano são obrigatórios
        if include_score {
            if month.is_none() || year.is_none() {
                return Err("Mês e ano são obrigatórios quando incluir notas existentes".to_string());
            }

            // Verifica se existe pelo menos um registro para o período
            let conn_guard = Self::get_connection()?;
            if conn_guard.is_none() {
                return Err("Conexão não inicializada".to_string());
            }
            let conn = conn_guard.as_ref().unwrap();

            let check_query = "SELECT COUNT(*) FROM supplier_score_records_table WHERE month = ?1 AND year = ?2";
            let count: i32 = conn
                .query_row(check_query, [&month.unwrap(), &year.unwrap()], |row| row.get(0))
                .map_err(|e| format!("Erro ao verificar período: {}", e))?;

            if count == 0 {
                return Err(format!(
                    "Não existem registros de notas para o período {}/{}",
                    month.unwrap(),
                    year.unwrap()
                ));
            }
        }

        let conn_guard = Self::get_connection()?;
        
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }

        let conn = conn_guard.as_ref().unwrap();

        // Mapeia o nome do critério para o nome da coluna no banco
        let score_column = match criteria_key.as_str() {
            "otif" => "otif",
            "nil" => "nil",
            "pickup" => "quality_pickup",
            "package" => "quality_package",
            _ => return Err(format!("Critério inválido: {}", trimmed_criteria)),
        };

        println!("📊 Coluna de score selecionada: {}", score_column);

        // Busca todos os fornecedores
        let suppliers_query = String::from(
            "SELECT DISTINCT 
                COALESCE(CAST(supplier_id AS TEXT), '') as supplier_id,
                COALESCE(vendor_name, '') as vendor_name,
                CASE 
                    WHEN bu = 'N/A' THEN ''
                    ELSE COALESCE(bu, '')
                END as bu,
                COALESCE(CAST(supplier_po AS TEXT), '') as supplier_po
             FROM supplier_database_table
             ORDER BY vendor_name"
        );

        let mut stmt = conn
            .prepare(&suppliers_query)
            .map_err(|e| format!("Erro ao preparar query de fornecedores: {}", e))?;

        #[derive(Debug)]
        struct ExportRow {
            record_id: Option<i32>,
            supplier_id: String,
            vendor_name: String,
            bu: String,
            supplier_po: String,
            score: Option<f64>,
            comment: Option<String>,
        }

        let mut export_data: Vec<ExportRow> = Vec::new();

        let suppliers = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                ))
            })
            .map_err(|e| format!("Erro ao executar query: {}", e))?;

        for supplier_result in suppliers {
            let (supplier_id, vendor_name, bu, supplier_po) = supplier_result
                .map_err(|e| format!("Erro ao processar fornecedor: {}", e))?;

            let mut score: Option<f64> = None;
            let mut record_id: Option<i32> = None;
            let mut comment: Option<String> = None;

            // Se deve incluir scores, busca da tabela de scores
            if include_score && month.is_some() && year.is_some() {
                let score_query = format!(
                    "SELECT id, {}, comment FROM supplier_score_records_table 
                     WHERE lower(trim(supplier_id)) = lower(trim(?1)) 
                     AND month = ?2 
                     AND year = ?3",
                    score_column
                );

                println!("🔍 Query de busca: {}", score_query);
                println!("🔍 Parâmetros: supplier_id='{}', month={}, year={}", 
                         supplier_id, month.unwrap(), year.unwrap());

                if let Ok(mut score_stmt) = conn.prepare(&score_query) {
                    match score_stmt.query_row(
                        [&supplier_id, &month.unwrap().to_string(), &year.unwrap().to_string()],
                        |row| {
                            let id = row.get::<_, i32>(0)?;
                            
                            // quality_pickup e quality_package são TEXT, outros são REAL
                            let score_val = if score_column == "quality_pickup" || score_column == "quality_package" {
                                row.get::<_, Option<String>>(1)?
                                    .and_then(|s| s.parse::<f64>().ok())
                            } else {
                                row.get::<_, Option<f64>>(1)?
                            };
                            
                            let comment_val = row.get::<_, Option<String>>(2)?;
                            
                            println!("   ✅ Encontrado: id={}, score={:?}, comment={:?}", id, score_val, comment_val);
                            Ok((Some(id), score_val, comment_val))
                        }
                    ) {
                        Ok(result) => {
                            record_id = result.0;
                            score = result.1;
                            comment = result.2;
                        }
                        Err(e) => {
                            println!("   ⚠️ Nenhum registro encontrado: {}", e);
                        }
                    }
                }
            }

            export_data.push(ExportRow {
                record_id,
                supplier_id,
                vendor_name,
                bu,
                supplier_po,
                score,
                comment,
            });
        }

        println!("✅ {} fornecedores preparados para exportação", export_data.len());

        // Cria o arquivo Excel usando rust_xlsxwriter
        use rust_xlsxwriter::{Workbook, Format, Color, FormatAlign, DataValidation, DataValidationRule};

        let mut workbook = Workbook::new();
        let worksheet = workbook.add_worksheet();
        
        // Formatos
        let header_format = Format::new()
            .set_bold()
            .set_font_size(12)
            .set_background_color(Color::RGB(0x4472C4))
            .set_font_color(Color::White)
            .set_align(FormatAlign::Center)
            .set_locked(); // Cabeçalho bloqueado

        // Formato para colunas bloqueadas (A e B - Record ID e Supplier ID)
        let locked_format = Format::new()
            .set_align(FormatAlign::Left)
            .set_background_color(Color::RGB(0xF2F2F2))
            .set_locked(); // Explicitamente bloqueado

        // Formato para colunas desbloqueadas (C e D - Vendor Name e Supplier PO)
        let unlocked_format = Format::new()
            .set_align(FormatAlign::Left)
            .set_unlocked(); // Explicitamente desbloqueado

        // Formato para coluna de score (E) - desbloqueada e com formato numérico
        let score_format = Format::new()
            .set_align(FormatAlign::Center)
            .set_num_format("0.0")
            .set_unlocked(); // Permite edição

        // Formato para coluna de comentário - desbloqueada
        let comment_format = Format::new()
            .set_align(FormatAlign::Left)
            .set_unlocked(); // Permite edição

        // Define largura das colunas
        if include_score {
            worksheet.set_column_width(0, 12).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(1, 15).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(2, 40).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(3, 18).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(4, 15).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(5, 12).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(6, 50).map_err(|e| format!("Erro ao definir largura: {}", e))?;
        } else {
            worksheet.set_column_width(0, 15).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(1, 40).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(2, 18).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(3, 15).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(4, 12).map_err(|e| format!("Erro ao definir largura: {}", e))?;
            worksheet.set_column_width(5, 50).map_err(|e| format!("Erro ao definir largura: {}", e))?;
        }

        // Cabeçalhos
        if include_score {
            worksheet.write_with_format(0, 0, "Record ID", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 1, "Supplier ID", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 2, "Vendor Name", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 3, "BU", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 4, "Supplier PO", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 5, criteria_label.as_str(), &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 6, "Comment", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
        } else {
            worksheet.write_with_format(0, 0, "Supplier ID", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 1, "Vendor Name", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 2, "BU", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 3, "Supplier PO", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 4, criteria_label.as_str(), &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
            worksheet.write_with_format(0, 5, "Comment", &header_format)
                .map_err(|e| format!("Erro ao escrever cabeçalho: {}", e))?;
        }

        // Dados
        for (idx, row) in export_data.iter().enumerate() {
            let row_num = (idx + 1) as u32;
            
            if include_score {
                // Coluna A: Record ID (bloqueada)
                if let Some(rid) = row.record_id {
                    worksheet.write_with_format(row_num, 0, rid, &locked_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                } else {
                    worksheet.write_with_format(row_num, 0, "", &locked_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                }

                // Coluna B: Supplier ID (bloqueada)
                worksheet.write_with_format(row_num, 1, &row.supplier_id, &locked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                
                // Coluna C: Vendor Name (desbloqueada)
                worksheet.write_with_format(row_num, 2, &row.vendor_name, &unlocked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                
                // Coluna D: BU (desbloqueada)
                worksheet.write_with_format(row_num, 3, &row.bu, &unlocked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                
                // Coluna E: Supplier PO (desbloqueada)
                worksheet.write_with_format(row_num, 4, &row.supplier_po, &unlocked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;

                // Coluna F: Score (desbloqueada com validação)
                if let Some(score_val) = row.score {
                    worksheet.write_with_format(row_num, 5, score_val, &score_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                } else {
                    worksheet.write_with_format(row_num, 5, "", &score_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                }

                // Coluna G: Comment (desbloqueada)
                if let Some(ref comment_val) = row.comment {
                    worksheet.write_with_format(row_num, 6, comment_val, &comment_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                } else {
                    worksheet.write_with_format(row_num, 6, "", &comment_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                }
            } else {
                // Modo sem score (não usado mais, mas mantido por compatibilidade)
                worksheet.write_with_format(row_num, 0, &row.supplier_id, &locked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                worksheet.write_with_format(row_num, 1, &row.vendor_name, &unlocked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                worksheet.write_with_format(row_num, 2, &row.bu, &unlocked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                worksheet.write_with_format(row_num, 3, &row.supplier_po, &unlocked_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                worksheet.write_with_format(row_num, 4, "", &score_format)
                    .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                // Coluna F: Comment (desbloqueada) - modo sem score
                if let Some(ref comment_val) = row.comment {
                    worksheet.write_with_format(row_num, 5, comment_val, &comment_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                } else {
                    worksheet.write_with_format(row_num, 5, "", &comment_format)
                        .map_err(|e| format!("Erro ao escrever dados: {}", e))?;
                }
            }
        }

        // Busca lista de BUs disponíveis no banco (da tabela business_unit_table)
        let bu_query = "SELECT DISTINCT bu FROM business_unit_table WHERE bu IS NOT NULL AND bu != '' ORDER BY bu";
        let mut bu_stmt = conn.prepare(bu_query)
            .map_err(|e| format!("Erro ao preparar query de BUs: {}", e))?;
        
        let bu_list: Vec<String> = bu_stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao buscar BUs: {}", e))?
            .filter_map(|r| r.ok())
            .collect();
        
        println!("📋 BUs disponíveis: {:?}", bu_list);

        // Fixa o header (congela primeira linha)
        worksheet.set_freeze_panes(1, 0)
            .map_err(|e| format!("Erro ao fixar header: {}", e))?;
        
        println!("📌 Header fixado (primeira linha congelada)");

        // Aplica validação de dados na coluna de score (coluna F com score ou coluna E sem score)
        let last_row = export_data.len() as u32;
        let score_col = if include_score { 5 } else { 4 };
        
        let validation = DataValidation::new()
            .allow_decimal_number(DataValidationRule::Between(0.0, 10.0))
            .set_error_title("Valor inválido")
            .map_err(|e| format!("Erro ao definir título de erro: {}", e))?
            .set_error_message("O valor deve ser um número entre 0.0 e 10.0 com uma casa decimal.")
            .map_err(|e| format!("Erro ao definir mensagem de erro: {}", e))?
            .set_input_title("Nota do Fornecedor")
            .map_err(|e| format!("Erro ao definir título de entrada: {}", e))?
            .set_input_message("Digite uma nota de 0.0 a 10.0")
            .map_err(|e| format!("Erro ao definir mensagem de entrada: {}", e))?;

        worksheet.add_data_validation(1, score_col as u16, last_row, score_col as u16, &validation)
            .map_err(|e| format!("Erro ao adicionar validação: {}", e))?;

        // Aplica validação de lista na coluna BU (coluna D com score ou coluna C sem score)
        if !bu_list.is_empty() {
            let bu_col = if include_score { 3 } else { 2 };
            let bu_validation = DataValidation::new()
                .allow_list_strings(&bu_list)
                .map_err(|e| format!("Erro ao criar validação de BU: {}", e))?
                .set_error_title("BU inválida")
                .map_err(|e| format!("Erro ao definir título de erro BU: {}", e))?
                .set_error_message("Selecione uma BU da lista disponível.")
                .map_err(|e| format!("Erro ao definir mensagem de erro BU: {}", e))?
                .set_input_title("Selecione a BU")
                .map_err(|e| format!("Erro ao definir título de entrada BU: {}", e))?
                .set_input_message("Escolha uma BU da lista")
                .map_err(|e| format!("Erro ao definir mensagem de entrada BU: {}", e))?;

            worksheet.add_data_validation(1, bu_col as u16, last_row, bu_col as u16, &bu_validation)
                .map_err(|e| format!("Erro ao adicionar validação de BU: {}", e))?;
            
            println!("✅ Validação de lista aplicada na coluna BU");
        }

        // Protege a planilha com senha
        worksheet.protect_with_password("30625629");

        println!("🔒 Planilha protegida com senha: 30625629");
        println!("🔒 Colunas A e B bloqueadas para edição");
        println!("✅ Validação aplicada na coluna de score (0.0 a 10.0)");

        // Cria aba oculta com dados de controle para validação na importação
        let control_sheet = workbook.add_worksheet();
        control_sheet.set_name("_control_")
            .map_err(|e| format!("Erro ao definir nome da aba: {}", e))?;
        control_sheet.set_hidden(true);

        // Formato para a aba de controle
        let control_header_format = Format::new()
            .set_bold()
            .set_background_color(Color::RGB(0x808080))
            .set_font_color(Color::White);

        let control_data_format = Format::new()
            .set_align(FormatAlign::Left);

        // Cabeçalhos da aba de controle
        control_sheet.write_with_format(0, 0, "Export Info", &control_header_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;
        control_sheet.write_with_format(0, 1, "Value", &control_header_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;

        // Dados de controle
        control_sheet.write_with_format(1, 0, "Criteria", &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;
        control_sheet.write_with_format(1, 1, criteria_key.as_str(), &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;

        control_sheet.write_with_format(2, 0, "Month", &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;
        control_sheet.write_with_format(2, 1, month.unwrap_or(0), &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;

        control_sheet.write_with_format(3, 0, "Year", &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;
        control_sheet.write_with_format(3, 1, year.unwrap_or(0), &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;

        control_sheet.write_with_format(4, 0, "Total Records", &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;
        control_sheet.write_with_format(4, 1, export_data.len() as i32, &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;

        // Adiciona timestamp da exportação
        use chrono::Local;
        let now = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
        control_sheet.write_with_format(5, 0, "Export Date", &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;
        control_sheet.write_with_format(5, 1, now.as_str(), &control_data_format)
            .map_err(|e| format!("Erro ao escrever controle: {}", e))?;

        println!("📋 Aba de controle '_control_' criada e ocultada");

        // Salva em buffer
        let buffer = workbook
            .save_to_buffer()
            .map_err(|e| format!("Erro ao salvar workbook: {}", e))?;

        println!("✅ Arquivo Excel gerado com sucesso ({} bytes)", buffer.len());
        Ok(buffer)
    }

    /// Valida arquivo de importação verificando a aba de controle
    pub fn validate_import_file(
        file_path: String,
        expected_criteria: String,
    ) -> Result<serde_json::Value, String> {
        println!("\n🔍 ========================================");
        println!("🔍 VALIDATE_IMPORT_FILE");
        println!("🔍 Arquivo: {}", file_path);
        println!("🔍 Critério esperado: {}", expected_criteria);
        println!("🔍 ========================================\n");

        use calamine::{Reader, open_workbook, Xlsx};

        // Abre o arquivo Excel
        let mut workbook: Xlsx<_> = open_workbook(&file_path)
            .map_err(|e| format!("Erro ao abrir arquivo: {}", e))?;

        // Busca a aba _control_
        let range = workbook.worksheet_range("_control_")
            .map_err(|e| format!("Erro ao ler aba '_control_': {}", e))?;

        println!("✅ Aba '_control_' encontrada");

            // Lê os dados de controle
            let mut criteria = String::new();
            let mut month: i32 = 0;
            let mut year: i32 = 0;
            let mut total_records: i32 = 0;
            let mut export_date = String::new();

            // Lê cada linha
            for row in range.rows() {
                if row.len() >= 2 {
                    let key = row[0].to_string();
                    let value = row[1].to_string();

                    match key.as_str() {
                        "Criteria" => criteria = value,
                        "Month" => month = value.parse().unwrap_or(0),
                        "Year" => year = value.parse().unwrap_or(0),
                        "Total Records" => total_records = value.parse().unwrap_or(0),
                        "Export Date" => export_date = value,
                        _ => {}
                    }
                }
            }

            println!("📋 Dados lidos:");
            println!("   Critério: {}", criteria);
            println!("   Mês: {}", month);
            println!("   Ano: {}", year);
            println!("   Total Registros: {}", total_records);
            println!("   Data Export: {}", export_date);

            // Valida o critério
            if criteria.to_lowercase() != expected_criteria.to_lowercase() {
                return Err(format!(
                    "Critério inválido. Esperado: {}, Encontrado: {}",
                    expected_criteria, criteria
                ));
            }

        println!("✅ Validação concluída com sucesso!");

        // Retorna resultado da validação
        Ok(serde_json::json!({
            "valid": true,
            "criteria": criteria,
            "month": month,
            "year": year,
            "total_records": total_records,
            "export_date": export_date,
        }))
    }

    /// Importa notas do arquivo Excel
    pub fn import_scores_from_file(
        file_path: String,
        criteria: String,
    ) -> Result<String, String> {
        println!("\n📥 ========================================");
        println!("📥 IMPORT_SCORES_FROM_FILE");
        println!("📥 Arquivo: {}", file_path);
        println!("📥 Critério: {}", criteria);
        println!("📥 ========================================\n");

        use calamine::{Reader, open_workbook, Xlsx};
        use rusqlite::params;

        // Abre o arquivo Excel
        let mut workbook: Xlsx<_> = open_workbook(&file_path)
            .map_err(|e| format!("Erro ao abrir arquivo: {}", e))?;

        // Busca a primeira aba (Sheet1)
        let sheet_names = workbook.sheet_names().to_owned();
        if sheet_names.is_empty() {
            return Err("Nenhuma aba encontrada no arquivo".to_string());
        }

        let sheet_name = &sheet_names[0];
        println!("📄 Lendo aba: {}", sheet_name);

        let range = workbook
            .worksheet_range(sheet_name)
            .map_err(|e| format!("Erro ao processar aba: {}", e))?;

        let mut updated_count = 0;
        let mut error_count = 0;
        let conn_guard = Self::get_connection()?;
        let conn = conn_guard.as_ref().ok_or_else(|| "Conexão não inicializada".to_string())?;

        // Define qual coluna atualizar baseado no critério
        let score_column = match criteria.to_lowercase().as_str() {
            "otif" => "otif",
            "nil" => "nil",
            "pickup" => "quality_pickup",
            "package" => "quality_package",
            _ => return Err(format!("Critério inválido: {}", criteria)),
        };

        println!("📊 Atualizando coluna: {}", score_column);

        // Busca os pesos dos critérios para calcular total_score
        let criteria_weights = Self::get_criteria_weights(conn)?;
        println!("⚖️ Pesos dos critérios: OTIF={}, NIL={}, Pickup={}, Package={}", 
                 criteria_weights.0, criteria_weights.1, criteria_weights.2, criteria_weights.3);

        let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        fn cell_to_string<T: ToString>(cell: &T) -> String {
            cell.to_string().trim().to_string()
        }

        fn cell_to_i32<T: ToString>(cell: &T) -> Option<i32> {
            let value = cell.to_string();
            let trimmed = value.trim();
            if trimmed.is_empty() {
                return None;
            }

            let normalized = trimmed.replace(',', ".");
            normalized
                .parse::<f64>()
                .ok()
                .map(|v| v.round() as i32)
        }

        fn cell_to_f64<T: ToString>(cell: &T) -> Option<f64> {
            let value = cell.to_string();
            let trimmed = value.trim();
            if trimmed.is_empty() {
                return None;
            }

            let normalized = trimmed.replace(',', ".");
            normalized.parse::<f64>().ok()
        }

        // Itera sobre as linhas (pulando o cabeçalho na linha 0)
        for (row_idx, row) in range.rows().enumerate() {
            if row_idx == 0 {
                println!("📋 Cabeçalho:");
                for (col_idx, cell) in row.iter().enumerate() {
                    println!("   Coluna {}: {}", col_idx, cell);
                }
                continue; // Pula cabeçalho
            }

            println!("\n📝 Linha {} - Total de colunas: {}", row_idx + 1, row.len());

            if row.len() < 5 {
                println!("⚠️ Linha {} ignorada: estrutura incompleta ({} colunas)", row_idx + 1, row.len());
            }

            // Lê os dados da linha usando índices atualizados
            let record_id_opt = row.get(0).and_then(|cell| cell_to_i32(cell));
            let supplier_id_str = row.get(1).map(|cell| cell_to_string(cell)).unwrap_or_default();
            let vendor_name_str = row.get(2).map(|cell| cell_to_string(cell)).unwrap_or_default();
            let _bu_str = row.get(3).map(|cell| cell_to_string(cell)).unwrap_or_default();
            let supplier_po_str = row.get(4).map(|cell| cell_to_string(cell)).unwrap_or_default();
            let score_opt = row.get(5).and_then(|cell| cell_to_f64(cell));
            let comment_str = row.get(6).map(|cell| cell_to_string(cell)).unwrap_or_default();

            println!("   [0] record_id: {:?}", record_id_opt);
            println!("   [1] supplier_id: '{}'", supplier_id_str);
            println!("   [2] vendor_name: '{}'", vendor_name_str);
            println!("   [3] bu: '{}'", _bu_str);
            println!("   [4] supplier_po: '{}'", supplier_po_str);
            println!("   [5] score: {:?}", score_opt);
            println!("   [6] comment: '{}'", comment_str);

            // Valida record_id
            let record_id = match record_id_opt {
                Some(id) if id > 0 => id,
                _ => {
                    println!("⚠️ record_id inválido na linha {}", row_idx + 1);
                    error_count += 1;
                    continue;
                }
            };

            // Valida nota
            let score = match score_opt {
                Some(value) => value,
                None => {
                    println!("⚠️ Score inválido/vazio na linha {}, pulando", row_idx + 1);
                    error_count += 1;
                    continue;
                }
            };

            // Valida range (0.0 a 10.0)
            if score < 0.0 || score > 10.0 {
                println!("⚠️ Score fora do range (0-10) na linha {}: {}", row_idx + 1, score);
                error_count += 1;
                continue;
            }

            // Busca o registro atual para pegar todos os scores existentes
            let current_record = conn.query_row(
                "SELECT otif, nil, quality_pickup, quality_package FROM supplier_score_records_table WHERE id = ?",
                params![record_id],
                |row| {
                    Ok((
                        row.get::<_, Option<f64>>(0)?,
                        row.get::<_, Option<f64>>(1)?,
                        row.get::<_, Option<String>>(2)?,
                        row.get::<_, Option<String>>(3)?,
                    ))
                }
            );

            let (mut otif, mut nil, mut pickup, mut package) = match current_record {
                Ok(data) => {
                    println!("📊 Scores atuais do record {}: OTIF={:?}, NIL={:?}, Pickup={:?}, Package={:?}", 
                             record_id, data.0, data.1, data.2, data.3);
                    data
                },
                Err(e) => {
                    println!("⚠️ Record {} não encontrado no banco: {}", record_id, e);
                    error_count += 1;
                    continue;
                }
            };

            // Atualiza APENAS o score do critério específico que está sendo importado
            match criteria.to_lowercase().as_str() {
                "otif" => {
                    println!("🔄 Atualizando OTIF: {} → {}", otif.unwrap_or(0.0), score);
                    otif = Some(score);
                },
                "nil" => {
                    println!("🔄 Atualizando NIL: {} → {}", nil.unwrap_or(0.0), score);
                    nil = Some(score);
                },
                "pickup" => {
                    println!("🔄 Atualizando Pickup: {:?} → {}", pickup, score);
                    pickup = Some(score.to_string());
                },
                "package" => {
                    println!("🔄 Atualizando Package: {:?} → {}", package, score);
                    package = Some(score.to_string());
                },
                _ => {}
            }

            // Recalcula o total_score usando TODAS as 4 notas (a nova + as antigas)
            let otif_val = otif.unwrap_or(0.0);
            let nil_val = nil.unwrap_or(0.0);
            let pickup_val = pickup.as_ref().and_then(|s| s.parse::<f64>().ok()).unwrap_or(0.0);
            let package_val = package.as_ref().and_then(|s| s.parse::<f64>().ok()).unwrap_or(0.0);

            println!("📐 Calculando total_score:");
            println!("   OTIF: {} × {} = {}", otif_val, criteria_weights.0, otif_val * criteria_weights.0);
            println!("   NIL: {} × {} = {}", nil_val, criteria_weights.1, nil_val * criteria_weights.1);
            println!("   Pickup: {} × {} = {}", pickup_val, criteria_weights.2, pickup_val * criteria_weights.2);
            println!("   Package: {} × {} = {}", package_val, criteria_weights.3, package_val * criteria_weights.3);

            let total_score = 
                (otif_val * criteria_weights.0) +
                (nil_val * criteria_weights.1) +
                (pickup_val * criteria_weights.2) +
                (package_val * criteria_weights.3);

            let total_score_str = format!("{:.2}", total_score);
            println!("   Total Score: {}", total_score_str);

            // Atualiza o registro no banco (inclui comment se não estiver vazio)
            let update_query = if !comment_str.is_empty() {
                format!(
                    "UPDATE supplier_score_records_table 
                     SET {} = ?, total_score = ?, comment = ?, change_date = ?, changed_by = ? 
                     WHERE id = ?",
                    score_column
                )
            } else {
                format!(
                    "UPDATE supplier_score_records_table 
                     SET {} = ?, total_score = ?, change_date = ?, changed_by = ? 
                     WHERE id = ?",
                    score_column
                )
            };

            println!("🔧 Query SQL: {}", update_query);
            println!("🔧 Parâmetros:");
            println!("   {} = {}", score_column, score);
            println!("   total_score = {}", total_score_str);
            if !comment_str.is_empty() {
                println!("   comment = {}", comment_str);
            }
            println!("   change_date = {}", now);
            println!("   changed_by = Import System");
            println!("   id = {}", record_id);

            let exec_result = if !comment_str.is_empty() {
                if score_column == "quality_pickup" || score_column == "quality_package" {
                    conn.execute(
                        &update_query,
                        params![score.to_string(), total_score_str.clone(), comment_str.clone(), now.clone(), "Import System", record_id]
                    )
                } else {
                    conn.execute(
                        &update_query,
                        params![score, total_score_str.clone(), comment_str.clone(), now.clone(), "Import System", record_id]
                    )
                }
            } else {
                if score_column == "quality_pickup" || score_column == "quality_package" {
                    conn.execute(
                        &update_query,
                        params![score.to_string(), total_score_str.clone(), now.clone(), "Import System", record_id]
                    )
                } else {
                    conn.execute(
                        &update_query,
                        params![score, total_score_str.clone(), now.clone(), "Import System", record_id]
                    )
                }
            };

            match exec_result {
                Ok(rows_affected) => {
                    println!("🔍 Linhas afetadas: {}", rows_affected);
                    if rows_affected > 0 {
                        println!("✅ Record {} atualizado: {} = {}, total_score = {}{}", 
                                 record_id, score_column, score, total_score_str,
                                 if !comment_str.is_empty() { format!(", comment = {}", comment_str) } else { "".to_string() });
                        updated_count += 1;
                    } else {
                        println!("⚠️ Record {} não foi atualizado (0 linhas afetadas)", record_id);
                        println!("   Possível causa: ID {} não existe na tabela", record_id);
                        error_count += 1;
                    }
                }
                Err(e) => {
                    println!("❌ Erro ao atualizar record {}: {}", record_id, e);
                    error_count += 1;
                }
            }
        }

        println!("✅ Importação concluída:");
        println!("   {} registros atualizados", updated_count);
        println!("   {} erros encontrados", error_count);

        if error_count > 0 {
            Ok(format!(
                "Atualizados: {} registros\nErros: {} registros",
                updated_count, error_count
            ))
        } else {
            Ok(format!("✅ {} registros atualizados com sucesso!", updated_count))
        }
    }

    // Função auxiliar para buscar os pesos dos critérios
    fn get_criteria_weights(conn: &Connection) -> Result<(f64, f64, f64, f64), String> {
        let mut stmt = conn
            .prepare("SELECT criteria_id, criteria_category, value FROM criteria_table WHERE criteria_id <= 4 ORDER BY criteria_id")
            .map_err(|e| format!("Erro ao buscar pesos: {}", e))?;

        let mut weights = vec![0.0; 4];
        let rows = stmt
            .query_map([], |row| {
                Ok((
                    row.get::<_, i32>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                ))
            })
            .map_err(|e| format!("Erro ao processar pesos: {}", e))?;

        for row_result in rows {
            if let Ok((criteria_id, category, value_str)) = row_result {
                let value = value_str.parse::<f64>().unwrap_or(0.0);
                let idx = (criteria_id - 1) as usize;
                if idx < 4 {
                    weights[idx] = value;
                    println!("  ⚖️ Critério {} ({}): peso = {}", criteria_id, category, value);
                }
            }
        }

        Ok((weights[0], weights[1], weights[2], weights[3]))
    }

    /// Exporta todos os suppliers para Excel com validações
    pub fn export_suppliers() -> Result<Vec<u8>, String> {
        println!("\n📤 ========================================");
        println!("📤 EXPORT_SUPPLIERS CHAMADO!");
        println!("📤 ========================================\n");

        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();

        // Busca todos os suppliers
        let query = "SELECT 
            CAST(supplier_id AS TEXT) as supplier_id, 
            vendor_name, 
            CASE WHEN bu = 'N/A' THEN '' ELSE COALESCE(bu, '') END as bu,
            CAST(supplier_po AS TEXT) as supplier_po, 
            CASE WHEN country = 'N/A' THEN '' ELSE COALESCE(country, '') END as origem,
            COALESCE(supplier_status, '') as supplier_status 
            FROM supplier_database_table ORDER BY vendor_name";
        let mut stmt = conn.prepare(query)
            .map_err(|e| format!("Erro ao preparar query: {}", e))?;

        let suppliers = stmt.query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, Option<String>>(2)?,
                row.get::<_, Option<String>>(3)?,
                row.get::<_, Option<String>>(4)?,
                row.get::<_, Option<String>>(5)?,
            ))
        })
        .map_err(|e| format!("Erro ao buscar suppliers: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Erro ao processar suppliers: {}", e))?;

        println!("✅ {} suppliers encontrados", suppliers.len());

        // Busca lista de BUs
        let bu_query = "SELECT DISTINCT bu FROM business_unit_table WHERE bu IS NOT NULL AND bu != '' ORDER BY bu";
        let mut bu_stmt = conn.prepare(bu_query)
            .map_err(|e| format!("Erro ao buscar BUs: {}", e))?;
        let bu_list: Vec<String> = bu_stmt.query_map([], |row| row.get(0))
            .map_err(|e| format!("Erro ao processar BUs: {}", e))?
            .filter_map(|r| r.ok())
            .collect();

        use rust_xlsxwriter::{Workbook, Format, Color, FormatAlign, DataValidation};

        let mut workbook = Workbook::new();
        
        // Formatos
        let header_format = Format::new()
            .set_bold()
            .set_font_size(12)
            .set_background_color(Color::RGB(0x4472C4))
            .set_font_color(Color::White)
            .set_align(FormatAlign::Center);

        let locked_format = Format::new()
            .set_align(FormatAlign::Left)
            .set_background_color(Color::RGB(0xF2F2F2))
            .set_locked();

        let unlocked_format = Format::new()
            .set_align(FormatAlign::Left)
            .set_unlocked();

        // Cria planilha principal
        let worksheet = workbook.add_worksheet();

        // Define larguras e formatos das colunas inteiras
        worksheet.set_column_width(0, 15).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_width(1, 40).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_width(2, 15).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_width(3, 15).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_width(4, 20).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_width(5, 15).map_err(|e| format!("Erro: {}", e))?;

        // Desbloqueia as colunas B até F inteiras
        worksheet.set_column_format(1, &unlocked_format).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_format(2, &unlocked_format).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_format(3, &unlocked_format).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_format(4, &unlocked_format).map_err(|e| format!("Erro: {}", e))?;
        worksheet.set_column_format(5, &unlocked_format).map_err(|e| format!("Erro: {}", e))?;

        // Fixa header
        worksheet.set_freeze_panes(1, 0)
            .map_err(|e| format!("Erro ao fixar header: {}", e))?;

        // Cabeçalhos
        worksheet.write_with_format(0, 0, "Supplier ID", &header_format)
            .map_err(|e| format!("Erro: {}", e))?;
        worksheet.write_with_format(0, 1, "Vendor Name", &header_format)
            .map_err(|e| format!("Erro: {}", e))?;
        worksheet.write_with_format(0, 2, "BU", &header_format)
            .map_err(|e| format!("Erro: {}", e))?;
        worksheet.write_with_format(0, 3, "Supplier PO", &header_format)
            .map_err(|e| format!("Erro: {}", e))?;
        worksheet.write_with_format(0, 4, "Origem", &header_format)
            .map_err(|e| format!("Erro: {}", e))?;
        worksheet.write_with_format(0, 5, "Supplier Status", &header_format)
            .map_err(|e| format!("Erro: {}", e))?;

        // Dados
        for (idx, (supplier_id, vendor_name, bu, supplier_po, origem, supplier_status)) in suppliers.iter().enumerate() {
            let row = (idx + 1) as u32;
            // Apenas coluna A (Supplier ID) fica bloqueada
            worksheet.write_with_format(row, 0, supplier_id, &locked_format)
                .map_err(|e| format!("Erro: {}", e))?;
            // Colunas B a E ficam desbloqueadas para edição
            worksheet.write_with_format(row, 1, vendor_name, &unlocked_format)
                .map_err(|e| format!("Erro: {}", e))?;
            worksheet.write_with_format(row, 2, bu.as_deref().unwrap_or(""), &unlocked_format)
                .map_err(|e| format!("Erro: {}", e))?;
            worksheet.write_with_format(row, 3, supplier_po.as_deref().unwrap_or(""), &unlocked_format)
                .map_err(|e| format!("Erro: {}", e))?;
            worksheet.write_with_format(row, 4, origem.as_deref().unwrap_or(""), &unlocked_format)
                .map_err(|e| format!("Erro: {}", e))?;
            worksheet.write_with_format(row, 5, supplier_status.as_deref().unwrap_or(""), &unlocked_format)
                .map_err(|e| format!("Erro: {}", e))?;
        }

        let last_row = suppliers.len() as u32;
        let validation_end_row = last_row + 1000; // 1000 linhas extras para validação

        // Validação BU
        if !bu_list.is_empty() {
            let bu_validation = DataValidation::new()
                .allow_list_strings(&bu_list)
                .map_err(|e| format!("Erro: {}", e))?
                .set_error_title("BU inválida")
                .map_err(|e| format!("Erro: {}", e))?
                .set_error_message("Selecione uma BU da lista.")
                .map_err(|e| format!("Erro: {}", e))?;

            worksheet.add_data_validation(1, 2, validation_end_row, 2, &bu_validation)
                .map_err(|e| format!("Erro: {}", e))?;
        }

        // Validação Origem
        let origem_list = vec!["Importado", "Nacional"];
        let origem_validation = DataValidation::new()
            .allow_list_strings(&origem_list)
            .map_err(|e| format!("Erro: {}", e))?
            .set_error_title("Origem inválida")
            .map_err(|e| format!("Erro: {}", e))?
            .set_error_message("Selecione Importado ou Nacional.")
            .map_err(|e| format!("Erro: {}", e))?;

        worksheet.add_data_validation(1, 4, validation_end_row, 4, &origem_validation)
            .map_err(|e| format!("Erro: {}", e))?;

        // Validação Supplier Status
        let status_list = vec!["Active", "Inactive"];
        let status_validation = DataValidation::new()
            .allow_list_strings(&status_list)
            .map_err(|e| format!("Erro: {}", e))?
            .set_error_title("Status inválido")
            .map_err(|e| format!("Erro: {}", e))?
            .set_error_message("Selecione Active ou Inactive.")
            .map_err(|e| format!("Erro: {}", e))?;

        worksheet.add_data_validation(1, 5, validation_end_row, 5, &status_validation)
            .map_err(|e| format!("Erro: {}", e))?;

        // Protege planilha principal
        worksheet.protect_with_password("30625629");

        // Cria aba oculta de controle para validação
        let control_sheet = workbook.add_worksheet();
        control_sheet.set_name("_control").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.set_hidden(true);
        
        // Armazena informações de controle
        control_sheet.write_string(0, 0, "VERSION").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(0, 1, "1.0").map_err(|e| format!("Erro: {}", e))?;
        
        control_sheet.write_string(1, 0, "EXPECTED_COLUMNS").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(1, 1, "6").map_err(|e| format!("Erro: {}", e))?;
        
        control_sheet.write_string(2, 0, "COL_0").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(2, 1, "Supplier ID").map_err(|e| format!("Erro: {}", e))?;
        
        control_sheet.write_string(3, 0, "COL_1").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(3, 1, "Vendor Name").map_err(|e| format!("Erro: {}", e))?;
        
        control_sheet.write_string(4, 0, "COL_2").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(4, 1, "BU").map_err(|e| format!("Erro: {}", e))?;
        
        control_sheet.write_string(5, 0, "COL_3").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(5, 1, "Supplier PO").map_err(|e| format!("Erro: {}", e))?;
        
        control_sheet.write_string(6, 0, "COL_4").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(6, 1, "Origem").map_err(|e| format!("Erro: {}", e))?;
        
        control_sheet.write_string(7, 0, "COL_5").map_err(|e| format!("Erro: {}", e))?;
        control_sheet.write_string(7, 1, "Supplier Status").map_err(|e| format!("Erro: {}", e))?;

        println!("✅ Validações aplicadas e planilha protegida");

        let buffer = workbook.save_to_buffer()
            .map_err(|e| format!("Erro ao salvar: {}", e))?;

        println!("✅ Excel gerado ({} bytes)", buffer.len());
        Ok(buffer)
    }

    /// Valida arquivo de importação de suppliers
    pub fn validate_supplier_import(file_content: Vec<u8>) -> Result<String, String> {
        use calamine::{Reader, Xlsx, open_workbook_from_rs};
        use std::io::Cursor;

        let cursor = Cursor::new(file_content);
        let mut workbook: Xlsx<_> = open_workbook_from_rs(cursor)
            .map_err(|e| format!("❌ Erro ao abrir Excel: {}", e))?;

        // Valida aba de controle
        let sheet_names = workbook.sheet_names();
        if !sheet_names.iter().any(|name| name == "_control") {
            return Err("Aba de controle '_control' não encontrada. Use um arquivo exportado pelo sistema.".to_string());
        }

        // Valida estrutura das colunas na aba de controle
        if let Ok(control_range) = workbook.worksheet_range("_control") {
            let expected_columns = vec!["Supplier ID", "Vendor Name", "BU", "Supplier PO", "Origem", "Supplier Status"];
            let mut found_columns = Vec::new();
            
            for row in control_range.rows() {
                if row.len() >= 2 {
                    let key = row[0].to_string();
                    let value = row[1].to_string();
                    if key.starts_with("COL_") {
                        found_columns.push(value);
                    }
                }
            }
            
            if found_columns != expected_columns {
                return Err(format!(
                    "Estrutura de colunas inválida.\n\nEsperado: {:?}\n\nEncontrado: {:?}",
                    expected_columns, found_columns
                ));
            }
        } else {
            return Err("Erro ao ler aba de controle.".to_string());
        }

        let sheet_name = workbook.sheet_names()[0].clone();
        let range = workbook.worksheet_range(&sheet_name)
            .map_err(|e| format!("Erro ao ler planilha: {}", e))?;

        // Valida header da planilha principal
        if let Some(header_row) = range.rows().next() {
            let expected_header = vec!["Supplier ID", "Vendor Name", "BU", "Supplier PO", "Origem", "Supplier Status"];
            let actual_header: Vec<String> = header_row.iter().map(|cell| cell.to_string()).collect();
            
            if actual_header != expected_header {
                return Err(format!(
                    "Cabeçalho inválido.\n\nEsperado: {:?}\n\nEncontrado: {:?}",
                    expected_header, actual_header
                ));
            }
        }

        let total_rows = range.rows().count() - 1; // Subtrai o header
        Ok(format!("Arquivo válido! {} registros encontrados.", total_rows))
    }

    /// Importa suppliers do Excel (UPDATE ou INSERT)
    pub fn import_suppliers(file_content: Vec<u8>) -> Result<String, String> {
        println!("\n📥 ========================================");
        println!("📥 IMPORT_SUPPLIERS CHAMADO!");
        println!("📥 ========================================\n");

        use calamine::{Reader, Xlsx, open_workbook_from_rs};
        use std::io::Cursor;

        let cursor = Cursor::new(file_content);
        let mut workbook: Xlsx<_> = open_workbook_from_rs(cursor)
            .map_err(|e| format!("Erro ao abrir Excel: {}", e))?;

        // Valida aba de controle
        let sheet_names = workbook.sheet_names();
        if !sheet_names.iter().any(|name| name == "_control") {
            return Err("❌ Arquivo inválido: aba de controle não encontrada. Use um arquivo exportado pelo sistema.".to_string());
        }

        // Valida estrutura das colunas na aba de controle
        if let Ok(control_range) = workbook.worksheet_range("_control") {
            let expected_columns = vec!["Supplier ID", "Vendor Name", "BU", "Supplier PO", "Origem", "Supplier Status"];
            let mut found_columns = Vec::new();
            
            for row in control_range.rows() {
                if row.len() >= 2 {
                    let key = row[0].to_string();
                    let value = row[1].to_string();
                    if key.starts_with("COL_") {
                        found_columns.push(value);
                    }
                }
            }
            
            if found_columns != expected_columns {
                return Err(format!(
                    "❌ Estrutura de colunas inválida.\nEsperado: {:?}\nEncontrado: {:?}",
                    expected_columns, found_columns
                ));
            }
            
            println!("✅ Validação de estrutura OK");
        } else {
            return Err("❌ Erro ao ler aba de controle".to_string());
        }

        let sheet_name = workbook.sheet_names()[0].clone();
        let range = workbook.worksheet_range(&sheet_name)
            .map_err(|e| format!("Erro ao ler planilha: {}", e))?;

        // Valida header da planilha principal
        if let Some(header_row) = range.rows().next() {
            let expected_header = vec!["Supplier ID", "Vendor Name", "BU", "Supplier PO", "Origem", "Supplier Status"];
            let actual_header: Vec<String> = header_row.iter().map(|cell| cell.to_string()).collect();
            
            if actual_header != expected_header {
                return Err(format!(
                    "❌ Cabeçalho inválido.\nEsperado: {:?}\nEncontrado: {:?}",
                    expected_header, actual_header
                ));
            }
            println!("✅ Cabeçalho validado");
        }

        let conn_guard = Self::get_connection()?;
        if conn_guard.is_none() {
            return Err("Conexão não inicializada".to_string());
        }
        let conn = conn_guard.as_ref().unwrap();

        let mut updated = 0;
        let mut inserted = 0;
        let mut errors = 0;

        for (idx, row) in range.rows().enumerate() {
            if idx == 0 { continue; } // Pula header

            if row.len() < 6 {
                println!("⚠️ Linha {} ignorada: menos de 6 colunas", idx + 1);
                errors += 1;
                continue;
            }

            let supplier_id = row[0].to_string().trim().to_string();
            let vendor_name = row[1].to_string().trim().to_string();
            let bu = row[2].to_string().trim().to_string();
            let supplier_po_str = row[3].to_string().trim().to_string();
            let origem = row[4].to_string().trim().to_string();
            let supplier_status = row[5].to_string().trim().to_string();
            
            // Converter supplier_po para INTEGER
            let supplier_po: Option<i32> = if supplier_po_str.is_empty() {
                None
            } else {
                match supplier_po_str.parse::<i32>() {
                    Ok(val) => Some(val),
                    Err(_) => {
                        println!("⚠️ Linha {}: supplier_po '{}' não é um número válido, usando None", idx + 1, supplier_po_str);
                        None
                    }
                }
            };

            // DEBUG: Mostrar valores lidos da linha
            println!("🔍 Linha {}: supplier_id='{}', vendor_name='{}', bu='{}', supplier_po_str='{}', origem='{}', supplier_status='{}'", 
                idx + 1, supplier_id, vendor_name, bu, supplier_po_str, origem, supplier_status);
            println!("🔍 Linha {}: supplier_po parsed = {:?}", idx + 1, supplier_po);

            // Se supplier_id está vazio, cria novo registro (obriga vendor_name e supplier_status)
            if supplier_id.is_empty() {
                println!("🔍 Linha {}: supplier_id VAZIO - tentando INSERT", idx + 1);
                
                if vendor_name.is_empty() {
                    println!("⚠️ Linha {} ignorada: vendor_name vazio", idx + 1);
                    errors += 1;
                    continue;
                }

                if supplier_po.is_none() {
                    println!("ℹ️ Linha {}: supplier_po vazio ou inválido, valor será mantido como NULL", idx + 1);
                } else if let Some(po_val) = supplier_po {
                    let existing_po_owner: Option<String> = conn
                        .query_row(
                            "SELECT CAST(supplier_id AS TEXT) FROM supplier_database_table WHERE supplier_po = ?1 LIMIT 1",
                            [po_val],
                            |row| row.get(0)
                        )
                        .optional()
                        .map_err(|e| format!("Erro ao verificar duplicidade de supplier_po: {}", e))?;

                    if let Some(existing_id) = existing_po_owner {
                        println!(
                            "⚠️ Linha {} ignorada: supplier_po '{}' já está em uso pelo supplier_id {}",
                            idx + 1,
                            po_val,
                            existing_id
                        );
                        errors += 1;
                        continue;
                    }
                }
                
                if supplier_status.is_empty() {
                    println!("⚠️ Linha {} ignorada: supplier_status vazio (obrigatório)", idx + 1);
                    errors += 1;
                    continue;
                }

                println!(
                    "📝 Linha {}: INSERT - vendor_name='{}', supplier_po='{:?}'",
                    idx + 1,
                    vendor_name,
                    supplier_po
                );

                // Prepara valores seguindo padrão da criação manual
                let vendor_name_val = vendor_name.as_str();
                let country_orig_val = if origem.is_empty() { "N/A" } else { origem.as_str() };  // origem vai para country
                let bu_val = if bu.is_empty() { "N/A" } else { bu.as_str() };
                let category_val = "N/A";  // supplier_category sempre N/A
                let email_val = "";
                let status_val = if supplier_status.is_empty() { "" } else { supplier_status.as_str() };
                let supplier_name_val = "N/A";
                let planner_val = "";
                let continuity_val = "";
                let sourcing_val = "";
                let sqie_val = "";
                let ssid_val = "";

                let has_supplier_name = Self::supplier_table_has_column(conn, "supplier_name")?;

                println!("📝 Linha {}: Executando INSERT com valores:", idx + 1);
                println!("   - vendor_name: '{}'", vendor_name_val);
                println!("   - country (origem): '{}'", country_orig_val);
                println!("   - bu: '{}'", bu_val);
                println!("   - supplier_category: '{}'", category_val);
                println!("   - supplier_email: '{}'", email_val);
                println!("   - supplier_po: {:?}", supplier_po);
                println!("   - supplier_status: '{}'", status_val);
                println!("   - has_supplier_name column: {}", has_supplier_name);

                let result = if has_supplier_name {
                    println!("   ➡️ Usando INSERT com supplier_name");
                    conn.execute(
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
                            vendor_name_val,
                            supplier_name_val,
                            bu_val,
                            category_val,
                            email_val,
                            supplier_po,
                            status_val,
                            planner_val,
                            country_orig_val,
                            continuity_val,
                            sourcing_val,
                            sqie_val,
                            ssid_val,
                        ]
                    )
                } else {
                    println!("   ➡️ Usando INSERT sem supplier_name");
                    conn.execute(
                        "INSERT INTO supplier_database_table (
                            vendor_name,
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
                            vendor_name_val,
                            bu_val,
                            category_val,
                            email_val,
                            supplier_po,
                            status_val,
                            planner_val,
                            country_orig_val,
                            continuity_val,
                            sourcing_val,
                            sqie_val,
                            ssid_val,
                        ]
                    )
                };

                match result {
                    Ok(rows_affected) => {
                        let new_supplier_id = conn.last_insert_rowid();
                        println!("   ✅ Novo supplier inserido com ID: {} ({} linhas afetadas)", new_supplier_id, rows_affected);
                        inserted += 1;
                    }
                    Err(e) => {
                        println!("   ❌ Erro ao inserir: {}", e);
                        errors += 1;
                    }
                }

                continue;
            }

            // Se supplier_id existe, faz UPDATE
            println!("🔄 Linha {}: UPDATE - supplier_id='{}' (não vazio, tentando atualizar)", idx + 1, supplier_id);
            
            // Verifica se o supplier_id existe no banco
            let check_query = "SELECT COUNT(*) FROM supplier_database_table WHERE supplier_id = ?1";
            let exists: i32 = conn.query_row(check_query, [&supplier_id], |row| row.get(0))
                .unwrap_or(0);

            println!("🔍 Linha {}: Supplier ID '{}' existe no banco? {}", idx + 1, supplier_id, exists > 0);

            if exists > 0 {
                // Verifica se a coluna supplier_name existe
                let has_supplier_name = Self::supplier_table_has_column(conn, "supplier_name")?;
                
                // Prepara valores
                if let Some(po_val) = supplier_po {
                    let existing_po_owner: Option<String> = conn
                        .query_row(
                            "SELECT CAST(supplier_id AS TEXT) FROM supplier_database_table WHERE supplier_po = ?1 LIMIT 1",
                            [po_val],
                            |row| row.get(0)
                        )
                        .optional()
                        .map_err(|e| format!("Erro ao verificar duplicidade de supplier_po: {}", e))?;

                    if let Some(existing_id) = existing_po_owner {
                        if existing_id != supplier_id {
                            println!(
                                "⚠️ Linha {} ignorada: supplier_po '{}' já está em uso pelo supplier_id {}",
                                idx + 1,
                                po_val,
                                existing_id
                            );
                            errors += 1;
                            continue;
                        }
                    }
                }

                let bu_val = if bu.is_empty() { "N/A" } else { bu.as_str() };
                let origem_val = if origem.is_empty() { "N/A" } else { origem.as_str() };
                let status_val = if supplier_status.is_empty() { "" } else { supplier_status.as_str() };
                
                println!("📝 Linha {}: Executando UPDATE com valores:", idx + 1);
                println!("   - vendor_name: '{}'", vendor_name);
                println!("   - bu: '{}'", bu_val);
                println!("   - supplier_po: {:?}", supplier_po);
                println!("   - origem: '{}'", origem_val);
                println!("   - supplier_status: '{}'", status_val);
                println!("   - supplier_id: '{}'", supplier_id);
                println!("   - has_supplier_name: {}", has_supplier_name);
                
                let result = {
                    println!("   ➡️ Usando UPDATE com country (origem)");
                    conn.execute(
                        "UPDATE supplier_database_table SET vendor_name = ?1, bu = ?2, supplier_po = ?3, country = ?4, supplier_status = ?5 WHERE supplier_id = ?6",
                        rusqlite::params![vendor_name.as_str(), bu_val, supplier_po, origem_val, status_val, &supplier_id]
                    )
                };
                
                match result {
                    Ok(rows_affected) => {
                        println!("   ✅ Supplier {} atualizado ({} linhas afetadas)", supplier_id, rows_affected);
                        updated += 1;
                    },
                    Err(e) => {
                        println!("   ❌ Erro ao atualizar {}: {}", supplier_id, e);
                        errors += 1;
                    }
                }
            } else {
                println!("   ⚠️ Supplier ID {} não encontrado no banco, ignorado", supplier_id);
                errors += 1;
            }
        }

        println!("\n✅ Importação concluída:");
        println!("   📊 Atualizados: {}", updated);
        println!("   ➕ Inseridos: {}", inserted);
        println!("   ❌ Erros: {}", errors);

        if errors > 0 {
            Ok(format!("Atualizados: {}\nInseridos: {}\nErros: {}", updated, inserted, errors))
        } else {
            Ok(format!("✅ {} suppliers atualizados e {} inseridos com sucesso!", updated, inserted))
        }
    }
}

