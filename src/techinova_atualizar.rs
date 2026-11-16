// TechInova (r6): atualizacao automatica assinada. Logica e testes em techinova/suporte-core.
// Uma vez por abertura (60 s depois) e a cada 24 h. O arquivo novo vale na proxima abertura.
use std::{io::Read, path::Path, time::Duration};

const CHAVE: &str = include_str!("../techinova/chave-atualizacao.txt");
const URL_FICHA: &str = "https://github.com/techinova-ti/rustdesk/releases/latest/download/versao.json";
const URL_FICHA_TESTE: &str = "https://github.com/techinova-ti/rustdesk/releases/download/canal-teste/versao.json";

pub fn iniciar() {
    std::thread::spawn(|| loop {
        std::thread::sleep(Duration::from_secs(60));
        let url = if std::env::var("TECHINOVA_CANAL").as_deref() == Ok("teste") {
            URL_FICHA_TESTE
        } else {
            URL_FICHA
        };
        match techinova_suporte::atualizar::atualizar(
            &baixar,
            url,
            CHAVE,
            techinova_suporte::versao_compilada(),
            Path::new(techinova_suporte::PASTA_PADRAO),
        ) {
            Ok(r) => log::info!("TechInova atualizacao: {:?}", r),
            Err(e) => log::warn!("TechInova atualizacao falhou: {}", e),
        }
        std::thread::sleep(Duration::from_secs(24 * 3600));
    });
}

fn baixar(url: &str, limite: u64) -> Result<Vec<u8>, String> {
    let c = reqwest::blocking::Client::builder()
        .connect_timeout(Duration::from_secs(20))
        .timeout(Duration::from_secs(900))
        .build()
        .map_err(|e| e.to_string())?;
    let r = c.get(url).send().map_err(|e| e.to_string())?;
    if !r.status().is_success() {
        return Err(format!("HTTP {} em {}", r.status(), url));
    }
    if r.content_length().is_some_and(|n| n > limite) {
        return Err("arquivo maior que o esperado".into());
    }
    let mut v = Vec::new();
    r.take(limite + 1).read_to_end(&mut v).map_err(|e| e.to_string())?;
    if v.len() as u64 > limite {
        return Err("arquivo maior que o esperado".into());
    }
    Ok(v)
}
