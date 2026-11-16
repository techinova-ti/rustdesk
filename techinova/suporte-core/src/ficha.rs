use crate::Versao;
use base64::Engine;
use serde::Deserialize;

pub const CONTEXTO: &[u8] = b"TechInova atualizacao v1\n";
pub const APP: &str = "techinova-suporte-remoto";
pub const PREFIXO_URL: &str = "https://github.com/techinova-ti/rustdesk/releases/download/";
pub const LIMITE_EXE: u64 = 300 * 1024 * 1024;

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Ficha {
    pub app: String,
    pub canal: String,
    pub versao: String,
    pub url: String,
    pub sha256: String,
    pub tamanho: u64,
}

fn b64(s: &[u8]) -> Result<Vec<u8>, String> {
    let t = std::str::from_utf8(s).map_err(|_| "base64 invalido".to_string())?.trim();
    base64::engine::general_purpose::STANDARD
        .decode(t)
        .map_err(|_| "base64 invalido".to_string())
}

/// Confere a assinatura ANTES de ler o JSON; depois valida cada campo.
/// `canal_esperado` ("producao" ou "teste"): uma ficha do canal de teste nunca vale no endereco de producao.
pub fn verificar(
    json: &[u8],
    assinatura_b64: &[u8],
    chave_publica_b64: &str,
    canal_esperado: &str,
) -> Result<(Ficha, Versao), String> {
    let chave = b64(chave_publica_b64.as_bytes())?;
    if chave.len() != 32 {
        return Err("chave publica invalida".into());
    }
    let sig = b64(assinatura_b64)?;
    if sig.len() != 64 {
        return Err("assinatura com tamanho errado".into());
    }
    let mut msg = CONTEXTO.to_vec();
    msg.extend_from_slice(json);
    ring::signature::UnparsedPublicKey::new(&ring::signature::ED25519, &chave)
        .verify(&msg, &sig)
        .map_err(|_| "assinatura nao confere".to_string())?;
    let f: Ficha = serde_json::from_slice(json).map_err(|e| format!("ficha invalida: {e}"))?;
    if f.app != APP {
        return Err("ficha de outro aplicativo".into());
    }
    if f.canal != canal_esperado {
        return Err(format!("ficha do canal {}, esperado {}", f.canal, canal_esperado));
    }
    let v = Versao::ler(&f.versao).ok_or("versao invalida na ficha")?;
    if !f.url.starts_with(PREFIXO_URL) || f.url.contains("..") || f.url.contains('?') || f.url.contains('#') {
        return Err("url fora do GitHub da TechInova".into());
    }
    if f.sha256.len() != 64 || !f.sha256.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)) {
        return Err("sha256 invalido".into());
    }
    if f.tamanho == 0 || f.tamanho > LIMITE_EXE {
        return Err("tamanho invalido".into());
    }
    Ok((f, v))
}
