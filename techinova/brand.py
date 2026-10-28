#!/usr/bin/env python3
"""TechInova - Suporte Remoto: aplica a marca e o servidor da TechInova sobre o codigo oficial do RustDesk.

Roda na raiz do codigo-fonte (tag oficial). Cada troca confere se o trecho existe e para com erro se nao existir,
para que uma versao nova do RustDesk nunca saia sem a marca sem ninguem perceber.
O RustDesk e AGPL-3.0: este repositorio publico e o codigo-fonte do aplicativo distribuido.
"""
import base64, pathlib, re, shutil, sys

APP = "TechInova - Suporte Remoto"
EMPRESA = "TechInova - Soluções em TI"
SERVIDOR = "rustdesk.techinova-ti.com.br"
ICONES = pathlib.Path("techinova/icons")
CHAVE = pathlib.Path("techinova/chave-publica.txt").read_text().strip()   # chave PUBLICA do servidor (nao e segredo)

def troca(arquivo, antigo, novo, regex=False, vezes=1):
    p = pathlib.Path(arquivo)
    s = p.read_text(encoding="utf-8")
    if regex:
        s2, n = re.subn(antigo, novo, s, count=vezes)
    else:
        n = s.count(antigo)
        s2 = s.replace(antigo, novo, vezes if vezes else -1)
    if n == 0:
        sys.exit(f"ERRO: trecho nao encontrado em {arquivo}: {antigo[:70]!r}")
    p.write_text(s2, encoding="utf-8")
    print(f"ok  {arquivo}: {antigo[:50]!r}")

# 1) nome do aplicativo, servidor e chave
cfg = "libs/hbb_common/src/config.rs"
troca(cfg, 'RwLock::new("RustDesk".to_owned())', f'RwLock::new("{APP}".to_owned())')
troca(cfg, 'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];', f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{SERVIDOR}"];')
troca(cfg, 'OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=', CHAVE)

# 2) informacoes do arquivo .exe no Windows (aparecem em Propriedades)
rc = "flutter/windows/runner/Runner.rc"
troca(rc, 'VALUE "CompanyName", "Purslane Tech Pte. Ltd."', f'VALUE "CompanyName", "{EMPRESA}"')
troca(rc, 'VALUE "FileDescription", "RustDesk Remote Desktop"', f'VALUE "FileDescription", "{APP}"')
troca(rc, 'VALUE "LegalCopyright", "Copyright © 2026 Purslane Tech Pte. Ltd. All rights reserved."', f'VALUE "LegalCopyright", "{EMPRESA}. Baseado no RustDesk (AGPL-3.0)."')
troca(rc, 'VALUE "ProductName", "RustDesk"', f'VALUE "ProductName", "{APP}"')
for cargo in ("Cargo.toml", "libs/portable/Cargo.toml"):
    troca(cargo, 'LegalCopyright = "Copyright © 2026 Purslane Tech Pte. Ltd. All rights reserved."', f'LegalCopyright = "{EMPRESA}. Baseado no RustDesk (AGPL-3.0)."')
    troca(cargo, 'ProductName = "RustDesk"', f'ProductName = "{APP}"')
    troca(cargo, 'FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{APP}"')
    troca(cargo, 'description = "RustDesk Remote Desktop"', f'description = "{APP}"')

# 3) textos em portugues do Brasil: so a traducao (2o texto), nunca a chave de busca
def traducoes(arquivo):
    p = pathlib.Path(arquivo)
    linhas = p.read_text(encoding="utf-8").split("\n")
    n = 0
    for i, l in enumerate(linhas):
        m = re.match(r'^(\s*\(")(.*?)(",\s*")(.*)("\),?\s*)$', l)
        if m and "RustDesk" in m.group(4):
            linhas[i] = m.group(1) + m.group(2) + m.group(3) + m.group(4).replace("RustDesk", APP) + m.group(5)
            n += 1
    p.write_text("\n".join(linhas), encoding="utf-8")
    print(f"ok  {arquivo}: {n} traducoes com o nome do app")
    return n
traducoes("src/lang/pt_BR.rs")

# 4) icones
copias = {
    "icon.ico": ["res/icon.ico"],
    "tray-icon.ico": ["res/tray-icon.ico"],
    "32.png": ["res/32x32.png"],
    "64.png": ["res/64x64.png"],
    "128.png": ["res/128x128.png"],
    "256.png": ["res/128x128@2x.png"],
    "icon-1024.png": ["res/icon.png", "res/mac-icon.png"],
}
for origem, destinos in copias.items():
    for d in destinos:
        shutil.copyfile(ICONES / origem, d); print(f"ok  icone {d}")
shutil.copyfile(ICONES / "icon.ico", "flutter/windows/runner/resources/app_icon.ico"); print("ok  icone flutter/windows/runner/resources/app_icon.ico")
png = base64.b64encode((ICONES / "256.png").read_bytes()).decode()
pathlib.Path("flutter/assets/icon.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="256" height="256" viewBox="0 0 256 256">'
    f'<image width="256" height="256" xlink:href="data:image/png;base64,{png}"/></svg>\n', encoding="utf-8")
print("ok  icone flutter/assets/icon.svg")

# 5) modo "somente receber" (o cliente nao oferece controle remoto) e rede escondida (servidor ja vem embutido)
troca(cfg, 'pub static ref HARD_SETTINGS: RwLock<HashMap<String, String>> = Default::default();',
      'pub static ref HARD_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(HashMap::from([("conn-type".to_owned(), "incoming".to_owned())]));')
troca(cfg, 'pub static ref BUILTIN_SETTINGS: RwLock<HashMap<String, String>> = Default::default();',
      'pub static ref BUILTIN_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(HashMap::from([("hide-network-settings".to_owned(), "Y".to_owned()), ("hide-server-settings".to_owned(), "Y".to_owned()), ("hide-proxy-settings".to_owned(), "Y".to_owned()), ("hide-websocket-settings".to_owned(), "Y".to_owned())]));')

# 6) cores da TechInova (BRAND.md): laranja FF6900, laranja escuro CC5400
LARANJA, LARANJA_ESC = "FF6900", "CC5400"
cd = "flutter/lib/common.dart"
troca(cd, "static const Color accent = Color(0xFF0071FF);", f"static const Color accent = Color(0xFF{LARANJA});")
troca(cd, "static const Color accent50 = Color(0x770071FF);", f"static const Color accent50 = Color(0x77{LARANJA});")
troca(cd, "static const Color accent80 = Color(0xAA0071FF);", f"static const Color accent80 = Color(0xAA{LARANJA});")
troca(cd, "static const Color idColor = Color(0xFF00B6F0);", f"static const Color idColor = Color(0xFF{LARANJA_ESC});")
troca(cd, "static const Color button = Color(0xFF2C8CFF);", f"static const Color button = Color(0xFF{LARANJA});")
troca(cd, "  return Color(0xFF2C8CFF);\n}", f"  return Color(0xFF{LARANJA});\n}}")
troca(cd, "primary: Colors.blue, secondary: accent, background: grayBg)", f"primary: Color(0xFF{LARANJA}), secondary: accent, background: grayBg)")
troca(cd, "      primary: Colors.blue,\n      secondary: accent,", f"      primary: Color(0xFF{LARANJA}),\n      secondary: accent,")
troca(cd, "        color: Colors.blue,\n        decoration: TextDecoration.underline,", f"        color: Color(0xFF{LARANJA}),\n        decoration: TextDecoration.underline,")
troca("flutter/lib/desktop/pages/server_page.dart", "Color(0xff0071ff)", f"Color(0xff{LARANJA.lower()})")
troca("flutter/lib/desktop/pages/desktop_setting_page.dart", "Color(0xFF2c8cff)", f"Color(0xFF{LARANJA.lower()})")


# 7) terceira versao (decisoes do Dann em 28/10/2026): so portatil, aceitar com clique, logo no topo,
#    "Precisa de ajuda?" abrindo o WhatsApp do suporte e texto da tela orientando o cliente. O tema segue o Windows.
WHATS = "5519996048421"   # celular corporativo do suporte
troca(cfg, '("conn-type".to_owned(), "incoming".to_owned())]));',
      '("conn-type".to_owned(), "incoming".to_owned()), ("disable-installation".to_owned(), "Y".to_owned())]));')
troca(cfg, 'pub static ref OVERWRITE_SETTINGS: RwLock<HashMap<String, String>> = Default::default();',
      'pub static ref OVERWRITE_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(HashMap::from([("approve-mode".to_owned(), "click".to_owned())]));')
for nome in ("logo_dark.png", "logo_light.png"):
    shutil.copyfile(ICONES / nome, f"flutter/assets/{nome}"); print(f"ok  logo flutter/assets/{nome}")
troca(cd, "launchUrl(Uri.parse('https://rustdesk.com'));\n      },\n      child: Opacity(\n          opacity: 0.5,",
      "launchUrl(Uri.parse('https://wa.me/" + WHATS + "?text=Ol%C3%A1%2C%20preciso%20de%20ajuda%20da%20TechInova'));\n      },\n      child: Opacity(\n          opacity: 1.0,")
troca(cd, 'translate("powered_by_me"),\n            overflow: TextOverflow.clip,\n            style: Theme.of(context)\n                .textTheme\n                .bodySmall\n                ?.copyWith(fontSize: 9, decoration: TextDecoration.underline),',
      'translate("powered_by_me"),\n            overflow: TextOverflow.clip,\n            style: Theme.of(context)\n                .textTheme\n                .bodySmall\n                ?.copyWith(fontSize: 11, color: MyTheme.accent, decoration: TextDecoration.underline),')
textos = {
    "src/lang/pt_BR.rs": {"powered_by_me": "Precisa de ajuda? Fale com a TechInova pelo WhatsApp",
                          "desk_tip": "Passe este ID ao técnico da TechInova. Quando ele conectar, clique em Aceitar."},
    "src/lang/en.rs": {"powered_by_me": "Need help? Talk to TechInova on WhatsApp",
                       "desk_tip": "Give this ID to the TechInova technician. When they connect, click Accept."},
}
for arq, mapa in textos.items():
    for chave, texto in mapa.items():
        troca(arq, r'\("' + chave + r'", ".*?"\),', '("' + chave + '", "' + texto + '"),', regex=True)

print("\nMarca da TechInova aplicada.")
