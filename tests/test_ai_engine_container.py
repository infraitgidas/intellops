"""Ancla el empaquetado y el arranque del worker de reglas (ISS-B-14).

El motor importa `ml.rules` como paquete top-level. La imagen del
`intellops-ai-engine` copiaba solo `entrypoint.py` (placeholder de S1-03), así
que con el motor real habría arrancado con `ModuleNotFoundError: No module
named 'ml.rules'`. Estos tests leen el Dockerfile y el entrypoint para que el
empaquetado no pueda divergir de los imports sin que la suite lo note.
"""

from pathlib import Path

DOCKERFILE = Path("src/ml/Dockerfile")
ENTRYPOINT = Path("src/ml/entrypoint.py")


def test_image_packages_the_full_source_tree():
    """La imagen copia `src/` y expone `ml.*` como top-level (PYTHONPATH)."""
    content = DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY src/ src/" in content
    assert "ENV PYTHONPATH=/app/src" in content


def test_image_runs_the_rules_entrypoint_as_a_module():
    """El CMD arranca el entrypoint del motor y el worker no expone puertos."""
    content = DOCKERFILE.read_text(encoding="utf-8")
    assert "ml.entrypoint" in content
    assert "EXPOSE" not in content


def test_entrypoint_imports_the_rules_package_as_top_level():
    """El entrypoint importa `ml.rules`, no `src.ml.rules` (path del runtime)."""
    source = ENTRYPOINT.read_text(encoding="utf-8")
    assert "from ml.rules" in source
    assert "src.ml.rules" not in source
