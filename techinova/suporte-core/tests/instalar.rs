use std::fs;
use techinova_suporte::{instalar::*, Versao};

fn tmp(nome: &str) -> std::path::PathBuf {
    let d = std::env::temp_dir().join(format!("tsc-{}-{}", nome, std::process::id()));
    let _ = fs::remove_dir_all(&d);
    fs::create_dir_all(&d).unwrap();
    d
}
fn restos(p: &std::path::Path) -> Vec<String> {
    fs::read_dir(p)
        .unwrap()
        .map(|e| e.unwrap().file_name().into_string().unwrap())
        .filter(|n| n.contains(".novo-") || n.contains(".antigo-"))
        .collect()
}

#[test]
fn primeira_vez_copia_e_grava_versao() {
    let d = tmp("a");
    let origem = d.join("baixado.exe");
    fs::write(&origem, b"R6").unwrap();
    let pasta = d.join("Suporte");
    assert_eq!(instalar_em_pasta(&origem, &pasta, Versao(1, 5, 3, 6)).unwrap(), Instalacao::Copiado);
    assert_eq!(fs::read(pasta.join(NOME_EXE)).unwrap(), b"R6");
    assert_eq!(versao_na_pasta(&pasta), Some(Versao(1, 5, 3, 6)));
}

#[test]
fn ja_na_pasta_nao_faz_nada() {
    let d = tmp("b");
    let pasta = d.join("Suporte");
    fs::create_dir_all(&pasta).unwrap();
    let exe = pasta.join(NOME_EXE);
    fs::write(&exe, b"R6").unwrap();
    assert_eq!(instalar_em_pasta(&exe, &pasta, Versao(1, 5, 3, 6)).unwrap(), Instalacao::JaEstaNaPasta);
    assert_eq!(fs::read(&exe).unwrap(), b"R6");
}

#[test]
fn nao_rebaixa() {
    let d = tmp("c");
    let pasta = d.join("Suporte");
    fs::create_dir_all(&pasta).unwrap();
    fs::write(pasta.join(NOME_EXE), b"R7").unwrap();
    gravar_versao(&pasta, Versao(1, 5, 3, 7)).unwrap();
    let velho = d.join("velho.exe");
    fs::write(&velho, b"R6").unwrap();
    assert_eq!(instalar_em_pasta(&velho, &pasta, Versao(1, 5, 3, 6)).unwrap(), Instalacao::JaAtual);
    assert_eq!(fs::read(pasta.join(NOME_EXE)).unwrap(), b"R7");
    assert_eq!(versao_na_pasta(&pasta), Some(Versao(1, 5, 3, 7)));
}

#[test]
fn sem_versao_txt_troca() {
    let d = tmp("d");
    let pasta = d.join("Suporte");
    fs::create_dir_all(&pasta).unwrap();
    fs::write(pasta.join(NOME_EXE), b"QUALQUER").unwrap();
    let novo = d.join("novo.exe");
    fs::write(&novo, b"R6").unwrap();
    assert_eq!(instalar_em_pasta(&novo, &pasta, Versao(1, 5, 3, 6)).unwrap(), Instalacao::Copiado);
    assert_eq!(fs::read(pasta.join(NOME_EXE)).unwrap(), b"R6");
    assert!(restos(&pasta).is_empty());
}

#[test]
fn troca_com_destino_existente_limpa_restos() {
    let d = tmp("e");
    let destino = d.join(NOME_EXE);
    fs::write(&destino, b"VELHO").unwrap();
    let novo = d.join("x.novo-1");
    fs::write(&novo, b"NOVO").unwrap();
    trocar_arquivo(&novo, &destino).unwrap();
    assert_eq!(fs::read(&destino).unwrap(), b"NOVO");
    assert!(restos(&d).is_empty());
}

#[test]
fn troca_que_falha_devolve_o_antigo() {
    let d = tmp("f");
    let destino = d.join(NOME_EXE);
    fs::write(&destino, b"VELHO").unwrap();
    let novo_inexistente = d.join("nao-existe.novo-1");
    assert!(trocar_arquivo(&novo_inexistente, &destino).is_err());
    assert_eq!(fs::read(&destino).unwrap(), b"VELHO");
}

#[test]
fn limpar_restos_apaga_so_os_nossos() {
    let d = tmp("g");
    for n in ["TechInova-Suporte-Remoto.antigo-9", "TechInova-Suporte-Remoto.exe.novo-9", "outro.txt"] {
        fs::write(d.join(n), b"x").unwrap();
    }
    limpar_restos(&d);
    assert!(restos(&d).is_empty());
    assert!(d.join("outro.txt").exists());
}

#[cfg(windows)]
#[test]
fn renomeia_exe_aberto() {
    // O Windows deixa renomear um exe em execucao: a troca nao pode falhar com o app aberto.
    let d = tmp("h");
    let destino = d.join(NOME_EXE);
    fs::copy(std::env::current_exe().unwrap(), &destino).unwrap();
    let mut filho = std::process::Command::new(&destino)
        .args(["--ignored", "--exact", "espera_aberto"])
        .stdout(std::process::Stdio::null())
        .spawn()
        .unwrap();
    std::thread::sleep(std::time::Duration::from_secs(2));
    assert!(filho.try_wait().unwrap().is_none(), "o filho precisa estar aberto durante a troca");
    let novo = d.join("y.novo-1");
    fs::write(&novo, b"NOVO").unwrap();
    let r = trocar_arquivo(&novo, &destino);
    let _ = filho.kill();
    let _ = filho.wait();
    r.unwrap();
    assert_eq!(fs::read(&destino).unwrap(), b"NOVO");
}

#[test]
#[ignore]
fn espera_aberto() {
    // Usado por renomeia_exe_aberto: mantem uma copia do binario de teste aberta.
    std::thread::sleep(std::time::Duration::from_secs(15));
}

#[test]
fn limpar_restos_recupera_antigo_quando_falta_o_exe() {
    let d = tmp("i");
    fs::write(d.join("TechInova-Suporte-Remoto.antigo-123"), b"BOM").unwrap();
    fs::write(d.join("TechInova-Suporte-Remoto.exe.novo-123"), b"PELA METADE").unwrap();
    limpar_restos(&d);
    assert_eq!(fs::read(d.join(NOME_EXE)).unwrap(), b"BOM");
    assert!(restos(&d).is_empty());
}

#[test]
fn copia_de_downloads_com_pasta_so_com_antigo_nao_perde_a_versao_boa() {
    let d = tmp("j");
    let pasta = d.join("Suporte");
    fs::create_dir_all(&pasta).unwrap();
    fs::write(pasta.join("TechInova-Suporte-Remoto.antigo-123"), b"R7").unwrap();
    gravar_versao(&pasta, Versao(1, 5, 3, 7)).unwrap();
    let velho = d.join("velho.exe");
    fs::write(&velho, b"R6").unwrap();
    assert_eq!(instalar_em_pasta(&velho, &pasta, Versao(1, 5, 3, 6)).unwrap(), Instalacao::JaAtual);
    assert_eq!(fs::read(pasta.join(NOME_EXE)).unwrap(), b"R7");
}

#[cfg(windows)]
#[test]
fn copia_sem_a_marca_de_baixado_da_internet() {
    let d = tmp("k");
    let origem = d.join("baixado.exe");
    fs::write(&origem, b"R6").unwrap();
    fs::write(format!("{}:Zone.Identifier", origem.display()), b"[ZoneTransfer]\r\nZoneId=3\r\n").unwrap();
    assert!(fs::metadata(format!("{}:Zone.Identifier", origem.display())).is_ok());
    let pasta = d.join("Suporte");
    instalar_em_pasta(&origem, &pasta, Versao(1, 5, 3, 6)).unwrap();
    assert!(fs::metadata(format!("{}:Zone.Identifier", pasta.join(NOME_EXE).display())).is_err());
}

#[cfg(windows)]
fn icacls(p: &std::path::Path) -> String {
    let o = std::process::Command::new("icacls").arg(p).output().unwrap();
    String::from_utf8_lossy(&o.stdout).to_string()
}

#[cfg(windows)]
#[test]
fn pasta_criada_pelo_app_fica_protegida() {
    let d = tmp("l");
    let origem = d.join("baixado.exe");
    fs::write(&origem, b"R6").unwrap();
    let pasta = d.join("Suporte");
    assert_eq!(instalar_em_pasta(&origem, &pasta, Versao(1, 5, 3, 6)).unwrap(), Instalacao::Copiado);
    let a = icacls(&pasta);
    assert!(a.contains("BUILTIN\\Users:(OI)(CI)(RX)"), "{a}");
    assert!(a.contains("OWNER RIGHTS:(OI)(CI)(M)"), "{a}");
    assert!(!a.contains("Authenticated Users"), "{a}");
    assert!(!a.contains("(I)"), "nada herdado: {a}");
    // o proprio usuario continua conseguindo atualizar
    let novo = d.join("novo.exe");
    fs::write(&novo, b"R7").unwrap();
    assert_eq!(instalar_em_pasta(&novo, &pasta, Versao(1, 5, 3, 7)).unwrap(), Instalacao::Copiado);
}

#[cfg(windows)]
#[test]
fn pasta_que_ja_existia_nao_tem_permissao_alterada() {
    let d = tmp("m");
    let pasta = d.join("Suporte");
    fs::create_dir_all(&pasta).unwrap();
    let antes = icacls(&pasta);
    let origem = d.join("baixado.exe");
    fs::write(&origem, b"R6").unwrap();
    instalar_em_pasta(&origem, &pasta, Versao(1, 5, 3, 6)).unwrap();
    assert_eq!(icacls(&pasta), antes);
}
