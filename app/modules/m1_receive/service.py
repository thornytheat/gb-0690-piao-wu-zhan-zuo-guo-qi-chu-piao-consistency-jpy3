from .rules import receive
def execute(ctx):
    ctx.update(receive(ctx['source'], ctx['params']['default_show']))
    ctx['stages'].append({'title': '渠道接收', 'rows': ctx['records'],
                          'metrics': {'输入': ctx['input_count'], '采信': len(ctx['records']),
                                      '隔离': len(ctx['quarantine']),
                                      '场次不明': sum(x['code'] == 'NO_SHOW' for x in ctx['quarantine'])}})
    return ctx
