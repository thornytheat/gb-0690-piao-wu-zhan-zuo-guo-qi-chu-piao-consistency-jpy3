from app.errors import DomainError
from datetime import timedelta
from decimal import Decimal as D
def audit(rows,bad,total,late_minutes):
    if len(rows)+len(bad)!=total:raise DomainError('INCOMPLETE','渠道行数不守恒')
    watermarks={};late=[]
    for row in sorted(rows,key=lambda r:r['_line']):
        show=row['show'];mark=watermarks.get(show)
        if mark and row['time']<mark-timedelta(minutes=float(late_minutes)):
            late.append({'id':row['id'],'show':show,'seat':row['seat'],'order':row['order'],'time':row['time'],'late_minutes':D(str((mark-row['time']).total_seconds()))/60,'state':'已回放'})
        watermarks[show]=max(mark,row['time']) if mark else row['time']
    return {'input':total,'retained':len(rows),'isolated':len(bad),'late':late,
            'watermark':dict(sorted(watermarks.items())),'shows':sorted(watermarks)}
