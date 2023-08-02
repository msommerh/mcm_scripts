import sys
import argparse
sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")
from rest import McM


parser = argparse.ArgumentParser(
    description="Resubmit chained requests that are stuck in submit-approved")
parser.add_argument("--prepids", type=str, nargs="+", required=True)
parser.add_argument("--dry", default=False, action="store_true")

args = parser.parse_args()
dry = args.dry
prepids = args.prepids

mcm = McM(dev=dry)

# operate each chained request
for request in prepids:   
    print("\nOperating chained request:", request)
    steps = mcm.steps_from_chained_request(request)
    
    # first check if really in submit-approved
    all_submit_approved = True
    for step in steps:
        current_request = mcm.get("requests", step)
        if (current_request["approval"] != "submit" or current_request["status"] != "approved"):
            all_submit_approved = False
            break
    if not all_submit_approved:
        print("Not all steps are in submit-approved, skipping...")
        break

    # soft-reset steps starting from last one
    all_success = True
    for step in steps[::-1]:
        success = mcm.soft_reset(step)
        if not success:
            all_success = False
            print(f"\nWARNING! Something unforeseen happened when"
                  f" soft-resetting {step}! Skipping this chained request!!\n")
            break
    if not all_success:
        break

    # resubmit root request
    success = mcm.approve("requests", steps[0])
    if success:
        print("\tSuccessfully resubmitted root request.")
    else:
        print("\nWARNING! Something unforeseen happened when"
              f" resubmitting {steps[0]}!!\n")
