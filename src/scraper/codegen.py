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

                        zod_type = handle_annotation(node.annotation)

                        a_zod_type.append(f"{var_name}: {zod_type}")

                a_zod_type.append("});")

                codegen.append("\n".join(a_zod_type))

        print(codegen)


def handle_annotation(expr: ast.expr) -> str:
    match expr:
        case ast.Name(id):
            return get_zod_string_from_type(id)
        case ast.BinOp():
            print(expr)
            return ""
        case ast.Subscript():
            return ""
        case _:
            raise Exception(f"Unhandled expr: {expr}")


def get_zod_string_from_type(type: str) -> str:
    match type:
        case "float" | "int":
            return "z.number(),"
        case "str":
            return "z.string(),"
        case _:
            raise Exception(f"Unhandled type {type}")


def search_alias_type_definition(type: str) -> str:
    pass


if __name__ == "__main__":
    main()
