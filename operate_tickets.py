import sys
import argparse
sys.path.append("/afs/cern.ch/cms/PPD/PdmV/tools/McM/")
from rest import McM


parser = argparse.ArgumentParser(description="Check and inject tickets in McM")
parser.add_argument("--tickets", type=str, nargs="+", required=True)
parser.add_argument("--dry", default=False, action="store_true")

args = parser.parse_args()
dry = args.dry
tickets = args.tickets

print("operating tickets:")
for ticket in tickets:
    print("\t", ticket)

mcm = McM(dev=dry)

# first check whether all are approved
approved_tickets = []
for ticket in tickets:
    all_approved = True
    requests_in_ticket = mcm.root_requests_from_ticket(ticket)
    for request in requests_in_ticket:
        if request["approval"] != "approve" or request["status"] != "approved":
            all_approved = False
            break
    if not all_approved:
        print("ticket", ticket, "has unapproved requests!")
    else:
        approved_tickets.append(ticket)

# asking user input in case of unapproved requests
if len(approved_tickets) == 0:
    print("No approved tickets found, aborting...")
    sys.exit()
elif len(approved_tickets) < len(tickets):
    print("Some of the given tickets are not approved yet."
          " Continue with approved tickets?")
    input("Press enter to continue or abort with Ctrl+C")
else:
    print("All tickets are approved :)")

# operate each ticket
for ticket in approved_tickets:
    
    print("\nOperating ticket:", ticket)

    # generate chained requests
    print("--> generating chained requests...")
    mcm.ticket_generate(ticket)

    # reserve and approve chained requests
    chained_requests = mcm.chained_requests_from_ticket(ticket)
    print("--> resulting chained requests:")
    root_requests = []
    for chained_request in chained_requests:
        print("\t", chained_request)
        mcm.reserve(chained_request)
        steps = mcm.steps_from_chained_request(chained_request)
        # first step is root request. Approve last
        root_requests.append(steps[0])
        for step in steps[1:]:
            mcm.approve("requests", step)

    # inject samples
    print("--> injecting root requests")
    for root_request in root_requests:
        print(f"\t injecting {root_request}")
        mcm.approve("requests", root_request)
