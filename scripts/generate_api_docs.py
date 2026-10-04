from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = [ROOT / "backend", ROOT / "simulator", ROOT / "scripts"]
OUTPUT = ROOT / "docs" / "referencia_api.md"


def clean_docstring(value: str | None) -> str:
    if not value:
        return "Sin descripción en el código."
    return " ".join(line.strip() for line in value.splitlines() if line.strip())


def format_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = [arg.arg for arg in node.args.args if arg.arg != "self"]

    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)

    args.extend(arg.arg for arg in node.args.kwonlyargs)

    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)

    return ", ".join(args) if args else "Sin parámetros"


def public_assignments(nodes: list[ast.stmt]) -> list[str]:
    names: list[str] = []

    for node in nodes:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.append(target.id)

        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                names.append(target.id)

    return sorted(set(names))


def relative_module(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def render_module(path: Path) -> list[str]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (UnicodeDecodeError, SyntaxError) as exc:
        return [
            f"## {relative_module(path)}",
            "",
            f"No fue posible analizar este módulo automáticamente: `{exc}`.",
            "",
        ]

    lines = [
        f"## {relative_module(path)}",
        "",
        clean_docstring(ast.get_docstring(tree)),
        "",
    ]

    variables = public_assignments(tree.body)
    if variables:
        lines.extend(["### Variables / constantes públicas", ""])
        lines.extend(f"- `{name}`" for name in variables)
        lines.append("")

    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

    functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    for cls in classes:
        lines.extend(
            [
                f"### Clase `{cls.name}`",
                "",
                clean_docstring(ast.get_docstring(cls)),
                "",
            ]
        )

        properties = public_assignments(cls.body)
        if properties:
            lines.extend(["**Propiedades / atributos declarados**", ""])
            lines.extend(f"- `{name}`" for name in properties)
            lines.append("")

        methods = [
            node
            for node in cls.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        ]

        if methods:
            lines.extend(["**Métodos públicos**", ""])

            for method in methods:
                prefix = "async " if isinstance(method, ast.AsyncFunctionDef) else ""
                lines.append(
                    f"- `{prefix}{method.name}({format_args(method)})`: "
                    f"{clean_docstring(ast.get_docstring(method))}"
                )

            lines.append("")

    if functions:
        lines.extend(["### Funciones", ""])

        for func in functions:
            if func.name.startswith("_"):
                continue

            prefix = "async " if isinstance(func, ast.AsyncFunctionDef) else ""

            lines.append(
                f"- `{prefix}{func.name}({format_args(func)})`: "
                f"{clean_docstring(ast.get_docstring(func))}"
            )

        lines.append("")

    return lines


def main() -> None:
    python_files: list[Path] = []

    for directory in SOURCE_DIRS:
        if directory.exists():
            python_files.extend(
                path
                for path in directory.rglob("*.py")
                if "__pycache__" not in path.parts
            )

    lines = [
        "# Referencia técnica automática",
        "",
        "Esta página se genera automáticamente desde el código fuente "
        "cada vez que GitHub Actions ejecuta el workflow de documentación.",
        "",
        f"**Módulos analizados:** {len(python_files)}",
        "",
    ]

    for path in sorted(python_files):
        lines.extend(render_module(path))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Documentación generada en: {OUTPUT}")


if __name__ == "__main__":
    main()
