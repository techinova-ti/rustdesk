#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Versao(pub u32, pub u32, pub u32, pub u32);

impl Versao {
    /// "1.5.3-r6" -> Versao(1,5,3,6). Qualquer outro formato: None.
    pub fn ler(s: &str) -> Option<Versao> {
        let (base, rev) = s.trim().split_once("-r")?;
        let mut p = base.split('.');
        let v = Versao(
            p.next()?.parse().ok()?,
            p.next()?.parse().ok()?,
            p.next()?.parse().ok()?,
            rev.parse().ok()?,
        );
        if p.next().is_some() {
            return None;
        }
        Some(v)
    }
}

impl std::fmt::Display for Versao {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}.{}.{}-r{}", self.0, self.1, self.2, self.3)
    }
}
