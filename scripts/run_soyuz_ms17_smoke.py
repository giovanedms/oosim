"""Run the Soyuz MS-17 end-to-end smoke pipeline and print the report."""
from oosim.scenarios.soyuz_ms17 import run_soyuz_ms17_pipeline, report

if __name__ == "__main__":
    result = run_soyuz_ms17_pipeline()
    print(report(result))
