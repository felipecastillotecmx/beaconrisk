# Protección de rama (`main`) con Quality Gate y tests

## Pasos por interfaz de GitHub
1. Settings → Branches → Branch protection rules → **Add rule**.
2. Branch name pattern: `main`.
3. Habilitar **Require a pull request before merging** (1+ approval, dismiss stale).
4. Habilitar **Require status checks to pass before merging** y marcar:
   - `CI — Tests & SonarQube / Unit tests & coverage`
   - `CI — Tests & SonarQube / SonarQube Scan & Quality Gate`
5. (Opcional) **Require branches to be up to date** y **Require signed commits**.
6. Guardar.

> Los nombres de checks corresponden al `name` del workflow y al `name` de cada *job*.

## Pasos con GitHub CLI (reemplaza OWNER/REPO)
```bash
OWNER=tu-org
REPO=tu-repo
gh api -X PUT repos/$OWNER/$REPO/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -F required_status_checks.strict=true \  -F required_status_checks.contexts[]="CI — Tests & SonarQube / Unit tests & coverage" \  -F required_status_checks.contexts[]="CI — Tests & SonarQube / SonarQube Scan & Quality Gate" \  -F enforce_admins=true \  -F required_pull_request_reviews.dismiss_stale_reviews=true \  -F restrictions=
```
