import sys
import argparse
sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")
from rest import McM


parser = argparse.ArgumentParser(
    description="Remove chained requests, including all the"
                " follow-up requests in the chain.")
parser.add_argument("--chained-requests", type=str, nargs="+", default=None)
parser.add_argument("--root-requests", type=str, nargs="+", default=None)
parser.add_argument("--hard-reset", default=False, action="store_true")
parser.add_argument("--dry", default=False, action="store_true")

args = parser.parse_args()
dry = args.dry
chained_requests = args.chained_requests
root_requests = args.root_requests
hard_reset = args.hard_reset

# making sure user input is meaningful
assert not (chained_requests is None and root_requests is None)
if chained_requests is None:
    assert root_requests is not None
    chained_requests = []
if root_requests is None:
    assert chained_requests is not None
    root_requests = []

mcm = McM(dev=dry)

# in case that root_requests are provided, identify their chained requests
for request in root_requests:
    mcm_request = mcm.get("requests", object_id=request)
    chains = mcm_request["member_of_chain"]
    if len(chains) != 1:
        print(f"The following root request is member of {len(chains)}"
              f" chains instead of 1: {request}")
        input("Press enter to skip it or abort with Ctrl+C")
        continue
    chained_requests.append(chains[0])

print("\nChained requests that will be deleted:")
for chained_request in chained_requests:
    print(f"\t{chained_request}")

# operate each chained request
for chained_request in chained_requests:

    print("\nOperating chained request:", chained_request)
    mcm_chained_request = mcm.get(
        "chained_requests", object_id=chained_request)
    if mcm_chained_request is None:
        print(f"Warning: Chained request doesn't exist!!")
        input("Press enter to skip it or abort with Ctrl+C")
        continue
    steps = mcm.steps_from_chained_request(chained_request)

    print("\tInvalidating chained request...")
    mcm_chained_request["action_parameters"]["flag"] = False
    update_answer = mcm.update("chained_requests", mcm_chained_request)

    print("\tRewinding chained request...")
    while mcm.rewind(chained_request):
        pass

    for step in steps[1:][::-1]:
        if "GEN" in step or "GS" in step:
            print(f"WARNING!!! Request {step} could be a root request!!!")
            input("Press enter to continue or abort with Ctrl+C")
        print(f"\tdeleting step {step}...")
        mcm.reset(step)
        mcm.delete("requests", step)

    if not hard_reset:
        print("\tSoft-resetting root request...")
        mcm.soft_reset(steps[0])
    else:
        print("\tHard-resetting root request...")
        mcm.reset(steps[0])

    print("\tRemoving chained request...")
    mcm.delete("chained_requests", chained_request)
