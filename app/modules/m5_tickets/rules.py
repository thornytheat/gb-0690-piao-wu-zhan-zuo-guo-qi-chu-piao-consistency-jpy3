from app.reasons import rejected
def verify_tickets(rows,payments):
    good=[];bad=[];tickets=[];used_tickets=set();sold_slots=set()
    for row in sorted(rows,key=lambda r:(r['time'],r['id'])):
        if row['type']!='issue':good.append(row);continue
        matches=[p for p in payments if p['show']==row['show'] and p['seat']==row['seat'] and p['order']==row['order'] and p['time']<=row['time']]
        if len(matches)!=1:bad.append(rejected(row,'ORPHAN','出票缺少同场次有效支付'));continue
        if row['channel']!=matches[0]['channel']:bad.append(rejected(row,'CONFLICT','出票渠道与支付渠道不符'));continue
        if not row['ticket']:bad.append(rejected(row,'MISSING','票号缺失'));continue
        slot=(row['show'],row['seat'])
        if row['ticket'] in used_tickets or slot in sold_slots:bad.append(rejected(row,'CONFLICT','票号全场重复或同场次座席重复出票'));continue
        if row['amount']!=matches[0]['amount']:bad.append(rejected(row,'CONFLICT','票面金额与支付不符'));continue
        used_tickets.add(row['ticket']);sold_slots.add(slot);tickets.append({**row,'lease':matches[0]['lease'],'state':'已出票'});good.append(row)
    return good,bad,tickets
