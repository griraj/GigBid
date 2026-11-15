"""Small-fixture regression gates; never substitutes for the 30-job GigSim run."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    result=json.loads((ROOT/'evals/results/synthetic_system.json').read_text())
    failures=[]
    if result['decision']['f1'] < 0.9:
        failures.append('Synthetic decision F1 below 0.90')
    if any(p['unapproved_send'] for p in result['adversarial_probes']):
        failures.append('Unapproved send detected')
    if any(not p['correct'] for p in result['claim_probes']):
        failures.append('Claim gate regression')
    if failures:raise SystemExit('; '.join(failures))
    print('Synthetic regression gates passed; external GigSim evaluation remains required.')


if __name__=='__main__':main()
