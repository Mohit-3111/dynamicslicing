import libcst as cst
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs

class SliceDataflow(BaseAnalysis):
    def __init__(self, source_path, output_dir=None):
        with open(source_path, "r") as file:
            source = file.read()
        self.source = source
        self.source_path = source_path
        iid_object = IIDs(source_path)