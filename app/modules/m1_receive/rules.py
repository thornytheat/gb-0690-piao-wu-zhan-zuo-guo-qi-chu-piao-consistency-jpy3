from app.normalize import rows_from
from app.reasons import rejected
from app.errors import DomainError
BLANK = {"", "-", "N/A", "NULL", "未知"}
def receive(raw, default_show):
    if not isinstance(default_show, str) or not default_show.strip():
        raise DomainError("PARAMS", "缺省场次必须是非空文本")
    default_show = default_show.strip()
    result = rows_from(raw, ['id', 'channel', 'seat', 'order', 'time', 'type', 'expires', 'version', 'amount', 'ticket'])
    has_show = 'show' in result['header']
    good = []
    for row in result['raw']:
        if not row['id'] or not row['order']:
            result['quarantine'].append(rejected(row, 'MISSING', '事件或订单缺失'))
            continue
        show = row.get('show', '').strip() if has_show else default_show
        if not has_show:
            row['show'] = default_show
        elif show in BLANK:
            # 场次不明：隔离并保留行号，绝不猜测归入任何场次
            result['quarantine'].append(rejected(row, 'NO_SHOW', '场次缺失，未参与任何场次的余票与收入计算'))
            continue
        else:
            row['show'] = show
        good.append(row)
    result['records'] = good
    result['show_column_present'] = has_show
    return result
