import sys
import argparse
sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")
from rest import McM


parser = argparse.ArgumentParser(
    description="Resubmit chained requests that are stuck in submit-approved")
parser.add_argument("--prepids", type=str, nargs="+")
parser.add_argument("--tickets", type=str, nargs="+")
parser.add_argument("--root-requests", type=str, nargs="+", default=None)
parser.add_argument("--dry", default=False, action="store_true")

args = parser.parse_args()
dry = args.dry
prepids = args.prepids
tickets = args.tickets
root_requests = args.root_requests

# making sure user input is meaningful
if prepids is None and tickets is None and root_requests is None:
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

# in case that root_requests are provided, identify their chained requests
if root_requests is not None:
    print("Will resubmit all submit-approved chained requests on top "
          "of the following root requests:")
    for root_request in root_requests:
        print("\t", root_request)
        
    if prepids is None:
        prepids = []
    else:
        print("Will append the chained requests found on top of root requests "
              "to the ones already provided:")
        for prepid in prepids:
            print("\t", prepid)
    
    for root_request in root_requests:
        mcm_request = mcm.get("requests", object_id=root_request)
        chains = mcm_request["member_of_chain"]
        if len(chains) != 1:
            print(f"The following root request is member of {len(chains)}"
                  f" chains instead of 1: {root_request}")
            input("Press enter to skip it or abort with Ctrl+C")
            continue
        prepids.append(chains[0])

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
        continue

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
