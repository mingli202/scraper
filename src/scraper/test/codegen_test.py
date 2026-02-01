import ast
import pytest

from scraper.codegen import (
    get_zod_string_from_type,
    handle_constant,
    handle_type_annotation,
)


@pytest.mark.parametrize(
    "input,expected",
    [
        ("None", "z.null()"),
    ],
)
def test_handle_constant(input: str, expected: str):
    expr = ast.parse(input, mode="eval")
    constant = expr.body

    assert isinstance(constant, ast.Constant)

    res = handle_constant(constant)

    assert res == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        ("str", "z.string()"),
        ("int", "z.number()"),
        ("float", "z.number()"),
    ],
)
def test_get_zod_string_from_type(input: str, expected: str):
    assert get_zod_string_from_type(input) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        ("an_int: int", "z.number()"),
        ("a_float: float", "z.number()"),
        ("a_string: str", "z.string()"),
        ("a_dict: dict[int, str]", "z.record(z.number(), z.string())"),
        ("a_list: list[str]", "z.array(z.string())"),
        ("a_tuple: tuple[int]", "z.tuple([z.number()])"),
        ("an_union: str | None", "z.union(z.number(), z.null())"),
        (
            'a_literal_union1: Literal["found", "foundn\'t"]',
            'z.literal(["found", "found\'nt"])',
        ),
        ("a_literal_union2: Literal[1, 2, 3]", "z.literal([1, 2, 3])"),
        (
            "a_tuple: tuple[int, str, int]",
            "z.tuple([z.number(), z.string(), z.number()])",
        ),
        (
            "a_mix_of_types1: dict[int, list[str]]",
            "z.record(z.number(), z.array(z.string()))",
        ),
        (
            "a_mix_of_types2: list[dict[int, str]]",
            "z.array(z.record(z.number(), z.string()))",
        ),
        (
            "a_mix_of_types3: tuple[list[str], dict[str, tuple[int, int]], str]",
            "z.tuple([z.array(z.string()), z.record(z.string(), z.tuple([z.number(), z.number()])), z.string()])",
        ),
        (
            "a_mix_of_types4: list[str] | int | None",
            "z.union([z.array(z.number()), z.number(), z.null()])",
        ),
        ("a_value: int = 5", "z.number()"),
        ("a_reference_to_another_type: list[MyType]", "z.array(MyType)"),
        pytest.param(
            "a_fail: int = 5", "const a_fail: number = 5", marks=pytest.mark.xfail
        ),
    ],
)
def test_handle_type_annotation(input: str, expected: str):
    body = ast.parse(input).body
    assign = body[0]

    assert isinstance(assign, ast.AnnAssign)

    target = assign.target
    assert isinstance(target, ast.Name)
    var_name = target.id

    annotation = assign.annotation

    print(var_name)
    assert handle_type_annotation(annotation) == expected


if __name__ == "__main__":
    exit(pytest.main(["--no-header", "-s", "-vvv", __file__]))
