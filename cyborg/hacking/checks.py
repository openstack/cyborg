# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import ast
import re


NAMED_PLACEHOLDER_RE = re.compile(r"%\([^)]+\)[a-zA-Z%]")

LOG_METHODS = frozenset(
    (
        "debug",
        "info",
        "warning",
        "error",
        "critical",
        "exception",
        "log",
    )
)


def _flatten_str_chain(node):
    """Extract a string from an AST node or Add-concatenation chain.

    Returns the string value if the node is a string constant or a
    chain of string constants joined with ``+``.  Returns ``None``
    for anything else (variables, f-strings, etc.).
    """
    parts = []

    def _visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            parts.append(node.value)
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return _visit(node.left) and _visit(node.right)
        return False

    if not _visit(node):
        return None
    return "".join(parts)


class CheckSetLiteralInLogging(ast.NodeVisitor):
    """C300: set literal passed where dict expected in logging call.

    Detects ``LOG.info("%(key)s", {"key", val})`` where a set literal
    (comma) was used instead of a dict literal (colon).  This causes
    ``TypeError: format requires a mapping`` at runtime.
    """

    name = "check_set_literal_in_logging"
    version = "0.1"

    CHECK_DESC = (
        "C300 set literal passed where dict expected for %-format logging"
    )

    def __init__(self, tree, filename):
        self._tree = tree
        self._errors = []

    def run(self):
        self.visit(self._tree)
        return self._errors

    def add_error(self, node, message=None):
        message = message or self.CHECK_DESC
        self._errors.append(
            (node.lineno, node.col_offset, message, type(self))
        )

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in LOG_METHODS
        ):
            # .log(level, msg, *args) vs .info(msg, *args)
            if node.func.attr == "log":
                fmt_idx, dict_idx = 1, 2
            else:
                fmt_idx, dict_idx = 0, 1

            if len(node.args) >= dict_idx + 1 and isinstance(
                node.args[dict_idx], ast.Set
            ):
                fmt_str = _flatten_str_chain(node.args[fmt_idx])
                if fmt_str and NAMED_PLACEHOLDER_RE.search(fmt_str):
                    self.add_error(node.args[dict_idx])

        self.generic_visit(node)
