fn main() {
    // Força rebuild se o ícone mudar
    println!("cargo:rerun-if-changed=icons/cummins.ico");
    println!("cargo:rerun-if-changed=resource.rc");
    println!("cargo:rerun-if-changed=app.manifest");
    
    tauri_build::build()
}
