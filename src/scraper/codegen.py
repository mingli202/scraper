import ast
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import final

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


@final
class UnhandledExpr(Exception):
    def __init__(self, expr: ast.expr):
        super().__init__(f"Unhandled expr: {expr}")


@final
class UnhandledNameId(Exception):
    def __init__(self, id: str):
        super().__init__(f"Unhandled name id {id}")


class Validator(BaseModel):
    model_config = ConfigDict(frozen=True)
    importLine: str
    array: str
    tuple: str
    object: str
    enum: Callable[[str, list[tuple[str, str]]], str]
    union: Callable[[str], str]
    record: str
    literal: str
    infer: Callable[[str], str]
    number: str
    string: str
    null: str


zod = Validator(
    importLine='import z from "zod";',
    array="z.array",
    tuple="z.tuple",
    object="z.object",
    enum=lambda name, variants: f"z.enum({name}Enum)",
    union=lambda s: f"z.union([{s}])",
    record="z.record",
    literal="z.literal",
    infer=lambda fnName: f"z.infer<typeof {fnName}>;",
    number="z.number()",
    string="z.string()",
    null="z.null()",
)

convex = Validator(
    importLine='import { v } from "convex/values";',
    array="v.array",
    tuple="v.tuple",
    object="v.object",
    enum=lambda name, variants: (
        f"v.union({','.join(f'v.literal("{var[1]}")' for var in variants)})"
    ),
    union=lambda s: f"v.union({s})",
    record="v.record",
    literal="v.literal",
    infer=lambda fnName: f"typeof {fnName}.type",
    number="v.number()",
    string="v.string()",
    null="v.null()",
)


def main():
    _ = load_dotenv()
    codegen_dir = os.environ.get("CODEGEN_DIR")

    if codegen_dir is None:
        print("Please set the environment variable CODEGEN_DIR")
        sys.exit(1)

    zod_file = Path(codegen_dir).resolve() / "src" / "types" / "generated.ts"
    convex_file = Path(codegen_dir).resolve() / "convex" / "types.generated.ts"

    codegen(zod, zod_file)
    codegen(convex, convex_file)


def codegen(v: Validator, codegen_file: Path) -> None:
    cur_dir = Path(__file__).resolve().parent.resolve()
    models_filepath = cur_dir / "models.py"

    with open(models_filepath, "r") as file:
        tree = ast.parse(file.read())

        codegen: list[str] = [
            "// DO NOT EDIT: THIS FILE WAS GENERATED VIA A SCRIPT",
            v.importLine,
        ]

        for node in tree.body:
            if isinstance(node, ast.ClassDef) and any(
                isinstance(exp, ast.Name) and "ConfiguredBaseModel" == exp.id
                for exp in node.bases
            ):
                a_zod_type: list[str] = [f"export const {node.name} = {v.object}({{"]

                for body_node in node.body:
                    if isinstance(body_node, ast.AnnAssign):
                        assert isinstance(body_node.target, ast.Name)
                        var_name = body_node.target.id

                        zod_type = handle_type_annotation(body_node.annotation, v)

                        a_zod_type.append(f"{to_camel(var_name)}: {zod_type},")

                a_zod_type.append("});")
                a_zod_type.append(f"export type {node.name} = {v.infer(node.name)}")

                codegen.append("\n".join(a_zod_type))

            if isinstance(node, ast.ClassDef) and any(
                isinstance(exp, ast.Name) and "Enum" == exp.id for exp in node.bases
            ):
                enum_variants: list[tuple[str, str]] = []

                for body_node in node.body:
                    if isinstance(body_node, ast.Assign):
                        variant_name = next(
                            t.id for t in body_node.targets if isinstance(t, ast.Name)
                        )

                        value = body_node.value
                        assert isinstance(value, ast.Constant)

                        enum_variants.append((variant_name, str(value.value)))

                variants_object = (
                    f"export const {node.name}Enum = {{"
                    + ",".join(f"{v[0]}: {json.dumps(v[1])}" for v in enum_variants)
                    + "} as const;"
                )

                enum_str = v.enum(node.name, enum_variants)
                zod_enum = f"export const {node.name} = {enum_str}"

                codegen.append(variants_object)
                codegen.append(zod_enum)
                codegen.append(f"export type {node.name} = {v.infer(node.name)}")

            if isinstance(node, ast.TypeAlias):
                name = node.name.id
                zod_type = handle_type_annotation(node.value, v)

                codegen.append(f"export const {name} = {zod_type};")
                codegen.append(f"export type {name} = {v.infer(name)}")

        all_types = "\n\n".join(codegen)

    with open(codegen_file, "w") as file:
        _ = file.write(all_types)

    _ = subprocess.run(["biome", "format", "--write", codegen_file], check=True)


def handle_type_annotation(expr: ast.expr, v: Validator) -> str:
    match expr:
        case ast.BinOp():
            return handle_binop(expr, v)
        case ast.Subscript():
            return handle_subscript(expr, v)
        case ast.Name(id):
            return get_zod_string_from_type(id, v)
        case ast.Tuple(elts):
            return ", ".join(handle_type_annotation(e, v) for e in elts)
        case ast.Constant():
            return handle_constant(expr, v)
        case _:
            raise UnhandledExpr(expr)


def handle_binop(binop: ast.BinOp, v: Validator, in_another_binop: bool = False) -> str:
    """
    Returns the zod or convex/values equivalent of BinOp ast
    """
    match binop.left:
        case ast.BinOp():
            left = handle_binop(binop.left, v, True)
        case _:
            left = handle_type_annotation(binop.left, v)

    right = handle_type_annotation(binop.right, v)

    string = f"{left}, {right}"

    if in_another_binop:
        return string

    return v.union(string)


def handle_subscript(subscript: ast.Subscript, v: Validator) -> str:
    """
    Returns the zod or convex/values equivalent of Subscript ast

    Examples:
    - handle_subscript(parse_ast("dict[int, list[str]]")) -> z.record(z.number(), z.array(z.string()))

    - handle_subscript(parse_ast("dict[int, list[str]]")) -> v.record(v.number(), v.array(v.string()))
    """
    assert isinstance(subscript.value, ast.Name)

    name = subscript.value
    assert isinstance(name, ast.Name)

    args = subscript.slice

    match name.id:
        case "dict":
            assert isinstance(args, ast.Tuple)
            return f"{v.record}({handle_type_annotation(args.elts[0], v)}, {handle_type_annotation(args.elts[1], v)})"
        case "list":
            return f"{v.array}({handle_type_annotation(args, v)})"
        case "tuple":
            return f"{v.tuple}([{handle_type_annotation(args, v)}])"
        case "Literal":
            assert isinstance(args, ast.Tuple)
            return f"{v.literal}([{', '.join(handle_constant(e, v) for e in args.elts if isinstance(e, ast.Constant))}])"
        case _:
            raise UnhandledNameId(name.id)


def get_zod_string_from_type(type: str, v: Validator) -> str:
    """
    Returns zod equivalent for primitives
    """
    match type:
        case "float" | "int":
            return v.number
        case "str":
            return v.string
        case _:
            return type


def handle_constant(constant: ast.Constant, v: Validator) -> str:
    """
    Returns the zod equivalent for the given python constant
    """
    match constant.value:
        case None:
            return v.null
        case _:
            return json.dumps(constant.value)


if __name__ == "__main__":
    main()
