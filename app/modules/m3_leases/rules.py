from app.reasons import rejected
# Lease replay owns only holds/releases; payment and issue events are judged by later modules.
# 占用以 (场次, 座席) 为键：不同场次共用座席编号，互不影响。
def replay(rows,end):
    active={};leases=[];bad=[];retained=[]
    priority={'release':0,'hold':1,'pay':2,'issue':3}
    for row in sorted(rows,key=lambda x:(x['time'],priority[x['type']],x['id'])):
        show=row['show'];seat=row['seat'];slot=(show,seat);current=active.get(slot)
        if current is not None and current['end']<=row['time']:active.pop(slot);current=None
        if row['type']=='hold':
            if current is not None:bad.append(rejected(row,'OVERLAP','同场次座席仍被其他租约占用'));continue
            lease={'show':show,'lease':row['id'],'seat':seat,'order':row['order'],'channel':row['channel'],'start':row['time'],'end':row['expires'],'expires':row['expires'],'released':False,'source_line':row['_line']}
            leases.append(lease);active[slot]=lease
        elif row['type']=='release':
            if current is None or current['order']!=row['order']:bad.append(rejected(row,'STATE','释放事件没有对应占座'));continue
            current['end']=row['time'];current['released']=True;active.pop(slot)
        retained.append(row)
    for lease in leases:
        lease['state']='已释放' if lease['released'] else '已过期' if lease['end']<=end else '占用中'
    return retained,bad,leases
