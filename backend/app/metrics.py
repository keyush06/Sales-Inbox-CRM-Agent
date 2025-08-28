from statistics import mean, median
from typing import List, Dict

class MetricsAgg:

    def __init__(self):
        self.classify_latencies = []
        self.extract_latencies = []
        self.tool_latencies = []
        self.total_tokens = 0
        self.total_cost = 0.0
        self.emails_processed = 0

    def _get_p95(self, lst):
        if not lst:
            return 0.0

        arr2 = sorted(lst)
        return arr2[int(0.95*(len(arr2)-1))] ## returning the index of the array that will give the 95th percentile among the latencies
    
    def _get_metrics(self):
        p_50_c = median(self.classify_latencies) if self.classify_latencies else 0.0
        p_95_c = self._get_p95(self.classify_latencies)

        ##similarly for the extraction method
        p_50_e = median(self.extract_latencies) if self.extract_latencies else 0.0
        p_95_e = self._get_p95(self.extract_latencies)

        ## version 3 for tool latencies
        p_50_t = median(self.tool_latencies) if self.tool_latencies else 0.0
        p_95_t = self._get_p95(self.tool_latencies)

        return {
            "classify": {
                "p_50": p_50_c,
                "p_95": p_95_c,
            },
            "extract": {
                "p_50": p_50_e,
                "p_95": p_95_e,
            },
            "tools_upsert": {
                "p_50": p_50_t,
                "p_95": p_95_t,
            },
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "emails_processed": self.emails_processed,
        }

Metrics = MetricsAgg()