import sys
import argparse
sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")
from rest import McM


parser = argparse.ArgumentParser(
    description="Check whether all requests in a ticket are submitted")
parser.add_argument("--tickets", type=str, nargs="+", required=True)
parser.add_argument("--dry", default=False, action="store_true")

args = parser.parse_args()
dry = args.dry
tickets = args.tickets

print("checking tickets:")
for ticket in tickets:
    print("\t", ticket)

mcm = McM(dev=dry)

submitted_tickets = []
for ticket in tickets:
    print("\n", ticket)
    submitted = True
    unsubmitted_requests = {}
    requests_in_ticket = mcm.root_requests_from_ticket(ticket)
    for request in requests_in_ticket:
        if request["approval"] != "submit" or request["status"] != "submitted":
            unsubmitted_requests[request["prepid"]] = {
                "status": f"\"{request['approval']} -- {request['status']}\""
            }
            submitted = False
    if submitted:
        print("\t --> fully submitted.")
        submitted_tickets.append(ticket)
    else:
        for request in unsubmitted_requests.keys():
            print(f"\t{request} is in {unsubmitted_requests[request]['status']}")

if len(submitted_tickets) == len(tickets):
    print("\n----> All tickets are fully submitted :)")
