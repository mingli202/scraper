import ast
from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic.alias_generators import to_camel

codegen_dir = os.environ.get("CODEGEN_DIR")
did_load_env = load_dotenv()

if codegen_dir is None and (
    not load_dotenv() or (codegen_dir := os.environ.get("CODEGEN_DIR") is None)
):
    print("Please set the environment variable CODEGEN_DIR")
    exit(1)

cur_dir = Path(__file__).resolve().parent.resolve()
models_filepath = cur_dir / "models.py"


def main():
    with open(models_filepath, "r") as file:
        tree = ast.parse(file.read())

        codegen: list[str] = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef) and any(
                isinstance(exp, ast.Name) and "ConfiguredBaseModel" == exp.id
                for exp in node.bases
            ):
                a_zod_type: list[str] = [f"const {node.name} = v.object({{"]

                for node in node.body:
                    if isinstance(node, ast.AnnAssign):
                        assert isinstance(node.target, ast.Name)
                        var_name = node.target.id

                        zod_type = handle_type_annotation(node.annotation)

                        a_zod_type.append(f"{var_name}: {zod_type},")

                a_zod_type.append("});")

                codegen.append("\n".join(a_zod_type))

        print(codegen)


def handle_type_annotation(expr: ast.expr) -> str:
    match expr:
        case ast.BinOp():
            return ""
        case ast.Subscript():
            return handle_subscript(expr)
        case ast.Name(id):
            return get_zod_string_from_type(id)
        case ast.Tuple(elts):
            return ", ".join(handle_type_annotation(e) for e in elts)
        case _:
            raise Exception(f"Unhandled expr: {expr}")


def handle_subscript(subscript: ast.Subscript) -> str:
    """
    Returns the zod equivalent of Subscript ast

    Examples:
    - handle_subscript(parse_ast("dict[int, list[str]]")) -> z.record(z.number(), z.array(z.string()))
    """
    assert isinstance(subscript.value, ast.Name)

    name = subscript.value
    assert isinstance(name, ast.Name)

    args = subscript.slice

    match name.id:
        case "dict":
            assert isinstance(args, ast.Tuple)
            return f"z.record({handle_type_annotation(args.elts[0])}, {handle_type_annotation(args.elts[1])})"
        case "list":
            return f"z.array({handle_type_annotation(args)})"
        case "tuple":
            return f"z.tuple([{handle_type_annotation(args)}])"
        case _:
            raise Exception(f"Unhandled name id {id}")


def get_zod_string_from_type(type: str) -> str:
    """
    Returns zod equivalent for primitives
    """
    match type:
        case "float" | "int":
            return "z.number()"
        case "str":
            return "z.string()"
        case _:
            return type


def handle_constant(constant: ast.Constant) -> str:
    """
    Returns the zod equivalent for the given python constant
    """
    match constant.value:
        case None:
            return "z.null()"
        case _:
            raise Exception(f"Unhandled constant {constant}")


def search_alias_type_definition(type: str) -> str:
    return ""


if __name__ == "__main__":
    main()
