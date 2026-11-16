use crate::Versao;
use std::{
    fs,
    io::{self, Write},
    path::Path,
};

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
/// Se o exe sumiu (queda de energia entre os dois renames da troca), o .antigo mais recente volta para o lugar.
pub fn limpar_restos(pasta: &Path) {
    let destino = pasta.join(NOME_EXE);
    let mut antigos = Vec::new();
    let mut novos = Vec::new();
    if let Ok(it) = fs::read_dir(pasta) {
        for e in it.flatten() {
            let n = e.file_name().to_string_lossy().to_string();
            if n.starts_with(PREFIXO_ANTIGO) {
                let t = e.metadata().and_then(|m| m.modified()).ok();
                antigos.push((e.path(), t));
            } else if n.starts_with(PREFIXO_NOVO) {
                novos.push(e.path());
            }
        }
    }
    if !destino.exists() {
        antigos.sort_by_key(|(_, t)| *t);
        if let Some((p, _)) = antigos.pop() {
            let _ = fs::rename(&p, &destino);
        }
    }
    for (p, _) in antigos {
        let _ = fs::remove_file(p);
    }
    for p in novos {
        let _ = fs::remove_file(p);
    }
}

/// Copia so o conteudo (fs::copy levaria junto o Zone.Identifier, a marca de "baixado da internet")
/// e garante o conteudo no disco antes da troca.
fn copiar_conteudo(origem: &Path, tmp: &Path) -> io::Result<()> {
    let dados = fs::read(origem)?;
    let mut a = fs::File::create(tmp)?;
    a.write_all(&dados)?;
    a.sync_all()
}

/// Pasta criada pelo app: so SYSTEM e Administradores com controle total, o dono (quem instalou) com
/// Modificar e os outros usuarios so com Ler e executar. Sem heranca da raiz do C: (que da Modificar a todos).
#[cfg(windows)]
fn proteger_pasta(pasta: &Path) -> io::Result<()> {
    use windows::core::HSTRING;
    use windows::Win32::Foundation::{LocalFree, HLOCAL};
    use windows::Win32::Security::Authorization::{
        ConvertStringSecurityDescriptorToSecurityDescriptorW, SDDL_REVISION_1,
    };
    use windows::Win32::Security::{
        SetFileSecurityW, DACL_SECURITY_INFORMATION, PROTECTED_DACL_SECURITY_INFORMATION, PSECURITY_DESCRIPTOR,
    };
    const SDDL: &str = "D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1301bf;;;OW)(A;OICI;0x1200a9;;;BU)";
    unsafe {
        let mut sd = PSECURITY_DESCRIPTOR::default();
        ConvertStringSecurityDescriptorToSecurityDescriptorW(&HSTRING::from(SDDL), SDDL_REVISION_1, &mut sd, None)
            .map_err(|e| io::Error::new(io::ErrorKind::Other, e.to_string()))?;
        let ok = SetFileSecurityW(
            &HSTRING::from(pasta.as_os_str()),
            DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION,
            sd,
        );
        let _ = LocalFree(Some(HLOCAL(sd.0)));
        if !ok.as_bool() {
            return Err(io::Error::last_os_error());
        }
    }
    Ok(())
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
    let criada_agora = !pasta.exists();
    fs::create_dir_all(pasta)?;
    #[cfg(windows)]
    if criada_agora {
        if let Err(e) = proteger_pasta(pasta) {
            let _ = fs::remove_dir(pasta);
            return Err(e);
        }
    }
    #[cfg(not(windows))]
    let _ = criada_agora;
    limpar_restos(pasta);
    if destino.exists() {
        if let Some(v) = versao_na_pasta(pasta) {
            if v >= propria {
                return Ok(Instalacao::JaAtual);
            }
        }
    }
    let tmp = pasta.join(format!("{}{}", PREFIXO_NOVO, std::process::id()));
    if let Err(e) = copiar_conteudo(origem, &tmp).and_then(|_| trocar_arquivo(&tmp, &destino)) {
        let _ = fs::remove_file(&tmp);
        return Err(e);
    }
    gravar_versao(pasta, propria)?;
    Ok(Instalacao::Copiado)
}
