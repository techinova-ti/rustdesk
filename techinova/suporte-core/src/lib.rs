//! TechInova - Suporte Remoto (r6 em diante): copia para C:\Suporte, atalho e atualizacao assinada.
pub mod atualizar;
pub mod ficha;
pub mod instalar;
pub mod versao;
#[cfg(windows)]
pub mod atalho;
pub use versao::Versao;

pub const PASTA_PADRAO: &str = r"C:\Suporte";
pub const NOME_ATALHO: &str = "TechInova - Suporte Remoto";

/// Versao gravada na compilacao (variavel VERSION do fluxo, ex.: 1.5.3-r6). Sem ela: 0.0.0-r0.
pub fn versao_compilada() -> Versao {
    option_env!("VERSION").and_then(Versao::ler).unwrap_or(Versao(0, 0, 0, 0))
}

/// Primeira execucao (chamada pelo pacote do exe): copia para C:\Suporte e cria o atalho uma vez por usuario.
#[cfg(windows)]
pub fn primeira_execucao() -> Result<(), String> {
    use std::path::Path;
    let propria = versao_compilada();
    if propria == Versao(0, 0, 0, 0) {
        return Err("versao desconhecida; nada feito".into());
    }
    let origem = std::env::current_exe().map_err(|e| e.to_string())?;
    let pasta = Path::new(PASTA_PADRAO);
    instalar::instalar_em_pasta(&origem, pasta, propria).map_err(|e| format!("pasta: {e}"))?;
    let alvo = pasta.join(instalar::NOME_EXE);
    let appdata = std::env::var_os("APPDATA").ok_or("sem APPDATA")?;
    let marcador = Path::new(&appdata).join("TechInova").join("atalho-criado");
    atalho::criar_atalho_uma_vez(&alvo, NOME_ATALHO, &marcador, None)?;
    Ok(())
}
