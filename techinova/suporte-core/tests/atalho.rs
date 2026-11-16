#![cfg(windows)]
use std::fs;
use techinova_suporte::atalho::{criar_atalho_uma_vez, pasta_desktop};

#[test]
fn cria_uma_vez_e_respeita_apagado() {
    let d = std::env::temp_dir().join(format!("tst-atalho-{}", std::process::id()));
    let _ = fs::remove_dir_all(&d);
    fs::create_dir_all(&d).unwrap();
    let alvo = d.join("TechInova-Suporte-Remoto.exe");
    fs::write(&alvo, b"x").unwrap();
    let marcador = d.join("TechInova").join("atalho-criado");
    let lnk = d.join("TechInova - Suporte Remoto.lnk");
    assert!(criar_atalho_uma_vez(&alvo, "TechInova - Suporte Remoto", &marcador, Some(&d)).unwrap());
    assert!(lnk.exists() && marcador.exists());
    fs::remove_file(&lnk).unwrap(); // cliente apagou
    assert!(!criar_atalho_uma_vez(&alvo, "TechInova - Suporte Remoto", &marcador, Some(&d)).unwrap());
    assert!(!lnk.exists()); // nao volta
}

#[test]
fn desktop_real_existe() {
    // So confere que a area de trabalho e encontrada (nao cria nada nela).
    assert!(pasta_desktop().unwrap().is_dir());
}
