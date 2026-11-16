use techinova_suporte::{ficha, Versao};
const JSON: &[u8] = include_bytes!("fixtures/versao.json");
const SIG: &[u8] = include_bytes!("fixtures/versao.json.sig");
const PUB: &str = include_str!("fixtures/chave-teste.pub");
const JSON_TESTE: &[u8] = include_bytes!("fixtures/versao-teste.json");
const SIG_TESTE: &[u8] = include_bytes!("fixtures/versao-teste.json.sig");

#[test]
fn versao_le_e_ordena() {
    assert_eq!(Versao::ler("1.5.3-r6"), Some(Versao(1, 5, 3, 6)));
    assert!(Versao::ler("1.5.3-r10").unwrap() > Versao::ler("1.5.3-r9").unwrap());
    assert!(Versao::ler("1.6.0-r1").unwrap() > Versao::ler("1.5.3-r9").unwrap());
    assert_eq!(Versao::ler("1.5.3"), None);
    assert_eq!(Versao::ler("1.5.3.1-r6"), None);
    assert_eq!(Versao::ler("1.5.3-r6\n"), Some(Versao(1, 5, 3, 6)));
    assert_eq!(Versao(1, 5, 3, 6).to_string(), "1.5.3-r6");
}

#[test]
fn ficha_boa_passa() {
    let (f, v) = ficha::verificar(JSON, SIG, PUB, "producao").unwrap();
    assert_eq!(v, Versao(1, 5, 3, 7));
    assert!(f.url.starts_with(ficha::PREFIXO_URL));
    assert_eq!(f.tamanho, 17);
}

#[test]
fn json_alterado_recusa() {
    let mut j = JSON.to_vec();
    let i = j.iter().position(|&b| b == b'7').unwrap();
    j[i] = b'8';
    assert!(ficha::verificar(&j, SIG, PUB, "producao").is_err());
}

#[test]
fn outra_chave_recusa() {
    let outra = "11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo=";
    assert!(ficha::verificar(JSON, SIG, outra, "producao").is_err());
}

#[test]
fn assinatura_lixo_recusa() {
    assert!(ficha::verificar(JSON, b"nao-e-base64!!", PUB, "producao").is_err());
    assert!(ficha::verificar(JSON, b"", PUB, "producao").is_err());
}

#[test]
fn ficha_do_canal_de_teste_nao_vale_em_producao() {
    assert!(ficha::verificar(JSON_TESTE, SIG_TESTE, PUB, "producao").is_err());
    assert!(ficha::verificar(JSON_TESTE, SIG_TESTE, PUB, "teste").is_ok());
    assert!(ficha::verificar(JSON, SIG, PUB, "teste").is_err());
}
