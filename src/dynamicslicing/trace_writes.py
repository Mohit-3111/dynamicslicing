# Implement a DynaPyt analysis to trace all writes by printing them to stdout.
from typing import Any, List, Callable
from dynapyt.analyses.BaseAnalysis import BaseAnalysis

class TraceWrites(BaseAnalysis):
    def write(self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any) -> Any:
        # Prints the variable value which is provided in milestone1_task1.py file
        print(new_val)