from typing import List, Union
import libcst as cst
from libcst._flatten_sentinel import FlattenSentinel
from libcst._nodes.statement import BaseStatement, If
from libcst._removal_sentinel import RemovalSentinel
from libcst import CSTNodeT, CSTVisitor
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
    
class LineRemovalByASTManipulaition(cst.CSTTransformer):
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

        # Added cst.IndentedBlock to remove RemovalSentinel error while visiting IndentedBlock. Earlier, node's parent does not allow it to be removed.
        # https://libcst.readthedocs.io/_/downloads/en/stable/pdf/

        if isinstance(node, cst.IndentedBlock) or code_location.start.line in self.lines_to_keep:
            return True
        
    def on_leave(self, original_node: CSTNodeT, updated_node: CSTNodeT) -> Union[CSTNodeT, cst.RemovalSentinel]:
        code_location = self.get_metadata(PositionProvider, original_node)
        # Added cst.IndentedBlock to remove RemovalSentinel error while visiting IndentedBlock. Earlier, node's parent does not allow it to be removed.
        if isinstance(original_node, cst.IndentedBlock) or code_location.start.line in self.lines_to_keep:
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

def get_slicing_values(source: str) -> List:
    syntax_tree = cst.parse_module(source)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    slicing_values = FetchSlicingValues()
    something = wrapper.visit(slicing_values)
    return slicing_values.vals

class FetchSlicingValues(CSTVisitor):
    '''Logic for fetching slicing values  '''
    def __init__(self):

        super().__init__()
        self.vals = {
            "slicing_criteria_line": -1,
            "lines_to_keep": [],
            "dependent_variables": []
        }


    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider,
    )

    # Used visit_[Nodename] to visit the node similarly for leave_. Mentioned in documentation.

    def leave_Comment(self, node: cst.Comment):
        if node.value == "# slicing criterion":
            self.vals["slicing_criteria_line"] = self.get_metadata(PositionProvider, node).start.line
            self.vals["lines_to_keep"] += [self.get_metadata(PositionProvider, node).start.line]

            whitespace = self.get_metadata(ParentNodeProvider, node)
            currentVariable = self.get_metadata(ParentNodeProvider, whitespace).body[0]

            if isinstance(currentVariable, cst.Assign):
                if isinstance(currentVariable.targets[0], cst.AssignTarget):
                    if isinstance(currentVariable.targets[0].target, cst.Subscript):
                        self.vals["dependent_variables"] += [currentVariable.targets[0].target.value.value]
                    elif isinstance(currentVariable.value, cst.Name):
                        self.vals["dependent_variables"] += [currentVariable.value.value]
                        self.vals["dependent_variables"] += [currentVariable.targets[0].target.value]
                    else:
                        self.vals["dependent_variables"] += [currentVariable.targets[0].target.value]
                elif isinstance(currentVariable, cst.BinaryOperation):
                    self.vals["dependent_variables"] += map(lambda i: i.value, m.findall(isinstance(currentVariable, cst.Name)))
            elif isinstance(currentVariable, cst.Call):
                if isinstance(currentVariable.value, cst.Call(func=cst.Attribute())):
                    self.vals["dependent_variables"] += [currentVariable.value.func.value.value]
                elif isinstance(currentVariable.value, cst.Call(func=cst.Name())):
                    self.vals["dependent_variables"] += map(lambda i: i.value.value, currentVariable.value.args)
            elif isinstance(currentVariable, cst.Return):
                if isinstance(currentVariable.value, cst.BinaryOperation):
                    self.vals["dependent_variables"] += map(lambda i: i.value, m.findall(isinstance(currentVariable, cst.Name)))
                elif isinstance(currentVariable.value, cst.Name):
                    self.vals["dependent_variables"] += [currentVariable.value.value]
                elif isinstance(currentVariable.value, cst.Attribute):
                    self.vals["dependent_variables"] += [currentVariable.value.value.value]
                    self.vals["dependent_variables"] += [currentVariable.value.value.value + "." + currentVariable.value.attr.value]


def get_functionDef_value(source: str) -> List:
    syntax_tree = cst.parse_module(source)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    slicing_values = FunctionDefinitionVisitor()
    something = wrapper.visit(slicing_values)
    return slicing_values.return_val

class FunctionDefinitionVisitor(CSTVisitor):
    """Function Definition Visitor Class"""
    def __init__(self):
        self.return_val = []

    METADATA_DEPENDENCIES = (
        PositionProvider,
    )

    def visit_FunctionDef(self, node: cst.FunctionDef):
        if node.name.value == "slice_me":
            self.return_val += [self.get_metadata(PositionProvider, node).start.line]
        else:
            for i in range(self.get_metadata(PositionProvider, node).start.line, self.get_metadata(PositionProvider, node).end.line + 1):
                self.return_val += [i]

def get_functionCall_value(source: str) -> List:
    syntax_tree = cst.parse_module(source)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    slicing_values = FunctionCallVisitor()
    something = wrapper.visit(slicing_values)
    return slicing_values.return_val

class FunctionCallVisitor(CSTVisitor):
    """Function Call Visitor Class"""
    def __init__(self):
        self.return_val = []

    METADATA_DEPENDENCIES = (
        PositionProvider,
    )

    def visit_Call(self, node: cst.Call):
        if node.func.value == "slice_me":
            self.return_val += [self.get_metadata(PositionProvider, node).start.line]

def get_classDef_value(source: str) -> List:
    syntax_tree = cst.parse_module(source)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    slicing_values = ClassDefinitionVisitor()
    something = wrapper.visit(slicing_values)
    return slicing_values.return_val

class ClassDefinitionVisitor(CSTVisitor):
    """Function Call Visitor Class"""
    def __init__(self):
        self.return_val = []

    METADATA_DEPENDENCIES = (
        PositionProvider,
    )

    def visit_ClassDef(self, node: cst.ClassDef):
        for i in range(self.get_metadata(PositionProvider, node).start.line, self.get_metadata(PositionProvider, node).end.line + 1):
            self.return_val += [i]