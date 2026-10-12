"""lldb fault injection for react-native-screens#4861 (mechanism check, not a natural trigger).

1. Clears RNSScreenStackHeaderConfig._safeAreaConstraints right before -prepareForRecycle, so a
   header screen's RNSScreenContentWrapper goes back to Fabric's recycle pool with
   translatesAutoresizingMaskIntoConstraints == NO ("leak").
2. Only while /tmp/faultsim.enable exists: when +[RNSScreenStackHeaderConfig updateViewController:withConfig:animated:] later tries to set
   tAMIC = YES on a wrapper that is still NO (the headerless-screen branch), turns that call into a
   no-op, i.e. it simulates a headerless screen whose wrapper RNS does not reset.
Logs to /tmp/faultsim.txt.
"""
import lldb

S = {'off': 0, 'W': 0, 'out': '/tmp/faultsim.txt'}


def log(t):
    with open(S['out'], 'a') as f:
        f.write(t + '\n')


def cb_recycle(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    cfg = frame.FindRegister('x0').GetValueAsUnsigned()
    err = lldb.SBError()
    arr = proc.ReadPointerFromMemory(cfg + S['off'], err)
    if arr:
        proc.WriteMemory(cfg + S['off'], b'\x00' * 8, err)
        log('leak: config %x will not reset its wrapper' % cfg)
    return False


def cb_tamic(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    w = frame.FindRegister('x0').GetValueAsUnsigned()
    err = lldb.SBError()
    isa = proc.ReadPointerFromMemory(w, err) & 0x0000000ffffffff8
    if isa != S['W']:
        return False
    val = frame.FindRegister('x2').GetValueAsUnsigned() & 0xff
    caller = frame.GetThread().GetFrameAtIndex(1).GetFunctionName() or ''
    if val != 1 or 'updateViewController' not in caller:
        return False
    import os
    if not os.path.exists('/tmp/faultsim.enable'):
        return False
    opts = lldb.SBExpressionOptions()
    opts.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)
    cur = frame.EvaluateExpression('(int)[(UIView *)%d translatesAutoresizingMaskIntoConstraints]' % w, opts).GetValueAsSigned()
    if cur == 0:
        frame.FindRegister('x2').SetValueFromCString('0')
        log('skip: kept tAMIC=NO on wrapper %x (headerless screen)' % w)
    return False


def install(debugger, command, result, internal_dict):
    open(S['out'], 'w').close()
    target = debugger.GetSelectedTarget()
    frame = target.GetProcess().GetSelectedThread().GetSelectedFrame()
    S['off'] = frame.EvaluateExpression(
        '(long)ivar_getOffset((Ivar)class_getInstanceVariable((Class)objc_getClass("RNSScreenStackHeaderConfig"), "_safeAreaConstraints"))').GetValueAsSigned()
    S['W'] = frame.EvaluateExpression('(unsigned long)objc_getClass("RNSScreenContentWrapper")').GetValueAsUnsigned()
    for name, fn in [('-[RNSScreenStackHeaderConfig prepareForRecycle]', 'cb_recycle'),
                     ('-[UIView setTranslatesAutoresizingMaskIntoConstraints:]', 'cb_tamic')]:
        b = target.BreakpointCreateByName(name)
        b.SetScriptCallbackFunction('faultsim.' + fn)
        b.SetAutoContinue(True)


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f faultsim.install faultsim_install')
