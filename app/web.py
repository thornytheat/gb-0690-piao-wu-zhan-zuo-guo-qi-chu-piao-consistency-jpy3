from flask import render_template,request
from app import store
from app.pipeline import run
from app.config import TITLE,MODULES,STAGES,COLUMNS,SAMPLES,DEFAULTS
def view(stage):
    if not 1<=stage<=7: return "页面不存在",404
    run_id=request.args.get("run")
    result=store.fetch(run_id) if run_id else run()
    sample_file = "shows.csv" if request.args.get("sample") == "shows" else "dirty.csv"
    sample = (SAMPLES / sample_file).read_text(encoding="utf-8-sig")
    data=result["stages"][stage-1]
    shows=sorted({r["show"] for r in result["records"]})
    current=request.args.get("show") or (shows[0] if shows else "")
    if current and current not in shows: current=shows[0] if shows else ""
    sold={t['seat'] for t in result['tickets'] if t['show']==current}
    paid={p['seat'] for p in result['payments'] if p['show']==current}
    held={l['seat'] for l in result['leases'] if l['show']==current}
    seats=[{'seat':f'A-{i:02d}','state':'已出票' if f'A-{i:02d}' in sold else '待出票' if f'A-{i:02d}' in paid else '已过期' if f'A-{i:02d}' in held else '空闲'} for i in range(1,17)]
    unknown=[q for q in result['quarantine'] if q['code']=='NO_SHOW']
    return render_template(f"m{stage}.html",title=TITLE,modules=MODULES,stage=stage,result=result,data=data,
                           sample=sample,defaults=DEFAULTS,columns=COLUMNS,history=store.history(),seats=seats,
                           shows=shows,current_show=current,unknown_rows=unknown)
