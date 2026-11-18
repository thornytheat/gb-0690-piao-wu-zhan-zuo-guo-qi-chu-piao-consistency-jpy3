from .rules import reconcile,show_balances
def execute(ctx):
    ctx['channel_balances']=reconcile(ctx['payments'],ctx['tickets'])
    ctx['show_balances']=show_balances(ctx['channel_balances'])
    ctx['stages'].append({'title':'渠道对账','rows':ctx['channel_balances'],'metrics':{'场次':len(ctx['show_balances']),'渠道行':len(ctx['channel_balances']),'有效支付':len(ctx['payments']),'悬单':len(ctx['payments'])-len(ctx['tickets'])}});return ctx
