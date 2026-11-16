use crate::Versao;
use std::{fs, io, path::Path};

pub const NOME_EXE: &str = "TechInova-Suporte-Remoto.exe";
pub const ARQ_VERSAO: &str = "versao.txt";
const PREFIXO_ANTIGO: &str = "TechInova-Suporte-Remoto.antigo-";
const PREFIXO_NOVO: &str = "TechInova-Suporte-Remoto.exe.novo-";

#[derive(Debug, PartialEq, Eq)]
pub enum Instalacao {
    JaEstaNaPasta,
    Copiado,
    JaAtual,
}

pub fn versao_na_pasta(pasta: &Path) -> Option<Versao> {
    fs::read_to_string(pasta.join(ARQ_VERSAO)).ok().and_then(|s| Versao::ler(&s))
}

pub fn gravar_versao(pasta: &Path, v: Versao) -> io::Result<()> {
    fs::write(pasta.join(ARQ_VERSAO), v.to_string())
}

/// Apaga sobras de trocas anteriores (o .antigo de um exe que estava aberto, .novo de um download interrompido).
pub fn limpar_restos(pasta: &Path) {
    if let Ok(it) = fs::read_dir(pasta) {
        for e in it.flatten() {
            let n = e.file_name().to_string_lossy().to_string();
            if n.starts_with(PREFIXO_ANTIGO) || n.starts_with(PREFIXO_NOVO) {
                let _ = fs::remove_file(e.path());
            }
        }
    }
}

/// Poe `novo` no lugar de `destino`. Se `destino` existe (mesmo aberto), ele e renomeado antes;
/// se a troca falhar, o antigo volta para o lugar.
pub fn trocar_arquivo(novo: &Path, destino: &Path) -> io::Result<()> {
    if !destino.exists() {
        return fs::rename(novo, destino);
    }
    let antigo = destino.with_file_name(format!("{}{}", PREFIXO_ANTIGO, std::process::id()));
    let _ = fs::remove_file(&antigo);
    fs::rename(destino, &antigo)?;
    if let Err(e) = fs::rename(novo, destino) {
        let _ = fs::rename(&antigo, destino);
        return Err(e);
    }
    let _ = fs::remove_file(&antigo); // falha se o exe antigo estiver aberto; limpar_restos apaga depois
    Ok(())
}

fn mesmo_arquivo(a: &Path, b: &Path) -> bool {
    match (fs::canonicalize(a), fs::canonicalize(b)) {
        (Ok(x), Ok(y)) => x == y,
        _ => false,
    }
}

pub fn instalar_em_pasta(origem: &Path, pasta: &Path, propria: Versao) -> io::Result<Instalacao> {
    let destino = pasta.join(NOME_EXE);
    if mesmo_arquivo(origem, &destino) {
        limpar_restos(pasta);
        return Ok(Instalacao::JaEstaNaPasta);
    }
    fs::create_dir_all(pasta)?;
    limpar_restos(pasta);
    if destino.exists() {
        if let Some(v) = versao_na_pasta(pasta) {
            if v >= propria {
                return Ok(Instalacao::JaAtual);
            }
        }
    }
    let tmp = pasta.join(format!("{}{}", PREFIXO_NOVO, std::process::id()));
    if let Err(e) = fs::copy(origem, &tmp).and_then(|_| trocar_arquivo(&tmp, &destino)) {
        let _ = fs::remove_file(&tmp);
        return Err(e);
    }
    gravar_versao(pasta, propria)?;
    Ok(Instalacao::Copiado)
}
