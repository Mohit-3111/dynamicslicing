from typing import List, Union
import libcst as cst
from libcst._flatten_sentinel import FlattenSentinel
from libcst._nodes.statement import BaseStatement, If
from libcst._removal_sentinel import RemovalSentinel
from libcst import CSTNodeT
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
)
import libcst.matchers as m


class OddIfNegation(m.MatcherDecoratableTransformer):
    """
    Negate the test of every if statement on an odd line.
    """
    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        PositionProvider,
    )

    def leave_If(self, original_node: If, updated_node: If) -> BaseStatement | FlattenSentinel[BaseStatement] | RemovalSentinel:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line % 2 == 0:
            return updated_node
        negated_test = cst.UnaryOperation(
            operator=cst.Not(),
            expression=updated_node.test,
        )
        return updated_node.with_changes(
            test=negated_test,
        )
    
class LineRemovalByASTManipulaition(m.MatcherDecoratableTransformer):
    """
    Excludes specific lines of code based on provided criteria.
    """

    def __init__(self, lines_to_keep: List[int]):
        super().__init__()
        self.lines_to_keep = lines_to_keep
    
    METADATA_DEPENDENCIES = (
        PositionProvider,
    )

    def on_visit(self, node: cst.CSTNode):
        code_location = self.get_metadata(PositionProvider, node)
        if code_location.start.line in self.lines_to_keep:
            return True
        
    def on_leave(self, original_node: CSTNodeT, updated_node: CSTNodeT) -> Union[CSTNodeT, cst.RemovalSentinel]:
        code_location = self.get_metadata(PositionProvider, original_node)
        if code_location.start.line in self.lines_to_keep:
            return updated_node
        
        return cst.RemoveFromParent()
    


def negate_odd_ifs(code: str) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = OddIfNegation()
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code

def remove_lines(code: str, lines_to_keep: List[int]) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = LineRemovalByASTManipulaition(lines_to_keep)
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code
