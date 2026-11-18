from decimal import Decimal as D
from collections import defaultdict
def reconcile(payments,tickets):
    channels=defaultdict(lambda:{'paid':D(0),'ticketed':D(0),'payments':0,'tickets':0})
    for p in payments:
        key=(p['show'],p['channel']);channels[key]['paid']+=p['amount'];channels[key]['payments']+=1
    for t in tickets:
        key=(t['show'],t['channel']);channels[key]['ticketed']+=t['amount'];channels[key]['tickets']+=1
    result=[]
    for (show,channel),row in sorted(channels.items()):
        result.append({'show':show,'channel':channel,**row,'delta':row['paid']-row['ticketed'],
                       'state':'通过' if row['paid']==row['ticketed'] and row['payments']==row['tickets'] else '待出票'})
    return result
def show_balances(rows):
    shows=defaultdict(lambda:{'paid':D(0),'ticketed':D(0),'payments':0,'tickets':0})
    for r in rows:
        bucket=shows[r['show']]
        if 'delta' in r:
            bucket['paid']+=r['paid'];bucket['ticketed']+=r['ticketed']
            bucket['payments']+=r['payments'];bucket['tickets']+=r['tickets']
    out=[]
    for show,bucket in sorted(shows.items()):
        out.append({'show':show,**bucket,'delta':bucket['paid']-bucket['ticketed']})
    return out
