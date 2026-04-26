# Contributing

Thanks for contributing.

## Scope

Contributions are welcome for:
- Bug fixes
- Security hardening
- UI/UX improvements
- Documentation updates
- Tests and reliability

## Local Development

```bash
git clone <your-fork-url>
cd Face-Recognition-Attendance-System
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

## Branch Naming

Use clear branch names:
- `feature/<short-name>`
- `fix/<short-name>`
- `docs/<short-name>`

## Coding Guidelines

- Keep changes focused and minimal.
- Follow existing file style and naming.
- Add or update tests when behavior changes.
- Do not commit secrets or `.env`.
- Update docs for user-facing changes.

## Pull Request Checklist

Before opening PR:
1. Run app locally and test changed flow.
2. Run relevant tests:
   ```bash
   pytest
   ```
3. Update docs if needed.
4. Add clear PR description: what changed and why.

## Security Reporting

If you discover a security issue, do not open a public exploit issue. Share details privately with maintainers first.