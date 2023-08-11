import sys
import argparse
sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")
from rest import McM


parser = argparse.ArgumentParser(
    description="Resubmit chained requests that are stuck in submit-approved")
parser.add_argument("--prepids", type=str, nargs="+")
parser.add_argument("--tickets", type=str, nargs="+")
parser.add_argument("--dry", default=False, action="store_true")

args = parser.parse_args()
dry = args.dry
prepids = args.prepids
tickets = args.tickets

if prepids is None and tickets is None:
    raise ValueError("Either chained request prepids or tickets must "
                     "be provided!")

mcm = McM(dev=dry)

# identify chained requests from tickets
if tickets is not None:
    print("Will resubmit all submit-approved chained requests in the "
          "following tickets:")
    for ticket in tickets:
        print("\t", ticket)

    if prepids is None:
        prepids = []
    else:
        print("Will append the chained requests found in the tickets "
              "to the ones already provided:")
        for prepid in prepids:
            print("\t", prepid)

    for ticket in tickets:
        prepids += (mcm.chained_requests_from_ticket(ticket))

print("\nThe following chained requests will be resubmitted (if in state "
      "submit-approved):")
for prepid in prepids:
    print("\t", prepid)

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
        print("\tNot all steps are in submit-approved, skipping...")
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
