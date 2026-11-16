use std::{
    fs,
    path::{Path, PathBuf},
};
use windows::core::{Interface, HSTRING};
use windows::Win32::System::Com::{
    CoCreateInstance, CoInitializeEx, CoTaskMemFree, CoUninitialize, IPersistFile, CLSCTX_INPROC_SERVER,
    COINIT_APARTMENTTHREADED,
};
use windows::Win32::UI::Shell::{FOLDERID_Desktop, IShellLinkW, SHGetKnownFolderPath, ShellLink, KF_FLAG_DEFAULT};

/// Area de trabalho do usuario (segue o redirecionamento para o OneDrive).
pub fn pasta_desktop() -> Result<PathBuf, String> {
    unsafe {
        let p = SHGetKnownFolderPath(&FOLDERID_Desktop, KF_FLAG_DEFAULT, None).map_err(|e| e.to_string())?;
        let s = p.to_string().map_err(|e| e.to_string());
        CoTaskMemFree(Some(p.0 as *const _));
        Ok(PathBuf::from(s?))
    }
}

/// Cria o atalho so se o marcador nao existir. Devolve true se criou agora.
/// Se o cliente apagar o atalho depois, o marcador impede que ele volte.
pub fn criar_atalho_uma_vez(alvo: &Path, nome: &str, marcador: &Path, desktop: Option<&Path>) -> Result<bool, String> {
    if marcador.exists() {
        return Ok(false);
    }
    let pasta = match desktop {
        Some(d) => d.to_path_buf(),
        None => pasta_desktop()?,
    };
    let lnk = pasta.join(format!("{nome}.lnk"));
    if !lnk.exists() {
        unsafe {
            let init = CoInitializeEx(None, COINIT_APARTMENTTHREADED);
            let r = (|| -> windows::core::Result<()> {
                let link: IShellLinkW = CoCreateInstance(&ShellLink, None, CLSCTX_INPROC_SERVER)?;
                link.SetPath(&HSTRING::from(alvo.as_os_str()))?;
                if let Some(dir) = alvo.parent() {
                    link.SetWorkingDirectory(&HSTRING::from(dir.as_os_str()))?;
                }
                link.SetIconLocation(&HSTRING::from(alvo.as_os_str()), 0)?;
                link.SetDescription(&HSTRING::from(nome))?;
                let pf: IPersistFile = link.cast()?;
                pf.Save(&HSTRING::from(lnk.as_os_str()), true)?;
                Ok(())
            })();
            if init.is_ok() {
                CoUninitialize();
            }
            r.map_err(|e| format!("atalho: {e}"))?;
        }
    }
    if let Some(p) = marcador.parent() {
        fs::create_dir_all(p).map_err(|e| e.to_string())?;
    }
    fs::write(marcador, b"").map_err(|e| e.to_string())?;
    Ok(true)
}
