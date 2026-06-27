# Test Strategy

## Offline Unit Tests

The default test suite must run without API keys and without network access. It covers:

- Mode selection defaults to image mode.
- Explicit no-image-generation requests select HTML mode.
- Deck-plan validation catches missing claims, duplicate numbers, and non-sequential slides.
- Starter artifact generation creates the expected image-mode and HTML-mode files.
- Public repo structure exposes one root skill.

Command:

```bash
.venv/bin/python -m pytest -v
```

## Integration Tests

No live integration tests are included in the initial public skill. Rendering belongs to the installing workspace's image-generation tooling.

## Manual Validation Before Push

- `scripts/presentation-skill --help` renders the CLI contract.
- `.env.example` contains fake placeholders only.
- A privacy review finds no real credentials, private 1Password references, local absolute workspace paths, or generated artifacts.
