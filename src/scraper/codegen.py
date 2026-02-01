import ast
import json
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

                for body_node in node.body:
                    if isinstance(body_node, ast.AnnAssign):
                        assert isinstance(body_node.target, ast.Name)
                        var_name = body_node.target.id

                        zod_type = handle_type_annotation(body_node.annotation)

                        a_zod_type.append(f"{to_camel(var_name)}: {zod_type},")

                a_zod_type.append("});")
                a_zod_type.append(f"type {node.name} = z.infer<{node.name}>;")

                codegen.append("\n".join(a_zod_type))

        print("\n".join(codegen))


def handle_type_annotation(expr: ast.expr) -> str:
    match expr:
        case ast.BinOp():
            return handle_binop(expr)
        case ast.Subscript():
            return handle_subscript(expr)
        case ast.Name(id):
            return get_zod_string_from_type(id)
        case ast.Tuple(elts):
            return ", ".join(handle_type_annotation(e) for e in elts)
        case ast.Constant():
            return handle_constant(expr)
        case _:
            raise Exception(f"Unhandled expr: {expr}")


def handle_binop(binop: ast.BinOp, in_another_binop: bool = False) -> str:
    """
    Returns the zod equivalent of BinOp ast
    """
    match binop.left:
        case ast.BinOp():
            left = handle_binop(binop.left, True)
        case _:
            left = handle_type_annotation(binop.left)

    right = handle_type_annotation(binop.right)

    string = f"{left}, {right}"

    if in_another_binop:
        return string

    return f"z.union([{string}])"


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
        case "Literal":
            assert isinstance(args, ast.Tuple)
            return f"z.literal([{', '.join(handle_constant(e) for e in args.elts if isinstance(e, ast.Constant))}])"
        case _:
            raise Exception(f"Unhandled name id {name.id}")


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
            return json.dumps(constant.value)


def search_alias_type_definition(type: str) -> str:
    return ""


if __name__ == "__main__":
    main()
