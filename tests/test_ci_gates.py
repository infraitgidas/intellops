"""Pin tests de los quality gates del CI (B.9, issue #71; S11–S14).

S14 pide "gates documentados y verificados con un PR de prueba". La rama de
este cambio es local (sin push y sin PR), así que ese PR de prueba no existe:
este archivo es el **sustituto local**. Fija en `.github/workflows/ci.yml` las
tres condiciones que el PR de prueba habría demostrado:

- S11: la cobertura por debajo de 70 % falla el job (umbral explícito, sin
  `continue-on-error`).
- S12: un warning o error de flake8/pylint falla el job.
- S13: un contrato OpenAPI inválido falla el job y ese job es requerido por el
  resto del flujo.

Un cambio que afloje un gate (bajar el umbral, agregar `continue-on-error`,
sacar el contrato de `needs`) rompe estos tests antes de llegar al PR.
"""

from pathlib import Path

import re
import tomllib
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
CONTRIBUTING_PATH = REPO_ROOT / "CONTRIBUTING.md"
MAKEFILE_PATH = REPO_ROOT / "Makefile"
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
LOAD_SCRIPT_PATH = REPO_ROOT / "load" / "ingest.js"

COVERAGE_THRESHOLD = 70
PYLINT_THRESHOLD = "9.0"
# Imagen de k6 pinneada por tag (LT-2/LT-4): sin tag, la corrida deja de ser
# reproducible y el número de latencia no se puede comparar entre corridas.
K6_IMAGE = "grafana/k6"
K6_TAG_PATTERN = rf"{re.escape(K6_IMAGE)}:\d+\.\d+\.\d+"


def _workflow() -> dict:
    with open(WORKFLOW_PATH, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _jobs() -> dict:
    return _workflow()["jobs"]


def _job(job_id: str) -> dict:
    jobs = _jobs()
    assert job_id in jobs, f"el job `{job_id}` DEBE existir en {WORKFLOW_PATH.name}"
    return jobs[job_id]


def _needs(job_id: str) -> set[str]:
    """`needs` normalizado a conjunto (YAML permite string o lista)."""
    needs = _job(job_id).get("needs", [])
    return {needs} if isinstance(needs, str) else set(needs)


def _step(job_id: str, fragment: str) -> dict:
    """Primer step del job cuyo `run` contiene `fragment`."""
    for step in _job(job_id)["steps"]:
        if fragment in step.get("run", ""):
            return step
    raise AssertionError(
        f"el job `{job_id}` DEBE tener un step que corra algo con `{fragment}`"
    )


def _make_recipe(target: str) -> str:
    """Receta del target: líneas con tab después de `target:` hasta el próximo target."""
    lines = MAKEFILE_PATH.read_text(encoding="utf-8").splitlines()
    start = lines.index(f"{target}:")
    recipe = [lines[start]]
    for line in lines[start + 1:]:
        if not line.startswith("\t"):
            break
        recipe.append(line)
    return "\n".join(recipe)


def _pyproject_fail_under() -> str:
    """Valor de `fail_under` en `[tool.coverage.report]` (sin tomllib: 3.11+ lo tiene,
    pero el repo corre la suite en 3.11 y en 3.14; el parseo textual es estable)."""
    lines = PYPROJECT_PATH.read_text(encoding="utf-8").splitlines()
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            in_section = stripped == "[tool.coverage.report]"
            continue
        if in_section and stripped.startswith("fail_under"):
            return stripped.split("=", 1)[1].strip()
    raise AssertionError("pyproject.toml DEBE declarar fail_under en [tool.coverage.report]")


# -- S11: cobertura < 70 % bloquea ------------------------------------------


def test_s11_coverage_gate_is_explicit_and_equals_seventy():
    """El job de la suite DEBE pasar `--cov-fail-under=70` a pytest (S11).

    El umbral tiene que ser explícito en el comando del CI (no solo heredado de
    `pyproject.toml`) para que el gate sea visible en el log y no se pueda
    aflojar cambiando un archivo de configuración sin tocar el workflow.
    """
    step = _step("test", "--cov")
    run = step["run"]

    assert f"--cov-fail-under={COVERAGE_THRESHOLD}" in run, (
        f"el job `test` DEBE fallar con cobertura < {COVERAGE_THRESHOLD} % (S11)"
    )


def test_s11_cli_threshold_matches_pyproject_and_is_not_lowered():
    """El umbral del CI y el de `pyproject.toml` DEBEN ser el mismo: 70 (S11)."""
    step = _step("test", "--cov")
    cli_value = step["run"].split("--cov-fail-under=", 1)[1].split()[0]

    assert cli_value == str(COVERAGE_THRESHOLD)
    assert _pyproject_fail_under() == str(COVERAGE_THRESHOLD), (
        "el gate único de cobertura DEBE seguir en 70 % (no se baja el umbral)"
    )


def test_s11_coverage_step_and_job_are_blocking():
    """Ni el job de la suite ni su step de cobertura DEBEN tolerar el fallo (S11)."""
    job = _job("test")
    step = _step("test", "--cov")

    assert job.get("continue-on-error") is not True
    assert step.get("continue-on-error") is not True
    assert "if" not in step, "el step de cobertura DEBE correr siempre (sin `if`)"


# -- S12: lint con warnings/errores bloquea ----------------------------------


def test_s12_flake8_step_is_blocking():
    """flake8 DEBE correr sobre `src/` y `tests/` sin `continue-on-error` (S12).

    flake8 sale con código ≠ 0 ante cualquier hallazgo, así que la sola
    existencia del step bloqueante es el gate.
    """
    job = _job("lint")
    step = _step("lint", "flake8")

    assert "src/" in step["run"] and "tests/" in step["run"]
    assert job.get("continue-on-error") is not True
    assert step.get("continue-on-error") is not True


def test_s12_pylint_fails_on_warnings_and_errors():
    """pylint DEBE fallar ante cualquier warning o error y mantener score ≥ 9.0 (S12).

    `--fail-under` solo no alcanza: un único warning puede dejar el score por
    encima del umbral. `--fail-on=W,E` convierte cada warning o error en un
    fallo del job.
    """
    step = _step("lint", "pylint")
    run = step["run"]

    assert "--fail-on=W,E" in run, (
        "pylint DEBE fallar ante warnings y errores (S12), no solo por score"
    )
    assert f"--fail-under={PYLINT_THRESHOLD}" in run, (
        f"el score mínimo DEBE seguir en {PYLINT_THRESHOLD}"
    )
    assert step.get("continue-on-error") is not True


def test_s12_pylint_step_disables_no_messages():
    """El step de pylint NO DEBE llevar `--disable` (S12).

    El árbol pasa el gate con 0 warnings y 0 errores; una calibración desde el
    CI escondería una categoría entera del gate. Las calibraciones reales
    (siempre acotadas) viven en `pyproject.toml` y en los `# pylint: disable`
    de cada módulo, no en el workflow.
    """
    run = _step("lint", "pylint")["run"]

    assert "--disable" not in run, (
        "el gate del CI NO DEBE desactivar mensajes: calibralo en el módulo (S12)"
    )


def test_s12_local_lint_reproduces_the_blocking_gate():
    """`make lint` DEBE correr el mismo gate que el CI (S12/S14).

    Un target local más laxo deja el fallo escondido hasta el PR.
    """
    recipe = _make_recipe("lint")

    assert "flake8 src/ tests/" in recipe
    assert f"--fail-under={PYLINT_THRESHOLD}" in recipe
    assert "--fail-on=W,E" in recipe, (
        "`make lint` DEBE fallar ante warnings y errores, igual que el CI (S12)"
    )
    assert "--disable" not in recipe


def test_s12_pylint_has_no_global_suppressions():
    """El gate de pylint NO DEBE vivir de mensajes desactivados (S12).

    Con las versiones fijadas en `requirements/dev.lock` el árbol pasa con 0
    warnings y 0 errores; una categoría desactivada en
    `[tool.pylint."messages control"]` achicaría el gate en silencio.
    """
    with open(PYPROJECT_PATH, "rb") as handle:
        config = tomllib.load(handle)
    control = config.get("tool", {}).get("pylint", {}).get("messages control", {})

    assert not control.get("disable"), (
        f"pylint NO DEBE desactivar mensajes globalmente: {control.get('disable')}"
    )


# -- QF-1 (ISS-B-05): el job del frontend bloquea ---------------------------


def test_frontend_job_runs_the_full_gate_and_is_blocking():
    """El job `frontend` DEBE correr el gate completo de la SPA y no tragarse fallos (QF-1).

    S16 (npm ci desde el lock), S17 (presupuesto de bundle) y S19 (lint, tests y
    smoke E2E) son bloqueantes: un bundle de más de 1 MB o un test rojo tienen
    que romper el job, no avisar.
    """
    job = _job("frontend")
    runs = [step.get("run", "") for step in job["steps"]]

    for expected in (
        "npm ci",
        "npm run lint",
        "npm test",
        "npm run build",
        "npm run check-size",
        "npm run test:e2e",
    ):
        assert any(expected in run for run in runs), (
            f"el job `frontend` DEBE correr `{expected}` (QF-1)"
        )
    assert job.get("continue-on-error") is not True
    assert all(step.get("continue-on-error") is not True for step in job["steps"])


# -- S13: OpenAPI/contract inválido bloquea ---------------------------------


def test_s13_contract_job_runs_the_contract_tests():
    """El job de contrato DEBE correr `tests/test_contract.py` (schemathesis, S13)."""
    step = _step("contract", "pytest")

    assert "tests/test_contract.py" in step["run"]
    assert step.get("continue-on-error") is not True
    assert _job("contract").get("continue-on-error") is not True


def test_s13_contract_job_is_required_by_the_flow():
    """`Docker Build` DEBE esperar al job de contrato: un contrato roto frena el
    flujo completo y no queda como job informativo (S13)."""
    assert "contract" in _needs("docker"), (
        "el job `docker` DEBE depender de `contract` (S13: contrato bloqueante)"
    )


# -- Flujo documentado y ausencia de supresiones ----------------------------


def test_no_job_or_step_swallows_failures():
    """Ningún job ni step DEBE declarar `continue-on-error` (S11–S13).

    Un gate que puede fallar sin romper el check no es un gate.
    """
    offenders = []
    for job_id, job in _jobs().items():
        if job.get("continue-on-error") is True:
            offenders.append(f"job:{job_id}")
        for index, step in enumerate(job.get("steps", [])):
            if step.get("continue-on-error") is True:
                offenders.append(f"{job_id}/step[{index}]:{step.get('name', '')}")
    assert not offenders, f"steps con continue-on-error: {offenders}"


def test_gates_appear_in_the_documented_flow():
    """Los gates DEBEN estar en el flujo documentado del pipeline (S14).

    Orden intencional: lint → unit → suite con cobertura, con contract en
    paralelo del lint; `Docker Build` espera a lint, suite, licencias y
    contrato. Si un gate sale de `needs`, deja de bloquear el flujo.
    """
    assert _needs("unit") == {"lint"}
    assert _needs("test") == {"unit"}
    assert _needs("contract") == {"lint"}
    assert {"lint", "test", "license-scan", "contract"} <= _needs("docker")


def test_contributing_documents_the_three_blocking_gates():
    """`CONTRIBUTING.md` DEBE documentar qué bloquea cada gate y cómo
    reproducirlo localmente (S14)."""
    contributing = CONTRIBUTING_PATH.read_text(encoding="utf-8")

    for expected in (
        "--cov-fail-under=70",
        "--fail-on=W,E",
        "make test-contract",
        "make lint",
    ):
        assert expected in contributing, (
            f"CONTRIBUTING.md DEBE documentar `{expected}` (S14)"
        )


# -- S24–S27 (ISS-C-03): E2E bloqueante y carga k6 versionada ---------------


def test_e2e_and_load_jobs_are_wired():
    """El E2E corre en cada cambio y la carga es un escenario k6 versionado (S24–S27).

    LT-1: `e2e` depende de `lint`, levanta la stack del perfil `smoke` y corre
    `scripts/smoke.py`, sin `continue-on-error` (un flujo roto frena el PR).
    LT-4: `load` sólo corre por `workflow_dispatch` y sube el summary.
    LT-2/LT-3: el escenario vive en `load/ingest.js` y k6 va pinneado por tag en
    `make load`, así la corrida es reproducible.
    """
    e2e = _job("e2e")
    load = _job("load")

    # LT-1/S24: bloqueante, después del lint y corriendo el smoke de C.1.
    assert _needs("e2e") == {"lint"}, (
        "el job `e2e` DEBE depender sólo de `lint` (LT-1)"
    )
    assert e2e.get("continue-on-error") is not True
    assert all(step.get("continue-on-error") is not True for step in e2e["steps"])
    e2e_runs = "\n".join(step.get("run", "") for step in e2e["steps"])
    assert "scripts/smoke.py" in e2e_runs, (
        "el job `e2e` DEBE correr `scripts/smoke.py` (LT-1: un solo guion, no YAML paralelo)"
    )
    assert "docker compose --profile smoke up" in e2e_runs, (
        "el job `e2e` DEBE levantar la stack con `--profile smoke` (LT-1)"
    )

    # LT-4/D6: la carga es manual, corre el target versionado y sube el summary.
    assert load.get("continue-on-error") is not True
    assert all(step.get("continue-on-error") is not True for step in load["steps"])
    assert "workflow_dispatch" in str(load.get("if", "")), (
        "el job `load` DEBE correr sólo por `workflow_dispatch` (LT-4/D6)"
    )
    load_runs = "\n".join(step.get("run", "") for step in load["steps"])
    assert "make load" in load_runs, (
        "el job `load` DEBE correr `make load`, el mismo comando local (LT-4)"
    )
    artifacts = [
        step.get("with", {}).get("path", "")
        for step in load["steps"]
        if step.get("uses", "").startswith("actions/upload-artifact")
    ]
    assert any("k6-summary.json" in path for path in artifacts), (
        "el job `load` DEBE subir `reports/k6-summary.json` como artefacto (LT-4)"
    )

    # LT-2/LT-3: escenario versionado + imagen de k6 pinneada en `make load`.
    assert LOAD_SCRIPT_PATH.is_file(), (
        "el escenario DEBE estar versionado en `load/ingest.js` (LT-2)"
    )
    recipe = _make_recipe("load")
    makefile = MAKEFILE_PATH.read_text(encoding="utf-8")
    assert re.search(K6_TAG_PATTERN, makefile), (
        f"el Makefile DEBE fijar `{K6_IMAGE}` con un tag pinneado (LT-2/LT-4)"
    )
    assert "$(K6_IMAGE)" in recipe, (
        "`make load` DEBE correr la imagen pinneada, no `latest` (LT-4)"
    )
    assert "k6-summary.json" in recipe, (
        "`make load` DEBE exportar el summary a `reports/k6-summary.json` (LT-4)"
    )


# -- ISS-C-05: JWT_SECRET obligatorio en el compose de despliegue --------------

# Sin default público: un `docker compose up` sin la variable no debe firmar
# tokens con un secreto publicado en el repo. Los consumidores del compose
# (CI, Makefile) declaran su propio valor.
JWT_SECRET_REQUIRED = re.compile(r"JWT_SECRET=\$\{JWT_SECRET:\?[^}]+\}")
COMPOSE_COMMAND = re.compile(r"docker compose|make (smoke|e2e-ci|load|up|setup)\b")
MIN_JWT_SECRET_LENGTH = 32  # `Settings._validate_jwt_secret_length` (AUTH-6)


def test_compose_requires_jwt_secret_and_has_no_public_default():
    """`docker-compose.yml` DEBE fallar sin `JWT_SECRET` (`:?`), no caer a un
    valor por defecto publicado en el repo (ISS-C-05)."""
    compose = COMPOSE_PATH.read_text(encoding="utf-8")
    assert JWT_SECRET_REQUIRED.search(compose), (
        "`JWT_SECRET` DEBE ser obligatorio en el compose (`${JWT_SECRET:?...}`)"
    )
    assert "JWT_SECRET:-" not in compose, (
        "`JWT_SECRET` NO DEBE tener default en el compose (`:-`)"
    )
    assert "dev-only-jwt-secret" not in compose, (
        "el compose NO DEBE embeber el secreto de dev publicado en el repo"
    )


def test_ci_jobs_that_run_compose_provide_their_own_jwt_secret():
    """Todo job que corre `docker compose` (directo o vía `make`) DEBE declarar
    un `JWT_SECRET` propio a nivel de job: sin él el compose aborta (ISS-C-05)."""
    offenders = []
    for job_id, job in _jobs().items():
        runs = "\n".join(step.get("run", "") for step in job.get("steps", []))
        if not COMPOSE_COMMAND.search(runs):
            continue
        secret = str(job.get("env", {}).get("JWT_SECRET", ""))
        if len(secret) < MIN_JWT_SECRET_LENGTH:
            offenders.append(job_id)
    assert not offenders, (
        f"los jobs {offenders} corren docker compose sin `env.JWT_SECRET` "
        f"(>= {MIN_JWT_SECRET_LENGTH} chars) a nivel de job"
    )


def test_make_smoke_targets_provide_a_jwt_secret_for_the_compose():
    """`make smoke` y `make e2e-ci` levantan el compose: DEBEN pasar
    `JWT_SECRET` (el del entorno o uno propio del smoke) (ISS-C-05)."""
    makefile = MAKEFILE_PATH.read_text(encoding="utf-8")
    smoke_env = makefile.split("SMOKE_ENV = ", 1)[1].split("\n\n", 1)[0]
    assert "JWT_SECRET=" in smoke_env, (
        "`SMOKE_ENV` DEBE definir `JWT_SECRET` para los targets smoke y e2e-ci"
    )
    for target in ("smoke", "e2e-ci"):
        assert "$(SMOKE_ENV)" in _make_recipe(target), (
            f"`make {target}` DEBE correr con `$(SMOKE_ENV)`"
        )
