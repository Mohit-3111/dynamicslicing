import os
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, List
from dynapyt.utils.nodeLocator import get_node_by_location

from dynamicslicing import utils
import libcst as cst
import libcst.matchers as m

class Slice(BaseAnalysis):
    def __init__(self, source_path, output_dir=None):
        super().__init__()
        self.source_path = source_path

        self.vals = {
            "slicing_criteria_line": -1,
            "lines_to_keep": [],
            "class_lines": [],
            "dependent_variables": []
        }

    def begin_execution(self) -> None:
        file = os.path.splitext(self.source_path)[0] + '.py.orig'
        with open(file, 'r') as f:
            source = f.read()
        self.source = source
        self.slicing_parameters()

    def slicing_parameters(self) -> None:
        slicing_values = utils.get_slicing_values(self.source)
        class_lines = utils.get_classDef_value(self.source)
        function_call_line = utils.get_functionCall_value(self.source)
        function_def_line = utils.get_functionDef_value(self.source)
        self.vals["lines_to_keep"] = class_lines + function_call_line + function_def_line + [slicing_values["slicing_criteria_line"]]
        self.vals["slicing_criteria_line"] = slicing_values["slicing_criteria_line"]
        self.vals["dependent_variables"] = slicing_values["dependent_variables"]
        self.vals["class_lines"] = class_lines
        self.extra_variables = dict()
        self.read_write = dict()

    def end_execution(self) -> None:
        sliced_code = utils.remove_lines(self.source, self.vals["lines_to_keep"])
        output_path = os.path.dirname(self.source_path) + '/sliced.py'
        with open(output_path, 'w') as f:
            f.write(sliced_code)

    def post_call(self, dyn_ast: str, iid: int, result: Any, call: Callable, pos_args: Tuple, kw_args: Dict) -> Any:
        iid_location = self.iid_to_location(dyn_ast, iid)

        if self.should_process(iid_location.start_line):
            located_node = get_node_by_location(self._get_ast(dyn_ast)[0], iid_location)
            
            def _get_arg_value(arg):
                if isinstance(arg.value, cst.Name):
                    return arg.value.value
                elif isinstance(arg.value, cst.Attribute):
                    return f"{arg.value.value.value}.{arg.value.attr.value}"
                return None
            
            if iid_location.start_line not in self.read_write:
                if isinstance(located_node.func, cst.Attribute):
                    entry = {
                        "write": located_node.func.value.value,
                        "read": []
                    }
                    for arg in located_node.args:
                        if val := _get_arg_value(arg):
                            entry["read"] += [val]
                        self.read_write[iid_location.start_line] = entry

            else:
                if isinstance(located_node.func, cst.Attribute) and not self.read_write[iid_location.start_line]["write"]:
                    self.read_write[iid_location.start_line]["write"] = located_node.func.value.value
                elif isinstance(located_node.func, cst.Name):
                    if located_node.func.value == "print":
                        self.vals["lines_to_keep"] += [iid_location.start_line]

                if list(filter(lambda x: x in self.read_write[iid_location.start_line]["read"], self.vals["dependent_variables"])):
                    self.vals["lines_to_keep"] += [iid_location.start_line]
                    if located_node.func.value != "print":    
                        self.vals["dependent_variables"] += [located_node.func.value.value]
                self.read_write[iid_location.start_line]["read"] += [_get_arg_value(arg) for arg in located_node.args if _get_arg_value(arg) is not None]

    def write(self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any) -> Any:
        iid_location = self.iid_to_location(dyn_ast, iid)

        if self.should_process(iid_location.start_line):
            located_node = get_node_by_location(self._get_ast(dyn_ast)[0], iid_location)

            def _get_target_value():
                if isinstance(located_node, cst.AugAssign):
                    return located_node.target.value
                if isinstance(located_node.targets[0].target, cst.Attribute):
                    return f"{located_node.targets[0].target.value.value}.{located_node.targets[0].target.attr.value}"
                return located_node.targets[0].target.value.value if isinstance(
                    located_node.targets[0].target, cst.Subscript
                ) else located_node.targets[0].target.value

            # Main logic flow
            if not self.read_write.get(iid_location.start_line):
                new_entry = {
                    "write": _get_target_value(),
                    "read": []
                }
                if isinstance(located_node, (cst.AugAssign, cst.Assign)):
                    self.read_write[iid_location.start_line] = new_entry
            else:
                self.read_write.get(iid_location.start_line)["write"] = _get_target_value()
                if list(filter(lambda x: x in self.read_write[iid_location.start_line]["read"], self.vals["dependent_variables"])):
                    self.vals["dependent_variables"] += [_get_target_value()]
                    self.vals["lines_to_keep"] += [iid_location.start_line]
                if isinstance(located_node, cst.Assign) and m.matches(located_node.value, m.Name()) and not m.matches(located_node.value, m.Call()):
                    self.extra_variables[located_node.targets[0].target.value] = [located_node.value.value,iid_location.start_line]


    def read(self, dyn_ast: str, iid: int, val: Any) -> Any:
        iid_location = self.iid_to_location(dyn_ast, iid)
        located_node = get_node_by_location(self._get_ast(dyn_ast)[0], iid_location)
        if self.should_process(iid_location.start_line) and not isinstance(located_node, cst.Subscript):
            
            node_value = (f"{located_node.value.value}.{located_node.attr.value}" if isinstance(located_node, cst.Attribute) else located_node.value)
            
            if not self.read_write.get(iid_location.start_line):
                self.read_write[iid_location.start_line] = {"write": "", "read": [node_value]}
                if node_value in self.vals["dependent_variables"]:
                    self.vals["lines_to_keep"] += [iid_location.start_line]
                for vars in self.vals["dependent_variables"]:
                    if isinstance(vars, str) and '.' in vars:
                        if node_value in vars.split('.'):
                            self.vals["lines_to_keep"] += [iid_location.start_line]
                            self.vals["dependent_variables"] += [node_value]
                
            else:
                self.read_write.get(iid_location.start_line)["read"] += [node_value]
        
    def enter_if(self, dyn_ast: str, iid: int, cond_value: bool) -> Optional[bool]:
        iid_location = self.iid_to_location(dyn_ast, iid)
        located_node = get_node_by_location(self._get_ast(dyn_ast)[0], iid_location)
        if iid_location.start_line >= self.vals["slicing_criteria_line"]:
            if cond_value:
                self.vals["lines_to_keep"] += [iid_location.start_line]
                inside_lines = str(located_node.body).count("SimpleStatementLine")
                self.vals["lines_to_keep"] += list(range(iid_location.start_line + 1, iid_location.start_line + inside_lines + 1))
                if located_node.orelse:
                    self.vals["lines_to_keep"] += [iid_location.start_line + inside_lines + 1]
                for i in range(inside_lines):
                    if (target := getattr(getattr(getattr(located_node.body, 'body', [None])[i], 'body', [None])[0], 'target', None), None) and (value := getattr(target, 'value', None)):
                        if isinstance(value, str):
                            self.vals["dependent_variables"] += value
                        else:
                            self.vals["dependent_variables"] += [value.value]

            else:
                if located_node.orelse:
                    possible_else = str(located_node.body).count("SimpleStatementLine")
                    else_location = iid_location.start_line + possible_else + 1
                    self.vals["lines_to_keep"] += [else_location]
                    if isinstance(located_node.orelse, cst.Else):
                        statements_in_else = str(located_node.orelse).count("SimpleStatementLine")
                        self.vals["lines_to_keep"] += list(range(else_location + 1, else_location + statements_in_else + 1))
                        for i in range(statements_in_else):
                            if (target_value := (located_node.orelse and 
                                                located_node.orelse.body and 
                                                located_node.orelse.body.body[i] and 
                                                located_node.orelse.body.body[i].body[0] and 
                                                getattr(located_node.orelse.body.body[i].body[0].target, 'value', None))):
                                self.vals["dependent_variables"].append(target_value)
                else:
                    if iid_location.start_line in self.vals["lines_to_keep"]:
                        self.vals["lines_to_keep"].remove(iid_location.start_line)

    def enter_while(self, dyn_ast: str, iid: int, cond_value: bool) -> Optional[bool]:
        iid_location = self.iid_to_location(dyn_ast, iid)
        located_node = get_node_by_location(self._get_ast(dyn_ast)[0], iid_location)
        if iid_location.start_line >= self.vals["slicing_criteria_line"]:
            if cond_value:
                self.vals["lines_to_keep"] += [iid_location.start_line, iid_location.end_line]
                for i in range(iid_location.start_line, iid_location.end_line + 1):
                    self.read_write[i] = {"write": "", "read": []}
            
        
    def should_process(self, line_number):
        return (line_number not in self.vals["class_lines"]) and (line_number >= self.vals["slicing_criteria_line"])
