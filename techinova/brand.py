#!/usr/bin/env python3
"""TechInova - Suporte Remoto: aplica a marca e o servidor da TechInova sobre o codigo oficial do RustDesk.

Roda na raiz do codigo-fonte (tag oficial). Cada troca confere se o trecho existe e para com erro se nao existir,
para que uma versao nova do RustDesk nunca saia sem a marca sem ninguem perceber.
O RustDesk e AGPL-3.0: este repositorio publico e o codigo-fonte do aplicativo distribuido.
"""
import base64, os, pathlib, re, shutil, sys

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


# 8) quarta versao (pedido do Dann em 28/10/2026): o cliente nao abre as configuracoes
troca(cfg, '("disable-installation".to_owned(), "Y".to_owned())]));',
      '("disable-installation".to_owned(), "Y".to_owned()), ("disable-settings".to_owned(), "Y".to_owned())]));')
troca("flutter/lib/desktop/pages/desktop_home_page.dart", "                        buildPopupMenu(context)\n",
      "                        if (!bind.isDisableSettings()) buildPopupMenu(context)\n")
troca("flutter/lib/desktop/pages/desktop_tab_page.dart",
      "      {SettingsTabKey initialPage = SettingsTabKey.general}) {\n    try {",
      "      {SettingsTabKey initialPage = SettingsTabKey.general}) {\n    if (bind.isDisableSettings()) return;\n    try {")


# 9) quinta versao (decisoes do Dann em 29/10/2026): correcao de seguranca, sem bloco de senha, pesquisa de
#    satisfacao ao fim do atendimento (so tecnico e data), janela de Aceitar com aviso contra golpe, acesso
#    transparente, tela principal mais clara, WhatsApp com o ID e a versao, e o slogan embaixo do logo.
VERSAO = os.environ.get("VERSION", "")
if not VERSAO:
    if os.environ.get("GITHUB_ACTIONS"):
        sys.exit("ERRO: VERSION nao definida no fluxo de compilacao")
    VERSAO = "teste-local"
sm = "flutter/lib/models/server_model.dart"
sp = "flutter/lib/desktop/pages/server_page.dart"
hp = "flutter/lib/desktop/pages/desktop_home_page.dart"
cp = "flutter/lib/desktop/pages/connection_page.dart"

# 9.1) seguranca: o nome do .exe nao troca mais o servidor (antes, "...,host=X,key=Y.exe" levava a marca para outro servidor)
troca("src/platform/windows.rs",
      "pub fn get_license_from_exe_name() -> ResultType<CustomServer> {\n",
      "pub fn get_license_from_exe_name() -> ResultType<CustomServer> {\n"
      "    if true {\n        hbb_common::bail!(\"TechInova: servidor fixo; o nome do arquivo nao troca o servidor\");\n    }\n")

# 9.2) sem o bloco "Senha de uso unico" (com aceite por clique a senha nem e lida pelo servidor)
troca(hp, "          builder: (context, model, child) {\n            return buildPasswordBoard2(context, model);\n          },",
      "          builder: (context, model, child) {\n            final approveMode = model.approveMode.isNotEmpty\n                ? model.approveMode\n                : bind.mainGetOptionSync(key: kOptionApproveMode);\n            if (approveMode == 'click') return const SizedBox.shrink();\n            return buildPasswordBoard2(context, model);\n          },")

# 9.3) acesso transparente: sem tela preta, sem travar mouse/teclado, sem camera; sessao parada cai em 30 min
troca(cfg, '("approve-mode".to_owned(), "click".to_owned())]));',
      '("approve-mode".to_owned(), "click".to_owned()), ("enable-privacy-mode".to_owned(), "N".to_owned()), '
      '("enable-block-input".to_owned(), "N".to_owned()), ("enable-camera".to_owned(), "N".to_owned()), '
      '("access-mode".to_owned(), "custom".to_owned()), ("allow-auto-disconnect".to_owned(), "Y".to_owned()), '
      '("auto-disconnect-timeout".to_owned(), "30".to_owned())]));')
troca(sp, "                      if (isWindows)\n                        buildPermissionIcon(\n                          client.blockInput,",
      "                      if (false)\n                        buildPermissionIcon(\n                          client.blockInput,")
troca(sp, "                      if (bind.mainSupportedPrivacyModeImpls() != '[]')",
      "                      if (false)")

# 9.4) janela de Aceitar: cores da TechInova, aviso contra golpe e so Aceitar / Recusar
troca(sp, "            Color(0xff00bfe1),\n            Color(0xffff6900),", "            Color(0xffff6900),\n            Color(0xffcc5400),")
troca(sp, "    final showAccept = model.approveMode != 'password';\n    return Column(\n      mainAxisAlignment: MainAxisAlignment.end,\n      children: [\n",
      "    final showAccept = model.approveMode != 'password';\n    return Column(\n      mainAxisAlignment: MainAxisAlignment.end,\n      children: [\n"
      "        Container(\n          width: double.infinity,\n          margin: EdgeInsets.all(4),\n          padding: EdgeInsets.all(8),\n"
      "          decoration: BoxDecoration(\n              color: MyTheme.accent.withOpacity(0.12),\n              border: Border.all(color: MyTheme.accent),\n"
      "              borderRadius: BorderRadius.circular(8)),\n          child: Column(\n            crossAxisAlignment: CrossAxisAlignment.start,\n"
      "            children: [\n              Text(translate('scam_title'),\n                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),\n"
      "              Text(translate('scam_text1'), style: TextStyle(fontSize: 12)),\n            ],\n          ),\n        ),\n")
troca(sp, "text: 'Cancel',", "text: 'Decline',")
troca(sp, "                client.disconnected\n            ? Offstage()", "                client.disconnected ||\n                !client.authorized\n            ? Offstage()")
troca(sp, "offstage: !showElevation,", "offstage: true,")
troca(cfg, '("hide-websocket-settings".to_owned(), "Y".to_owned())]));',
      '("hide-websocket-settings".to_owned(), "Y".to_owned()), ("hide-elevate-button-in-accept-window".to_owned(), "Y".to_owned())]));')

# 9.5) tela principal mais clara: ID grande, botao Copiar, sem maximizar, rodape que diz o que acontece
troca(hp, "      margin: const EdgeInsets.only(left: 20, right: 11),\n      height: 57,", "      margin: const EdgeInsets.only(left: 20, right: 11),\n      height: 96,")
troca(hp, "                        style: TextStyle(\n                          fontSize: 22,\n                        ),",
      "                        style: TextStyle(\n                          fontSize: 32,\n                          fontWeight: FontWeight.bold,\n                          letterSpacing: 1.5,\n                        ),")
troca(hp, "                        controller: model.serverId,\n                        readOnly: true,",
      "                        controller: model.serverId,\n                        readOnly: true,\n                        showCursor: false,\n                        enableInteractiveSelection: false,")
troca(hp, "                        if (!bind.isDisableSettings()) buildPopupMenu(context)\n",
      "                        if (!bind.isDisableSettings())\n                          buildPopupMenu(context)\n                        else\n"
      "                          InkWell(\n                            borderRadius: BorderRadius.circular(4),\n                            onTap: () {\n"
      "                              final t = model.serverId.text;\n                              if (!RegExp(r'\\d').hasMatch(t)) return;\n"
      "                              Clipboard.setData(ClipboardData(text: t));\n                              showToast(translate('Copied'));\n                            },\n"
      "                            child: Row(mainAxisSize: MainAxisSize.min, children: [\n"
      "                              Icon(Icons.copy_rounded, size: 15, color: MyTheme.accent),\n                              SizedBox(width: 4),\n"
      "                              Text(translate('Copy'),\n                                  style: TextStyle(fontSize: 13, color: MyTheme.accent)),\n"
      "                            ]).paddingSymmetric(horizontal: 4),\n                          ).marginOnly(top: 5),\n")
troca(hp, '              translate("desk_tip"),\n              overflow: TextOverflow.clip,\n              style: Theme.of(context).textTheme.bodySmall,',
      '              translate("desk_tip"),\n              overflow: TextOverflow.clip,\n              style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.4),')
troca("flutter/lib/desktop/pages/desktop_tab_page.dart", "            body: DesktopTab(\n              controller: tabController,",
      "            body: DesktopTab(\n              controller: tabController,\n              showMaximize: !bind.isIncomingOnly(),")
troca(cp, "    return Text(\n      _svcStopped.value\n",
      "    return Text(\n      stateGlobal.videoConnCount.value > 0\n          ? translate('tech_connected')\n          : _svcStopped.value\n")
troca(cp, "                color: _svcStopped.value ||",
      "                color: stateGlobal.videoConnCount.value > 0\n                    ? MyTheme.accent\n                    : _svcStopped.value ||")

# 9.6) ajuda pelo WhatsApp: telefone escrito, ID e versao ja na mensagem
troca(cd, "launchUrl(Uri.parse('https://wa.me/" + WHATS + "?text=Ol%C3%A1%2C%20preciso%20de%20ajuda%20da%20TechInova'));",
      "final id = gFFI.serverModel.serverId.text;\n        launchUrl(Uri.parse('https://wa.me/" + WHATS + "?text=' +\n"
      "            Uri.encodeComponent('Olá, preciso de ajuda da TechInova.' +\n"
      "                (RegExp(r'\\d').hasMatch(id) ? ' ID deste computador: ' + id + '.' : '') +\n"
      "                ' (versão " + VERSAO + ")')));")
troca(cd, 'translate("powered_by_me"),\n            overflow: TextOverflow.clip,\n',
      'translate("powered_by_me"),\n            overflow: TextOverflow.clip,\n            textAlign: TextAlign.center,\n')
troca(cd, "?.copyWith(fontSize: 11, color: MyTheme.accent, decoration: TextDecoration.underline),",
      "?.copyWith(\n                    fontSize: 13,\n                    fontWeight: FontWeight.w600,\n"
      "                    color: Theme.of(context).brightness == Brightness.dark\n                        ? MyTheme.accent\n                        : MyTheme.idColor,\n"
      "                    decoration: TextDecoration.underline),")
troca("libs/portable/Cargo.toml", '#ProductVersion = ""', 'ProductVersion = "' + VERSAO + '"')

# 9.7) slogan oficial embaixo do logo
troca(cd, "          return Container(\n            constraints: BoxConstraints(maxWidth: 300, maxHeight: 60),\n            child: image,\n          ).marginOnly(left: 12, right: 12, top: 12);",
      "          return Column(\n            mainAxisSize: MainAxisSize.min,\n            children: [\n              Container(\n"
      "                constraints: BoxConstraints(maxWidth: 300, maxHeight: 60),\n                child: image,\n              ),\n"
      "              Text(\n                'Tecnologia que conecta você ao futuro',\n                textAlign: TextAlign.center,\n"
      "                style: TextStyle(\n                    fontSize: 10.5,\n"
      "                    color: Theme.of(context).textTheme.bodySmall?.color?.withOpacity(0.6)),\n"
      "              ).marginOnly(top: 4),\n            ],\n          ).marginOnly(left: 12, right: 12, top: 12);")

# 9.8) textos (re.subn: r'\\n' grava a sequencia \n dentro do .rs)
textos9 = {
    "src/lang/pt_BR.rs": {
        "Your Desktop": "Para receber ajuda",
        "desk_tip": r"1. Passe o ID abaixo ao técnico da TechInova.\\n2. Quando ele pedir acesso, clique em Aceitar.",
        "powered_by_me": r"Precisa de ajuda?\\nWhatsApp (19) 99604-8421",
        "Ready": "Pronto para o técnico conectar",
        "connecting_status": "Conectando... aguarde",
        "not_ready_status": "Sem conexão. Verifique a internet",
        "Request access to your device": "Pedido de acesso ao computador",
        "scam_title": "Atenção: cuidado com golpes",
        "scam_text1": "Só clique em Aceitar se você acabou de passar seu ID ao técnico da TechInova. A TechInova nunca pede senha de banco, código do celular ou PIX.",
    },
    "src/lang/en.rs": {
        "desk_tip": r"1. Give the ID below to the TechInova technician.\\n2. When they ask for access, click Accept.",
        "powered_by_me": r"Need help?\\nWhatsApp +55 19 99604-8421",
        "connecting_status": "Connecting... please wait",
        "not_ready_status": "No connection. Check the internet",
        "scam_title": "Warning: beware of scams",
        "scam_text1": "Only click Accept if you just gave your ID to the TechInova technician. TechInova never asks for bank passwords, phone codes or PIX.",
    },
}
for arq, mapa in textos9.items():
    for chave, texto in mapa.items():
        troca(arq, r'\("' + re.escape(chave) + r'", ".*?"\),', '("' + chave + '", "' + texto + '"),', regex=True)
troca("src/lang/pt_BR.rs", '("Ready", "Pronto para o técnico conectar"),',
      '("Ready", "Pronto para o técnico conectar"),\n        ("tech_connected", "Técnico conectado agora"),')
troca("src/lang/en.rs", '("connecting_status", "Connecting... please wait"),',
      '("connecting_status", "Connecting... please wait"),\n        ("tech_connected", "Technician connected now"),')
troca("src/lang/pt_BR.rs", '("Copied", "Copiado"),', '("Copied", "Copiado"),\n        ("Copy", "Copiar"),')


# 9.9) pesquisa de satisfacao: no fim de um atendimento aceito (2 min ou mais), a janelinha do atendimento
#      mostra um convite com botao; o navegador so abre se o cliente clicar. O Forms recebe so o tecnico
#      e a data com hora (perguntas "Tecnico" e "Data do Atendimento"; a do computador fica para o cliente).
#      PESQUISA vazio = recurso desligado (compila, mas o convite nunca aparece).
PESQUISA = "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=EsoBsqcknU-2Fv2nPLAkeEFuxg9TySlIrvavJbjqc-RURUpKMjdTQUg2OFRZR1ZNT1dLSERTOFBVVy4u&r5cef696bf87a4c9da19898cede947959=TROCATEC&rb6fbb345b4444fbcb25d681293489f47=TROCADATA"
if "'" in PESQUISA:
    sys.exit("ERRO: o link da pesquisa nao pode ter aspas simples")

# como troca(), mas exige exatamente 1 ocorrencia: uma versao nova do RustDesk nao duplica a mudanca em silencio
def troca1(arquivo, antigo, novo):
    n = pathlib.Path(arquivo).read_text(encoding="utf-8").count(antigo)
    if n != 1:
        sys.exit(f"ERRO: esperava 1 ocorrencia em {arquivo}, achei {n}: {antigo[:70]!r}")
    troca(arquivo, antigo, novo)
BLOCO_PESQUISA = r"""// TechInova - pesquisa de satisfacao (techinova/brand.py, secao 9.9).
// Quando termina um atendimento aceito, a janela do atendimento (CM) mostra um convite com
// botao. O navegador so abre se o cliente clicar em "Avaliar o atendimento".
// Link: Microsoft Forms > Obter link pre-preenchido, so com Tecnico (TROCATEC) e Data (TROCADATA).
// Enquanto o link nao comecar com https://, nao ha convite.
const String kPesquisaTechInovaLink = r'COLE_AQUI_O_LINK_DA_PESQUISA';
// Atendimento mais curto que isso (contado do primeiro Aceitar) nao gera convite.
const Duration kPesquisaTechInovaMinimo = Duration(minutes: 2);
// Espera com a janela escondida antes do convite. Se o tecnico voltar nesse tempo
// (queda de rede, Reconectar, troca de remoto para arquivos), nao ha convite.
const Duration kPesquisaTechInovaEspera = Duration(seconds: 40);
// Tempo do convite na tela, em voltas do timer de 500 ms da CM (240 = 2 minutos).
const int kPesquisaTechInovaVoltas = 240;
// Nome que vai no formulario, pelo comeco do nome que o RustDesk do tecnico envia.
// Qualquer outro nome vai em branco (o texto vem de fora e nao e confiavel).
const Map<String, String> kPesquisaTechInovaTecnicos = {
  'dann': 'Dannilo',
  'vinicius': 'Vinicius',
  'vinícius': 'Vinicius',
  'suporte': 'Vinicius',
};

class PesquisaTechInova {
  static bool _convite = false; // convite mostrado nesta janela (processo da CM)
  static bool _pendente = false; // atendimento terminou; esperando para ver se o tecnico volta
  static bool _respondido = false; // o cliente ja clicou em Avaliar ou Agora nao
  static bool _desenhado = false; // ultimo estado do convite que a tela desenhou
  static DateTime? _aceite; // primeiro Aceitar do atendimento atual
  static DateTime _fim = DateTime.now();
  static DateTime _mostradoEm = DateTime.now();
  static String _tecnico = '';

  // O convite vale ate kPesquisaTechInovaVoltas x 500 ms depois de aparecer.
  static bool get convite =>
      _convite &&
      DateTime.now().difference(_mostradoEm) <
          const Duration(milliseconds: 500 * kPesquisaTechInovaVoltas);

  // A janela nao pode fechar: convite na tela ou espera em curso.
  static bool get segurando => convite || _pendente;

  // Timer de 500 ms da CM: true quando a tela precisa ser redesenhada.
  static bool mudou() {
    final c = convite;
    if (c == _desenhado) return false;
    _desenhado = c;
    return true;
  }

  // Timer de 500 ms da CM: ha conexao aceita e ativa.
  static void aceita(bool algumaAtiva) {
    if (!algumaAtiva) return;
    _aceite ??= DateTime.now();
    _pendente = false; // o tecnico voltou: o atendimento continua
    _convite = false;
  }

  // ServerModel.onClientRemove, antes de a aba sair. estavaAceita: a conexao que terminou
  // estava aceita e ativa. outraAtiva: ainda ha outra conexao ativa ou pedido esperando.
  static void fimDaSessao(String tecnico, bool estavaAceita, bool outraAtiva) {
    try {
      if (estavaAceita) _tecnico = _nome(tecnico);
      if (outraAtiva) return; // o atendimento continua em outra aba
      final aceite = _aceite;
      if (aceite == null || _respondido || gFFI.serverModel.hideCm) return;
      if (!kPesquisaTechInovaLink.startsWith('https://')) return;
      if (!isWindows || desktopType != DesktopType.cm) return;
      if (DateTime.now().difference(aceite) < kPesquisaTechInovaMinimo) return;
      _pendente = true;
      final fim = DateTime.now();
      _fim = fim;
      Future.delayed(kPesquisaTechInovaEspera, () => _mostrar(fim));
    } catch (e) {
      debugPrint('PesquisaTechInova.fimDaSessao: $e');
    }
  }

  // Passou a espera: se ninguem voltou, mostra o convite.
  static Future<void> _mostrar(DateTime fim) async {
    if (!_pendente || fim != _fim) return; // cancelado ou substituido
    _pendente = false;
    try {
      final cs = gFFI.serverModel.clients;
      if (_respondido || !cs.every((c) => c.disconnected)) return; // ha conexao ou pedido novo
      _aceite = null; // um proximo atendimento nesta janela conta do proprio Aceitar
      _convite = true;
      _mostradoEm = DateTime.now();
      // da tempo de o timer redesenhar a tela antes de a janela aparecer
      await Future.delayed(const Duration(milliseconds: 600));
      if (!convite) return;
      await windowManager.setOpacity(1);
      await windowManager.restore();
      await windowManager.show();
      // cartao "Desconectado" (arquivo ou chat): volta a ficar minimizado quando o convite vence
      Future.delayed(
          const Duration(milliseconds: 500 * kPesquisaTechInovaVoltas + 1000), () {
        final agora = gFFI.serverModel.clients;
        if (!convite && agora.isNotEmpty && agora.every((c) => c.disconnected)) {
          windowManager.minimize();
        }
      });
    } catch (e) {
      debugPrint('PesquisaTechInova._mostrar: $e');
    }
  }

  static String _nome(String nome) {
    final n = nome.trim().toLowerCase();
    for (final e in kPesquisaTechInovaTecnicos.entries) {
      if (n.startsWith(e.key)) return e.value;
    }
    return '';
  }

  // Botao "Avaliar o atendimento": abre o formulario no navegador padrao do cliente.
  static Future<void> avaliar() async {
    if (_respondido) return; // clique duplo
    _respondido = true;
    _convite = false;
    try {
      final d = _fim;
      String dois(int n) => n.toString().padLeft(2, '0');
      final data =
          '${dois(d.day)}/${dois(d.month)}/${d.year} ${dois(d.hour)}:${dois(d.minute)}';
      final url = kPesquisaTechInovaLink
          .replaceAll('TROCADATA', Uri.encodeComponent(data))
          .replaceAll('TROCATEC', Uri.encodeComponent(_tecnico));
      await launchUrl(Uri.parse(url));
    } catch (e) {
      debugPrint('PesquisaTechInova.avaliar: $e');
    }
  }

  // Botao "Agora nao" (ou "Fechar" no cartao que mostra o convite).
  static void dispensar() {
    _respondido = true;
    _convite = false;
  }

  // O que a janela da CM mostra no lugar de "Aguardando" enquanto o convite vale.
  static Widget tela() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.star_rounded, size: 40, color: MyTheme.accent),
        const SizedBox(height: 12),
        const Text('Atendimento encerrado',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        const Text('Como foi o atendimento? Avalie em 1 minuto.',
            textAlign: TextAlign.center),
        const SizedBox(height: 16),
        dialogButton('Avaliar o atendimento', onPressed: () async {
          await avaliar();
          hideCmWindow();
        }),
        const SizedBox(height: 8),
        dialogButton('Agora não', isOutline: true, onPressed: () {
          dispensar();
          hideCmWindow();
        }),
      ],
    ).paddingSymmetric(horizontal: 24);
  }
}

Widget loadPowered(BuildContext context) {
"""
troca1(cd, 'Widget loadPowered(BuildContext context) {\n', BLOCO_PESQUISA.replace("COLE_AQUI_O_LINK_DA_PESQUISA", PESQUISA))
troca1(sm, '            hideCmWindow();\n            if (_zeroClientLengthCounter++ == 12) {\n              // 6 second\n              windowManager.close();\n            }\n          } else {\n            _zeroClientLengthCounter = 0;\n',
       r"""            if (PesquisaTechInova.mudou()) notifyListeners();
            if (!PesquisaTechInova.convite) hideCmWindow();
            if (PesquisaTechInova.segurando) {
              _zeroClientLengthCounter = 0; // TechInova: convite na tela ou espera em curso
            } else if (_zeroClientLengthCounter++ == 12) {
              // 6 second
              windowManager.close();
            }
          } else {
            _zeroClientLengthCounter = 0;
            PesquisaTechInova.aceita(
                _clients.any((c) => c.authorized && !c.disconnected));
            if (PesquisaTechInova.mudou()) notifyListeners();
""")
troca1(sm, '        if (index >= 0) {\n          if (close) {\n',
       r"""        if (index >= 0) {
          // TechInova: pesquisa de satisfacao. Decide antes de a aba sair, porque se era a
          // ultima a janela fecharia nesta mesma chamada (tabController.remove -> onRemoveId).
          PesquisaTechInova.fimDaSessao(
              _clients[index].name,
              _clients[index].authorized && !_clients[index].disconnected,
              _clients.any((c) => c.id != id && !c.disconnected));
          if (close) {
""")
troca1(sm, '      if (desktopType == DesktopType.cm && _clients.isEmpty) {\n        hideCmWindow();\n',
       r"""      if (desktopType == DesktopType.cm &&
          _clients.isEmpty &&
          !PesquisaTechInova.convite) {
        hideCmWindow();
""")
troca1(sp, '    if (tabController.state.value.tabs.isEmpty) {\n      windowManager.close();\n',
       r"""    if (tabController.state.value.tabs.isEmpty) {
      // TechInova: convite da pesquisa na tela ou espera em curso: o timer da CM fecha depois
      if (PesquisaTechInova.segurando) return;
      windowManager.close();
""")
troca1(sp, '                  child: Text(translate("Waiting")),\n',
       r"""                  child: PesquisaTechInova.convite
                      ? PesquisaTechInova.tela()
                      : Text(translate("Waiting")),
""")
troca1(sp, "  buildDisconnected(BuildContext context) {\n    return Row(\n      mainAxisAlignment: MainAxisAlignment.center,\n      children: [\n        Expanded(\n            child: buildButton(context,\n                color: MyTheme.accent,\n                onClick: handleClose,\n                text: 'Close',\n                textColor: Colors.white)),\n      ],\n    ).marginOnly(bottom: buttonBottomMargin);\n  }\n",
       r"""  buildDisconnected(BuildContext context) {
    // TechInova: com o convite da pesquisa valendo, o cartao "Desconectado" ganha o botao
    final convite = PesquisaTechInova.convite;
    return Column(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        if (convite)
          Text('Como foi o atendimento? Avalie em 1 minuto.',
                  textAlign: TextAlign.center)
              .marginOnly(bottom: 4),
        if (convite)
          Row(
            children: [
              Expanded(
                  child: buildButton(context,
                      color: MyTheme.accent,
                      onClick: () async {
                        await PesquisaTechInova.avaliar();
                        handleClose();
                      },
                      text: 'Avaliar o atendimento',
                      textColor: Colors.white)),
            ],
          ),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Expanded(
                child: buildButton(context,
                    color: convite ? Colors.transparent : MyTheme.accent,
                    border: convite ? Border.all(color: Colors.grey) : null,
                    onClick: () {
                      if (convite) PesquisaTechInova.dispensar();
                      handleClose();
                    },
                    text: 'Close',
                    textColor: convite ? null : Colors.white)),
          ],
        ),
      ],
    ).marginOnly(bottom: buttonBottomMargin);
  }
""")

print("\nMarca da TechInova aplicada.")
