use std::{cell::RefCell, collections::HashMap, fs};
use techinova_suporte::{atualizar::*, instalar::*, Versao};

const JSON: &[u8] = include_bytes!("fixtures/versao.json");
const SIG: &[u8] = include_bytes!("fixtures/versao.json.sig");
const PUB: &str = include_str!("fixtures/chave-teste.pub");
const FICHA: &str = "https://exemplo.invalid/versao.json";
const EXE_URL: &str =
    "https://github.com/techinova-ti/rustdesk/releases/download/canal-teste/TechInova-Suporte-Remoto.exe";

fn pasta(nome: &str, com_exe: bool) -> std::path::PathBuf {
    let d = std::env::temp_dir().join(format!("tsa-{}-{}", nome, std::process::id()));
    let _ = fs::remove_dir_all(&d);
    fs::create_dir_all(&d).unwrap();
    if com_exe {
        fs::write(d.join(NOME_EXE), b"R6").unwrap();
        gravar_versao(&d, Versao(1, 5, 3, 6)).unwrap();
    }
    d
}

struct Falso {
    m: HashMap<String, Vec<u8>>,
    pedidos: RefCell<Vec<String>>,
}
impl Falso {
    fn novo(exe: &[u8]) -> Falso {
        let mut m = HashMap::new();
        m.insert(FICHA.to_string(), JSON.to_vec());
        m.insert(format!("{FICHA}.sig"), SIG.to_vec());
        m.insert(EXE_URL.to_string(), exe.to_vec());
        Falso { m, pedidos: RefCell::new(vec![]) }
    }
    fn baixar(&self, url: &str, limite: u64) -> Result<Vec<u8>, String> {
        self.pedidos.borrow_mut().push(url.to_string());
        let v = self.m.get(url).cloned().ok_or("404")?;
        if v.len() as u64 > limite {
            return Err("grande".into());
        }
        Ok(v)
    }
    fn pediu_exe(&self) -> bool {
        self.pedidos.borrow().iter().any(|u| u == EXE_URL)
    }
}
fn sem_novo(p: &std::path::Path) -> bool {
    fs::read_dir(p).unwrap().all(|e| !e.unwrap().file_name().to_string_lossy().contains(".novo-"))
}

#[test]
fn atualiza_quando_ha_nova() {
    let p = pasta("a", true);
    let f = Falso::novo(b"EXE NOVO DE TESTE");
    let r = atualizar(&|u, l| f.baixar(u, l), FICHA, PUB, Versao(1, 5, 3, 6), &p).unwrap();
    assert_eq!(r, Atualizacao::Atualizado(Versao(1, 5, 3, 7)));
    assert_eq!(fs::read(p.join(NOME_EXE)).unwrap(), b"EXE NOVO DE TESTE");
    assert_eq!(versao_na_pasta(&p), Some(Versao(1, 5, 3, 7)));
    assert!(sem_novo(&p));
}

#[test]
fn sem_pasta_nao_baixa_nada() {
    let p = pasta("b", false);
    let f = Falso::novo(b"EXE NOVO DE TESTE");
    let r = atualizar(&|u, l| f.baixar(u, l), FICHA, PUB, Versao(1, 5, 3, 6), &p).unwrap();
    assert_eq!(r, Atualizacao::SemPasta);
    assert!(f.pedidos.borrow().is_empty());
}

#[test]
fn mesma_versao_nao_baixa_exe() {
    let p = pasta("c", true);
    gravar_versao(&p, Versao(1, 5, 3, 7)).unwrap();
    let f = Falso::novo(b"EXE NOVO DE TESTE");
    let r = atualizar(&|u, l| f.baixar(u, l), FICHA, PUB, Versao(1, 5, 3, 6), &p).unwrap();
    assert_eq!(r, Atualizacao::JaAtual(Versao(1, 5, 3, 7)));
    assert!(!f.pediu_exe());
}

#[test]
fn propria_mais_nova_que_a_pasta_conta() {
    let p = pasta("d", true);
    let f = Falso::novo(b"EXE NOVO DE TESTE");
    let r = atualizar(&|u, l| f.baixar(u, l), FICHA, PUB, Versao(1, 5, 3, 8), &p).unwrap();
    assert_eq!(r, Atualizacao::JaAtual(Versao(1, 5, 3, 8)));
    assert!(!f.pediu_exe());
}

#[test]
fn exe_adulterado_nao_troca() {
    let p = pasta("e", true);
    let f = Falso::novo(b"EXE NOVO DE TESTX"); // mesmo tamanho, hash diferente
    assert!(atualizar(&|u, l| f.baixar(u, l), FICHA, PUB, Versao(1, 5, 3, 6), &p).is_err());
    assert_eq!(fs::read(p.join(NOME_EXE)).unwrap(), b"R6");
    assert_eq!(versao_na_pasta(&p), Some(Versao(1, 5, 3, 6)));
    assert!(sem_novo(&p));
}

#[test]
fn exe_truncado_nao_troca() {
    let p = pasta("f", true);
    let f = Falso::novo(b"EXE NOVO");
    assert!(atualizar(&|u, l| f.baixar(u, l), FICHA, PUB, Versao(1, 5, 3, 6), &p).is_err());
    assert_eq!(fs::read(p.join(NOME_EXE)).unwrap(), b"R6");
    assert!(sem_novo(&p));
}

#[test]
fn assinatura_errada_nao_baixa_exe() {
    let p = pasta("g", true);
    let mut f = Falso::novo(b"EXE NOVO DE TESTE");
    f.m.insert(format!("{FICHA}.sig"), b"AAAA".to_vec());
    assert!(atualizar(&|u, l| f.baixar(u, l), FICHA, PUB, Versao(1, 5, 3, 6), &p).is_err());
    assert!(!f.pediu_exe());
    assert_eq!(fs::read(p.join(NOME_EXE)).unwrap(), b"R6");
}

#[test]
fn sem_internet_e_erro_sem_mexer() {
    let p = pasta("h", true);
    assert!(atualizar(&|_, _| Err("sem rede".into()), FICHA, PUB, Versao(1, 5, 3, 6), &p).is_err());
    assert_eq!(fs::read(p.join(NOME_EXE)).unwrap(), b"R6");
}
