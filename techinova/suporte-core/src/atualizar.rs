use crate::{ficha, instalar, Versao};
use std::{fs, io::Write, path::Path};

/// Endereco do canal de teste: so a ficha assinada com canal "teste" vale nele.
pub const MARCA_CANAL_TESTE: &str = "/releases/download/canal-teste/";

#[derive(Debug, PartialEq, Eq)]
pub enum Atualizacao {
    SemPasta,
    JaAtual(Versao),
    Atualizado(Versao),
}

/// Le a ficha assinada, confere, baixa o exe se for mais novo e troca o arquivo da pasta.
/// `baixar(url, limite_de_bytes)` e injetado (no app usa reqwest; nos testes, um falso).
pub fn atualizar(
    baixar: &dyn Fn(&str, u64) -> Result<Vec<u8>, String>,
    url_ficha: &str,
    chave_publica_b64: &str,
    propria: Versao,
    pasta: &Path,
) -> Result<Atualizacao, String> {
    let destino = pasta.join(instalar::NOME_EXE);
    instalar::limpar_restos(pasta); // tambem devolve o .antigo de uma troca interrompida
    if !destino.exists() {
        return Ok(Atualizacao::SemPasta);
    }
    let canal = if url_ficha.contains(MARCA_CANAL_TESTE) { "teste" } else { "producao" };
    let base = instalar::versao_na_pasta(pasta).map_or(propria, |v| v.max(propria));
    let json = baixar(url_ficha, 64 * 1024)?;
    let sig = baixar(&format!("{url_ficha}.sig"), 1024)?;
    let (f, nova) = ficha::verificar(&json, &sig, chave_publica_b64, canal)?;
    if nova <= base {
        return Ok(Atualizacao::JaAtual(base));
    }
    let exe = baixar(&f.url, f.tamanho)?;
    if exe.len() as u64 != f.tamanho {
        return Err("download com tamanho errado".into());
    }
    let hash: String = ring::digest::digest(&ring::digest::SHA256, &exe)
        .as_ref()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    if hash != f.sha256 {
        return Err("sha256 do download nao confere".into());
    }
    let tmp = pasta.join(format!("{}.novo-{}", instalar::NOME_EXE, std::process::id()));
    let gravar = || -> std::io::Result<()> {
        let mut a = fs::File::create(&tmp)?;
        a.write_all(&exe)?;
        a.sync_all() // conteudo no disco antes do rename (queda de energia)
    };
    if let Err(e) = gravar().and_then(|_| instalar::trocar_arquivo(&tmp, &destino)) {
        let _ = fs::remove_file(&tmp);
        return Err(format!("troca falhou: {e}"));
    }
    instalar::gravar_versao(pasta, nova).map_err(|e| e.to_string())?;
    Ok(Atualizacao::Atualizado(nova))
}
