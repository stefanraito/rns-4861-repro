"""lldb helper: simulate a wrapper that is recycled with translatesAutoresizingMaskIntoConstraints == NO.

Clears RNSScreenStackHeaderConfig._safeAreaConstraints right before -prepareForRecycle runs, so the
config does not reset its wrapper. Used to test whether a leaked tAMIC=NO wrapper alone reproduces
react-native-screens#4861.
"""
import lldb

S = {'off': 0, 'n': 0, 'out': '/tmp/leaksim.txt'}


def cb(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    cfg = frame.FindRegister('x0').GetValueAsUnsigned()
    err = lldb.SBError()
    arr = proc.ReadPointerFromMemory(cfg + S['off'], err)
    if arr:
        proc.WriteMemory(cfg + S['off'], b'\x00' * 8, err)
        S['n'] += 1
        with open(S['out'], 'a') as f:
            f.write('skipped reset for config %x (constraints %x) #%d\n' % (cfg, arr, S['n']))
    return False


def install(debugger, command, result, internal_dict):
    open(S['out'], 'w').close()
    target = debugger.GetSelectedTarget()
    frame = target.GetProcess().GetSelectedThread().GetSelectedFrame()
    S['off'] = frame.EvaluateExpression(
        '(long)ivar_getOffset((Ivar)class_getInstanceVariable((Class)objc_getClass("RNSScreenStackHeaderConfig"), "_safeAreaConstraints"))').GetValueAsSigned()
    b = target.BreakpointCreateByName('-[RNSScreenStackHeaderConfig prepareForRecycle]')
    b.SetScriptCallbackFunction('leaksim.cb')
    b.SetAutoContinue(True)


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f leaksim.install leaksim_install')
